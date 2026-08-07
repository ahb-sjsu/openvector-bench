"""Round-13 stage 0: does real retrieval phenotype quantize? (PREREG_ROUND13 P-13A)

Measurement only. Nothing is generated, no candidate is scored, no band is
read. The single registered question is whether real embedding geometry
carries a LOW-DIMENSIONAL hubness phenotype — if it does not, the codebook
premise is wrong and no layer-3 control work should be built on it.

Gate-first, applied to the campaign's own proposal: round 12 built a stage
on a mechanism whose presence at ladder scale had never been checked, and
the presence gate added one round earlier is what stopped a failure clause
from firing on an absent mechanism. This driver is the analogous check,
run before any generator exists.

The anti-circularity rule is structural here, not a convention:

  * LATENT features (layers 1 and 2 of the prereg: corpus geometry and
    query exposure) are the ONLY inputs to the codebook fit.
  * RESPONSE features (layer 3: N_k, reverse-neighbour rank) are held out
    of the fit entirely and used only to score it.

A codebook fitted on response would reproduce response by construction.
The whole claim is that latent structure PREDICTS response, so the two
sets never touch until scoring.

Registered thresholds (PREREG_ROUND13 §4, P-13A), all read on HELD-OUT
points:
  * K <= 12 states,
  * cross-validated mutual information about response >= 2x the best
    single latent feature,
  * state assignment stable across seeds at adjusted Rand index >= 0.7.

Env: R13_OUT (output json), R13_REAL (corpus .npy), R13_N (base rows),
R13_SEEDS (JSON list), R13_KS (JSON list of k), R13_KMAX (codebook sizes
to sweep).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.geometry import (  # noqa: E402
    id_local,
    knn,
    normalize,
)

OUT = os.environ.get("R13_OUT", "results/r13_stage0.json")
REAL_DIR = os.environ.get("R13_REAL_DIR", "/archive/tqp_real/wiki1024")
QUERIES = os.environ.get("R13_QUERIES", "/archive/tqp_real/wiki1024/queries.npy")
N_BASE = int(os.environ.get("R13_N", "100000"))
N_QUERY = int(os.environ.get("R13_NQ", "20000"))
SEEDS = json.loads(os.environ.get("R13_SEEDS", "[0, 1, 2]"))
KS = json.loads(os.environ.get("R13_KS", "[10, 30, 100]"))
K_CODEBOOK = json.loads(os.environ.get("R13_KMAX", "[2, 4, 6, 8, 10, 12]"))
# Reference partition, far above the registered K<=12 ceiling. It does not
# gate anything; it separates the two ways P-13A can fail. If K=64 predicts
# response well but K<=12 does not, the phenotype is real but NOT
# low-dimensional (the registered claim fails honestly). If even K=64 fails,
# the latent code does not predict response at all, which indicts the feature
# set rather than the quantization premise. k-means minimizes latent variance,
# not MI, so without this a suboptimal partition and an absent phenotype look
# identical.
K_REFERENCE = int(os.environ.get("R13_KREF", "64"))
KNN_K = max(KS) + 1
N_BINS = 8  # response discretization for the MI estimate


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# Layer 1 + 2: latent codes. Geometry and query exposure ONLY — nothing here   #
# may look at how often a point is actually retrieved.                         #
# --------------------------------------------------------------------------- #
def latent_features(base: np.ndarray, queries: np.ndarray, seed: int) -> dict:
    """Per-base-point latent code: local geometry + query exposure.

    Query exposure is deliberately computed as the query measure's density
    AT the point (how much query mass is near it), not as the point's
    retrieval count. Those differ exactly where the interesting cases live:
    a point in a query-dense region that is never returned is one of the
    prereg's five anti-hub categories, and collapsing the two would make
    that category unobservable.
    """
    n = len(base)
    # Base-to-base geometry. Self-match is dropped by taking columns 1:.
    d_bb, i_bb = knn(base, base, KNN_K)
    d_bb, i_bb = d_bb[:, 1:], i_bb[:, 1:]

    feats: dict[str, np.ndarray] = {}
    # --- density / radius spectrum (layer 1) ---
    for k in KS:
        feats[f"r{k}"] = d_bb[:, k - 1].astype(np.float64)
    # Radius spectrum shape, not just level: how fast the ball grows.
    feats["radius_slope"] = np.log(
        np.maximum(d_bb[:, max(KS) - 1], 1e-12) / np.maximum(d_bb[:, KS[0] - 1], 1e-12)
    )
    # --- local intrinsic dimension (layer 1) ---
    lid = np.full(n, np.nan)
    good = (d_bb[:, : KS[1] - 1] > 0).all(1) & (d_bb[:, KS[1] - 1] > 0)
    lid[good] = id_local(d_bb, KS[1])
    feats["local_id"] = lid
    # --- anisotropy: angular vs radial contribution (layer 1) ---
    # How aligned a point's neighbourhood is: the resultant length of its
    # neighbour directions. Isotropic surroundings -> near 0; a point sitting
    # off the edge of a cluster -> near 1.
    nb = base[i_bb[:, : KS[0]]]  # (n, k, dim)
    diff = nb - base[:, None, :]
    nrm = np.maximum(np.linalg.norm(diff, axis=2, keepdims=True), 1e-12)
    feats["anisotropy"] = np.linalg.norm((diff / nrm).mean(axis=1), axis=1)
    # --- query exposure (layer 2) ---
    # Distance from each BASE point to the query cloud: small = heavily
    # interrogated region. Computed base->query, so it is a property of the
    # query measure at that location, never a retrieval outcome.
    d_bq, _ = knn(queries, base, KS[0])
    feats["query_dist"] = d_bq[:, KS[0] - 1].astype(np.float64)
    feats["query_mass"] = -np.log(np.maximum(d_bq.mean(1), 1e-12))
    return feats


# --------------------------------------------------------------------------- #
# Layer 3: response. Held out of the fit; used only to score it.               #
# --------------------------------------------------------------------------- #
def response_features(base: np.ndarray, queries: np.ndarray) -> dict:
    d_qb, i_qb = knn(base, queries, max(KS))
    n = len(base)
    out: dict[str, np.ndarray] = {}
    for k in KS:
        out[f"Nk{k}"] = np.bincount(i_qb[:, :k].ravel(), minlength=n).astype(np.float64)
    # Reverse-neighbour rank: for each base point, the best rank it ever
    # achieved in any query's list (max(KS)+1 = never retrieved).
    best = np.full(n, max(KS) + 1, dtype=np.float64)
    for r in range(max(KS) - 1, -1, -1):
        best[i_qb[:, r]] = r + 1
    out["best_rank"] = best
    return out


# --------------------------------------------------------------------------- #
# Scoring                                                                      #
# --------------------------------------------------------------------------- #
def _discretize(v: np.ndarray, bins: int) -> np.ndarray:
    """Quantile bins, robust to the heavy zero-atom in N_k."""
    v = np.asarray(v, dtype=np.float64)
    qs = np.quantile(v[np.isfinite(v)], np.linspace(0, 1, bins + 1)[1:-1])
    return np.searchsorted(np.unique(qs), v)


def mutual_information(a: np.ndarray, b: np.ndarray) -> float:
    """MI in nats between two discrete labelings."""
    a = a.astype(np.int64)
    b = b.astype(np.int64)
    na, nb = a.max() + 1, b.max() + 1
    joint = np.bincount(a * nb + b, minlength=na * nb).reshape(na, nb).astype(float)
    joint /= joint.sum()
    pa = joint.sum(1, keepdims=True)
    pb = joint.sum(0, keepdims=True)
    nz = joint > 0
    return float((joint[nz] * np.log(joint[nz] / (pa @ pb)[nz])).sum())


def kmeans(x: np.ndarray, k: int, seed: int, iters: int = 40):
    """Plain Lloyd's with k-means++ init — no sklearn dependency in the harness."""
    rng = np.random.default_rng(seed)
    c = [x[rng.integers(len(x))]]
    for _ in range(k - 1):
        d = np.min(((x[:, None, :] - np.array(c)[None, :, :]) ** 2).sum(2), axis=1)
        p = d / max(d.sum(), 1e-12)
        c.append(x[rng.choice(len(x), p=p)])
    c = np.array(c)
    lab = np.zeros(len(x), dtype=np.int64)
    for _ in range(iters):
        d = ((x[:, None, :] - c[None, :, :]) ** 2).sum(2)
        new = d.argmin(1)
        if (new == lab).all():
            break
        lab = new
        for j in range(k):
            m = lab == j
            if m.any():
                c[j] = x[m].mean(0)
    return lab, c


def assign(x: np.ndarray, c: np.ndarray) -> np.ndarray:
    return ((x[:, None, :] - c[None, :, :]) ** 2).sum(2).argmin(1)


def adjusted_rand(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = a.max() + 1, b.max() + 1
    m = np.bincount(a * nb + b, minlength=na * nb).reshape(na, nb).astype(float)
    ai, bj = m.sum(1), m.sum(0)
    n = m.sum()

    def c2(v):
        return (v * (v - 1) / 2).sum()

    idx, ea, eb = c2(m), c2(ai), c2(bj)
    exp = ea * eb / max(c2(np.array([n])), 1e-12)
    mx = (ea + eb) / 2
    return float((idx - exp) / max(mx - exp, 1e-12))


def load_real(n_rows: int, rng) -> np.ndarray:
    """Sample n_rows from the sharded real corpus.

    The Cohere corpus is 42 x 1M-row parts, not one array. Rows are drawn
    across a spread of parts rather than from the head of part_000: Wikipedia
    row order is topically clustered, and the round-2 admission run measured
    what that does to a query marginal (battery-A G6 9.4-11 versus ~1.5 under
    uniform sampling). A head slice would be a different corpus.
    """
    import glob

    parts = sorted(glob.glob(os.path.join(REAL_DIR, "part_*.npy")))
    if not parts:
        raise FileNotFoundError(f"no part_*.npy under {REAL_DIR}")
    per = max(1, n_rows // len(parts))
    out = []
    for p in parts:
        a = np.load(p, mmap_mode="r")
        take = min(per, len(a))
        idx = np.sort(rng.choice(len(a), size=take, replace=False))
        out.append(np.asarray(a[idx], dtype=np.float32))
        if sum(len(o) for o in out) >= n_rows:
            break
    return np.concatenate(out)[:n_rows]


def main() -> None:
    log("R13 STAGE 0 — quantization gate on real data (measurement only)")
    rng = np.random.default_rng(12345)
    base = normalize(load_real(N_BASE, rng))
    q_all = np.load(QUERIES, mmap_mode="r") if os.path.exists(QUERIES) else None
    if q_all is not None:
        qsel = rng.choice(len(q_all), size=min(N_QUERY, len(q_all)), replace=False)
        queries = normalize(np.asarray(q_all[np.sort(qsel)], dtype=np.float32))
    else:
        # Fall back to the harness convention: a held-out slice of the corpus
        # as queries. Recorded in the output — it changes the query marginal,
        # which is exactly what layer 2 measures.
        cut = int(len(base) * (1.0 - 1.0 / 9.0))
        base, queries = base[:cut], base[cut:]
    log(f"base {base.shape}, queries {queries.shape}")

    lat = latent_features(base, queries, seed=0)
    resp = response_features(base, queries)
    log(f"latent features: {sorted(lat)}")
    log(f"response features: {sorted(resp)}")

    X = np.column_stack([lat[k] for k in sorted(lat)])
    ok = np.isfinite(X).all(1)
    X = X[ok]
    # Standardize: k-means on raw radii would be dominated by scale.
    X = (X - X.mean(0)) / np.maximum(X.std(0), 1e-12)
    resp_ok = {k: v[ok] for k, v in resp.items()}
    names = sorted(lat)

    n = len(X)
    half = n // 2
    perm = np.random.default_rng(7).permutation(n)
    tr, te = perm[:half], perm[half:]

    resp_bins = {k: _discretize(v, N_BINS) for k, v in resp_ok.items()}

    # Baseline: the best SINGLE latent feature cut into THE SAME NUMBER OF
    # CELLS as the codebook it is compared against. Matching the state budget
    # is load-bearing, not tidiness: MI is bounded by log(cells), so scoring a
    # K=2 codebook against an 8-bin feature caps the ratio near 0.33 for a
    # purely mechanical reason and the registered 2x threshold becomes
    # unmeetable at small K. Caught by the smoke test before any real run.
    def best_single_at(cells: int):
        per = {}
        for j, nm in enumerate(names):
            b = _discretize(X[:, j], cells)
            per[nm] = {
                rk: mutual_information(b[te], rb[te]) for rk, rb in resp_bins.items()
            }
        best = {rk: max(per[nm][rk] for nm in names) for rk in resp_bins}
        who = {rk: max(names, key=lambda nm: per[nm][rk]) for rk in resp_bins}
        return best, who

    results = []
    baselines = {}
    for K in K_CODEBOOK:
        best_single, best_single_name = best_single_at(K)
        baselines[str(K)] = {"mi": best_single, "feature": best_single_name}
        lab_tr, cent = kmeans(X[tr], K, seed=SEEDS[0])
        lab_te = assign(X[te], cent)
        mi = {rk: mutual_information(lab_te, rb[te]) for rk, rb in resp_bins.items()}
        ratio = {rk: mi[rk] / max(best_single[rk], 1e-12) for rk in mi}
        # Seed stability: refit from scratch on other seeds, compare the
        # assignment of the SAME held-out points.
        aris = []
        for s in SEEDS[1:]:
            _, c2_ = kmeans(X[tr], K, seed=s)
            aris.append(adjusted_rand(lab_te, assign(X[te], c2_)))
        occ = np.bincount(lab_te, minlength=K) / len(lab_te)
        row = {
            "K": K,
            "mi": mi,
            "mi_ratio_vs_best_single": ratio,
            "ari_across_seeds": aris,
            "ari_min": float(min(aris)) if aris else None,
            "occupancy": occ.round(4).tolist(),
            "passes": bool(
                K <= 12
                and min(ratio.values()) >= 2.0
                and (min(aris) >= 0.7 if aris else False)
            ),
        }
        results.append(row)
        log(
            f"K={K}: baseline={best_single_name} MI ratio { {k: round(v, 2) for k, v in ratio.items()} } "
            f"ARI_min={row['ari_min']:.3f} passes={row['passes']}"
        )

    # Diagnostic reference partition (not a gate).
    _, cent_ref = kmeans(X[tr], K_REFERENCE, seed=SEEDS[0])
    lab_ref = assign(X[te], cent_ref)
    ref_single, _ = best_single_at(K_REFERENCE)
    ref_mi = {rk: mutual_information(lab_ref, rb[te]) for rk, rb in resp_bins.items()}
    reference = {
        "K": K_REFERENCE,
        "mi": ref_mi,
        "mi_ratio_vs_best_single": {
            rk: ref_mi[rk] / max(ref_single[rk], 1e-12) for rk in ref_mi
        },
        "role": "diagnostic only — separates 'not low-dimensional' from "
        "'latent code does not predict response at all'",
    }
    log(
        f"reference K={K_REFERENCE}: MI ratio "
        f"{ {k: round(v, 2) for k, v in reference['mi_ratio_vs_best_single'].items()} }"
    )

    passing = [r for r in results if r["passes"]]
    verdict = {
        "P13A_passes": bool(passing),
        "smallest_passing_K": min((r["K"] for r in passing), default=None),
        "why": (
            "phenotype quantizes: a latent-only codebook predicts held-out "
            "response at >=2x the best single latent feature with stable "
            "states"
            if passing
            else "no K<=12 met both the MI-ratio and stability thresholds; "
            "P-13A fails as registered — report the phenotype dimensionality "
            "and do not proceed to layer-3 control work"
        ),
    }
    out = {
        "meta": {
            "prereg": "results/PREREG_ROUND13.md v1 (DRAFT; P-13A quantization gate)",
            "real": REAL_DIR,
            "queries": QUERIES if q_all is not None else "held-out corpus slice",
            "n_base": int(len(base)),
            "n_query": int(len(queries)),
            "ks": KS,
            "seeds": SEEDS,
            "latent_features": names,
            "response_features": sorted(resp),
            "rule": "codebook fitted on LATENT features only; response held out",
        },
        "baseline_per_K": baselines,
        "codebook": results,
        "reference_partition": reference,
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log(json.dumps(verdict, indent=1))
    log("R13_STAGE0_DONE")


if __name__ == "__main__":
    main()
