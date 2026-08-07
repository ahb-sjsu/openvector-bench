"""Round-13 stage 0b: is there joint structure, and does it concentrate?
(PREREG_ROUND13 v2, P-13D and P-13E)

Stage 0 measured that an UNSUPERVISED codebook of the latent space carries
less about retrieval response than one axis of it does, and that finding
stands. It could not separate two causes: k-means spends its state budget
isotropically, so "no joint structure exists" and "this quantizer wastes
its budget" produce the same number.

This driver asks the prior question instead of re-asking the old one:

  P-13D  does response depend on the latent code JOINTLY at all, beyond
         query_mass — the axis stage 0 measured as dominant?
  P-13E  if it does, does that dependence SATURATE at few states?

The quantizer here is a greedy axis-aligned partition that maximizes
mutual information with response. It is allowed to see response ON
TRAINING ROWS ONLY; every reported number is measured on held-out rows it
never saw. That is the restricted circularity rule of prereg v2 §3b, and
what it forfeits is stated there: a supervised codebook is evidence about
a relevance-weighted summary of the latent code, not about latent space as
such.

The baseline for P-13D is the SAME procedure restricted to query_mass
alone. Both sides are supervised, both get the same leaf budget, both are
scored on the same held-out rows — so the comparison isolates exactly one
thing, whether the other seven features add anything.

Env: R13B_OUT, R13_REAL_DIR, R13_QUERIES, R13_N, R13_NQ, R13_SEEDS,
R13_KS, R13B_KS (leaf budgets), R13B_KREF (saturation reference).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from r13_stage0 import (  # noqa: E402
    KS,
    N_BASE,
    N_BINS,
    N_QUERY,
    QUERIES,
    _discretize,
    adjusted_rand,
    latent_features,
    load_real,
    mutual_information,
    response_features,
)

from openvector_bench.geometry import normalize  # noqa: E402

OUT = os.environ.get("R13B_OUT", "results/r13_stage0b.json")
LEAF_KS = json.loads(os.environ.get("R13B_KS", "[2, 4, 6, 8, 10, 12]"))
K_REF = int(os.environ.get("R13B_KREF", "64"))
SEEDS = json.loads(os.environ.get("R13_SEEDS", "[0, 1, 2]"))
DOMINANT = os.environ.get("R13B_DOMINANT", "query_mass")


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# Greedy MI-maximizing axis-aligned partition (a decision tree by another       #
# name, kept dependency-free like the rest of the harness).                     #
# --------------------------------------------------------------------------- #
def _split_gain(col: np.ndarray, y: np.ndarray, thr: float) -> float:
    """MI(y ; side) for one candidate threshold — the gain from one cut."""
    side = (col > thr).astype(np.int64)
    if side.min() == side.max():
        return -1.0
    return mutual_information(side, y)


def fit_partition(X: np.ndarray, y: np.ndarray, n_leaves: int, seed: int):
    """Grow to ``n_leaves`` by repeatedly splitting the leaf that gains most.

    Returns a list of (feature, threshold, leaf_id_left, leaf_id_right)
    applied in order, plus the training leaf assignment. Candidate
    thresholds are quantiles of the feature within the leaf, subsampled by
    ``seed`` so that seed-to-seed stability is a real test rather than a
    determinism check.
    """
    rng = np.random.default_rng(seed)
    leaf = np.zeros(len(X), dtype=np.int64)
    rules: list[tuple[int, float, int, int]] = []
    n_cand = 15
    while leaf.max() + 1 < n_leaves:
        best = (-1.0, None)
        for lid in range(leaf.max() + 1):
            m = leaf == lid
            if m.sum() < 50:
                continue
            ys = y[m]
            if ys.min() == ys.max():
                continue
            for j in range(X.shape[1]):
                col = X[m, j]
                qs = np.quantile(col, rng.uniform(0.1, 0.9, n_cand))
                for thr in np.unique(qs):
                    g = _split_gain(col, ys, thr)
                    # Weight by leaf mass: a big leaf's gain matters more.
                    g *= m.mean()
                    if g > best[0]:
                        best = (g, (lid, j, float(thr)))
        if best[1] is None:
            break
        lid, j, thr = best[1]
        new_id = leaf.max() + 1
        m = (leaf == lid) & (X[:, j] > thr)
        leaf[m] = new_id
        rules.append((j, thr, lid, new_id))
    return rules, leaf


def apply_partition(X: np.ndarray, rules) -> np.ndarray:
    leaf = np.zeros(len(X), dtype=np.int64)
    for j, thr, lid, new_id in rules:
        leaf[(leaf == lid) & (X[:, j] > thr)] = new_id
    return leaf


def main() -> None:
    log("R13 STAGE 0b — joint structure (P-13D) and saturation (P-13E)")
    rng = np.random.default_rng(12345)
    base = normalize(load_real(N_BASE, rng))
    q_all = np.load(QUERIES, mmap_mode="r") if os.path.exists(QUERIES) else None
    if q_all is not None:
        qsel = rng.choice(len(q_all), size=min(N_QUERY, len(q_all)), replace=False)
        queries = normalize(np.asarray(q_all[np.sort(qsel)], dtype=np.float32))
    else:
        cut = int(len(base) * (1.0 - 1.0 / 9.0))
        base, queries = base[:cut], base[cut:]
    log(f"base {base.shape}, queries {queries.shape}")

    lat = latent_features(base, queries, seed=0)
    resp = response_features(base, queries)
    names = sorted(lat)
    X = np.column_stack([lat[k] for k in names])
    ok = np.isfinite(X).all(1)
    X = X[ok]
    X = (X - X.mean(0)) / np.maximum(X.std(0), 1e-12)
    resp_bins = {k: _discretize(v[ok], N_BINS) for k, v in resp.items()}
    dom = names.index(DOMINANT)
    log(f"features {names}; dominant axis = {DOMINANT} (col {dom})")

    n = len(X)
    perm = np.random.default_rng(7).permutation(n)
    tr, te = perm[: n // 2], perm[n // 2 :]

    rows = []
    for K in LEAF_KS + [K_REF]:
        entry: dict = {"K": K, "all": {}, "dominant_only": {}, "ratio": {}}
        leaves_by_seed: dict[str, list[np.ndarray]] = {}
        for rk, rb in resp_bins.items():
            mi_all, mi_dom, seed_leaves = [], [], []
            for s in SEEDS:
                r_all, _ = fit_partition(X[tr], rb[tr], K, seed=s)
                lab_all = apply_partition(X[te], r_all)
                mi_all.append(mutual_information(lab_all, rb[te]))
                seed_leaves.append(lab_all)
                r_dom, _ = fit_partition(X[tr][:, [dom]], rb[tr], K, seed=s)
                lab_dom = apply_partition(X[te][:, [dom]], r_dom)
                mi_dom.append(mutual_information(lab_dom, rb[te]))
            entry["all"][rk] = float(np.mean(mi_all))
            entry["dominant_only"][rk] = float(np.mean(mi_dom))
            entry["ratio"][rk] = float(np.mean(mi_all) / max(np.mean(mi_dom), 1e-12))
            leaves_by_seed[rk] = seed_leaves
        # Stability on the primary response variable.
        prim = f"Nk{KS[0]}"
        ls = leaves_by_seed[prim]
        aris = [adjusted_rand(ls[0], ls[i]) for i in range(1, len(ls))]
        entry["ari_min"] = float(min(aris)) if aris else None
        rows.append(entry)
        log(
            f"K={K}: joint/dominant MI ratio "
            f"{ {k: round(v, 3) for k, v in entry['ratio'].items()} } "
            f"ARI_min={entry['ari_min']}"
        )

    ref = next(r for r in rows if r["K"] == K_REF)
    gated = [r for r in rows if r["K"] in LEAF_KS]

    # P-13D: joint beats dominant-only by >= 1.25x at K=12, >=3 of 4 response
    # variables, on the seed-averaged held-out MI.
    k12 = max(gated, key=lambda r: r["K"])
    d_hits = sum(1 for v in k12["ratio"].values() if v >= 1.25)
    p13d = bool(d_hits >= 3)

    # P-13E: K<=12 reaches >= 0.90 of the K=64 MI, and leaves are stable.
    sat = {rk: k12["all"][rk] / max(ref["all"][rk], 1e-12) for rk in k12["all"]}
    p13e = bool(min(sat.values()) >= 0.90 and (k12["ari_min"] or 0.0) >= 0.7)

    verdict = {
        "P13D_passes": p13d,
        "P13D_ratio_at_K12": k12["ratio"],
        "P13D_vars_meeting_1.25x": d_hits,
        "P13E_passes": p13e,
        "P13E_saturation_K12_over_K64": sat,
        "P13E_ari_min": k12["ari_min"],
        "reading": (
            "joint structure present"
            if p13d
            else "response depends on the latent code essentially through "
            "one axis (query exposure); the codebook programme closes on "
            "the merits per the registered failure clause"
        ),
    }
    out = {
        "meta": {
            "prereg": "results/PREREG_ROUND13.md v2 (P-13D joint structure, "
            "P-13E saturation)",
            "rule": "quantizer fitted against response on TRAINING rows only; "
            "all reported numbers on held-out rows",
            "n_base": int(len(base)),
            "n_query": int(len(queries)),
            "features": names,
            "dominant": DOMINANT,
            "seeds": SEEDS,
            "leaf_budgets": LEAF_KS,
            "reference_K": K_REF,
        },
        "partitions": rows,
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log(json.dumps(verdict, indent=1))
    log("R13_STAGE0B_DONE")


if __name__ == "__main__":
    main()
