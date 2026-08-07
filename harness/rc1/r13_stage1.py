"""Round-13 stage 1: the anti-hub taxonomy, and whether G6 can see it.
(PREREG_ROUND13 P-13B)

Not gated on P-13A. The registered claim has two halves and they are
independent findings:

  half 1  the five anti-hub categories are SEPARABLE by latent code —
          legitimate high-dimensional anti-hubs, low-density outliers,
          boundary points, metric-misaligned points, and points the query
          marginal never visits;
  half 2  G6 is BLIND to them — corpora matched on G6 and on base-to-base
          skew differ in category proportions by >= 2x in at least one
          category.

If both hold, the battery's lower tail is an unmeasured axis and the
discriminator is a contribution independent of any generator. Stage 0
raised the prior on the fifth category specifically: query_mass was the
single best predictor of retrieval response, so "never asked for" should
be both large and invisible to a corpus-side statistic.

Category assignment is by LATENT rule, never by the response being
explained. Each point with N_k = 0 is assigned by the mechanism that
accounts for its invisibility:

  never_asked    far from all query mass (the query marginal avoids it)
  low_density    sparse neighbourhood — nothing near it to be near
  boundary       neighbourhood strongly one-sided (it sits on an edge)
  metric_misfit  its neighbours do not reciprocate: it is in others' lists
                 far less than they are in its own
  legit_antihub  none of the above — genuinely far in a high-dimensional
                 sense, the category the literature assumes is the whole
                 story

Separability is then tested the honest way: fit the rule-free classifier on
half the points, predict held-out labels from latent features, and report
balanced accuracy. A category that cannot be recovered from the latent code
without its defining rule is not a real category.

**Corpus size is swept, and that is part of the measurement.** With a fixed
real query set of 1,000 and k = 10 there are at most 10,000 retrieval slots,
so at n = 50,000 at least 80% of points are unretrieved by pigeonhole alone
and the taxonomy would be measuring query budget rather than anti-hubness.
Sweeping n makes the budget an explicit axis: the registered n = 8,000 is the
harness convention (8,000 base + 1,000 queries, QUERY_FRAC = 1/9) and the
smaller and larger points show how the category mix moves as the query
measure covers more or less of the corpus. That dependence is itself the
round-7 claim in the lower tail.

Env: R13S1_OUT, R13_REAL_DIR, R13_QUERIES, R13S1_NS (JSON list of corpus
sizes), R13_NQ, R13_KS.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from r13_stage0 import (  # noqa: E402
    KS,
    N_QUERY,
    QUERIES,
    latent_features,
    load_real,
    response_features,
)

from openvector_bench.geometry import knn, normalize  # noqa: E402

OUT = os.environ.get("R13S1_OUT", "results/r13_stage1.json")
# 8000 is the registered harness convention (8000 base + 1000 queries); the
# flanking sizes expose the query-budget dependence of the lower tail.
NS = json.loads(os.environ.get("R13S1_NS", "[3000, 8000, 20000]"))
CATS = [
    "never_asked",
    "low_density",
    "boundary",
    "metric_misfit",
    "legit_antihub",
]


def log(msg: str) -> None:
    print(msg, flush=True)


def categorize(lat: dict, base: np.ndarray, zero: np.ndarray) -> np.ndarray:
    """Assign each never-retrieved point its mechanism of invisibility.

    Order matters and is registered: a point far from all query mass is
    'never asked' regardless of its geometry, because no geometric property
    can make it retrievable if nothing looks for it. Only points that ARE
    interrogated get diagnosed geometrically.
    """
    n = len(base)
    lab = np.full(n, -1, dtype=np.int64)
    qm = lat["query_mass"]
    r_mid = lat[f"r{KS[1]}"]
    aniso = lat["anisotropy"]

    # Thresholds are quantiles of the WHOLE corpus, so a category means
    # "extreme relative to this corpus" rather than an absolute cut.
    q_lo = np.quantile(qm, 0.20)
    d_hi = np.quantile(r_mid, 0.80)
    a_hi = np.quantile(aniso, 0.80)

    # Reciprocity: how often this point appears in its own neighbours' lists.
    d_bb, i_bb = knn(base, base, KS[0] + 1)
    i_bb = i_bb[:, 1:]
    back = np.zeros(n, dtype=np.float64)
    for r in range(i_bb.shape[1]):
        np.add.at(back, i_bb[:, r], 1.0)
    recip_lo = np.quantile(back, 0.20)

    for i in zero:
        if qm[i] <= q_lo:
            lab[i] = 0  # never_asked
        elif r_mid[i] >= d_hi:
            lab[i] = 1  # low_density
        elif aniso[i] >= a_hi:
            lab[i] = 2  # boundary
        elif back[i] <= recip_lo:
            lab[i] = 3  # metric_misfit
        else:
            lab[i] = 4  # legit_antihub
    return lab


def balanced_accuracy(true: np.ndarray, pred: np.ndarray, k: int) -> float:
    accs = []
    for c in range(k):
        m = true == c
        if m.sum() >= 5:
            accs.append(float((pred[m] == c).mean()))
    return float(np.mean(accs)) if accs else float("nan")


def nearest_centroid(xtr, ytr, xte, k):
    """Rule-free classifier: class centroids in standardized latent space.

    Deliberately weak. If a category is only recoverable by a high-capacity
    model, it is a thin slice of feature space rather than a phenotype.
    """
    cents = []
    for c in range(k):
        m = ytr == c
        cents.append(xtr[m].mean(0) if m.sum() else np.full(xtr.shape[1], 1e9))
    C = np.array(cents)
    return ((xte[:, None, :] - C[None, :, :]) ** 2).sum(2).argmin(1)


def run_one(n_base: int) -> dict:
    rng = np.random.default_rng(12345)
    base = normalize(load_real(n_base, rng))
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
    nk = resp[f"Nk{KS[0]}"]
    zero = np.flatnonzero(nk == 0)
    log(
        f"never-retrieved at k={KS[0]}: {len(zero)} / {len(base)} "
        f"({100 * len(zero) / len(base):.1f}%)"
    )

    lab = categorize(lat, base, zero)
    names = sorted(lat)
    X = np.column_stack([lat[k] for k in names])
    okmask = np.isfinite(X).all(1)
    X = np.where(np.isfinite(X), X, 0.0)
    X = (X - X.mean(0)) / np.maximum(X.std(0), 1e-12)

    counts = {CATS[c]: int((lab == c).sum()) for c in range(len(CATS))}
    props = {k: (v / max(len(zero), 1)) for k, v in counts.items()}
    log(f"category counts: {counts}")

    # Half 1: separability from latent features WITHOUT the defining rules.
    idx = zero[okmask[zero]]
    perm = np.random.default_rng(3).permutation(len(idx))
    cut = len(idx) // 2
    tr, te = idx[perm[:cut]], idx[perm[cut:]]
    pred = nearest_centroid(X[tr], lab[tr], X[te], len(CATS))
    bacc = balanced_accuracy(lab[te], pred, len(CATS))
    per_cat = {}
    for c in range(len(CATS)):
        m = lab[te] == c
        per_cat[CATS[c]] = float((pred[m] == c).mean()) if m.sum() >= 5 else None
    log(f"balanced accuracy: {bacc:.3f}; per-category {per_cat}")

    # Half 2: is G6 blind? Build two subsamples matched on G6 and on
    # base-to-base skew, and compare their category proportions. Matching is
    # by rejection over random subsamples rather than by construction, so
    # neither corpus is engineered toward a category.
    def g6_and_skew(sub: np.ndarray):
        b = base[sub]
        _, i_qb = knn(b, queries, KS[0])
        c = np.bincount(i_qb.ravel(), minlength=len(b)).astype(float)
        g6 = float(((c - c.mean()) ** 3).mean() / max(c.std() ** 3, 1e-12))
        _, i_bb = knn(b, b, KS[0] + 1)
        cb = np.bincount(i_bb[:, 1:].ravel(), minlength=len(b)).astype(float)
        skew = float(((cb - cb.mean()) ** 3).mean() / max(cb.std() ** 3, 1e-12))
        return g6, skew

    rs = np.random.default_rng(11)
    half = len(base) // 2
    cands = []
    for _ in range(6):
        sub = rs.choice(len(base), size=half, replace=False)
        g6, sk = g6_and_skew(sub)
        cands.append((g6, sk, sub))
        log(f"  candidate subsample: G6={g6:.3f} bb_skew={sk:.3f}")
    # Pick the pair closest in BOTH statistics.
    best = None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            d = abs(cands[i][0] - cands[j][0]) + abs(cands[i][1] - cands[j][1])
            if best is None or d < best[0]:
                best = (d, i, j)
    _, i, j = best
    pair_props = []
    for which in (i, j):
        sub = cands[which][2]
        sl = lab[sub]
        z = sl[sl >= 0]
        pair_props.append(
            {
                CATS[c]: float((z == c).mean()) if len(z) else 0.0
                for c in range(len(CATS))
            }
        )
    ratios = {
        c: (
            max(pair_props[0][c], pair_props[1][c])
            / max(min(pair_props[0][c], pair_props[1][c]), 1e-9)
        )
        for c in CATS
    }
    matched = {
        "g6": [cands[i][0], cands[j][0]],
        "bb_skew": [cands[i][1], cands[j][1]],
        "proportions": pair_props,
        "max_ratio_per_category": ratios,
    }
    log(
        f"matched-pair category ratios: { {k: round(v, 2) for k, v in ratios.items()} }"
    )

    half1 = bool(bacc >= 0.6)
    half2 = bool(max(ratios.values()) >= 2.0)
    verdict = {
        "P13B_half1_separable": half1,
        "balanced_accuracy": bacc,
        "P13B_half2_g6_blind": half2,
        "max_category_ratio_at_matched_G6": float(max(ratios.values())),
        "reading": (
            "the battery's lower tail is an unmeasured axis: categories are "
            "real and G6 cannot see them"
            if (half1 and half2)
            else "see failure clauses in PREREG_ROUND13 §5"
        ),
    }
    return {
        "meta": {
            "prereg": "results/PREREG_ROUND13.md P-13B",
            "n_base": int(len(base)),
            "n_query": int(len(queries)),
            "k": KS[0],
            "categories": CATS,
            "rule": "categories assigned by LATENT rule; separability tested "
            "without those rules, on held-out points",
        },
        "n_never_retrieved": int(len(zero)),
        "category_counts": counts,
        "category_proportions": props,
        "separability": {"balanced_accuracy": bacc, "per_category": per_cat},
        "g6_blindness": matched,
        "verdict": verdict,
        "retrieval_slots_per_point": float(len(queries) * KS[0] / max(len(base), 1)),
    }


def main() -> None:
    log("R13 STAGE 1 — anti-hub taxonomy (P-13B), swept over corpus size")
    runs = []
    for n in NS:
        log(f"--- n_base = {n} ---")
        runs.append(run_one(n))
    primary = next(
        (
            r
            for r in runs
            if r["meta"]["n_base"] <= 8100 and r["meta"]["n_base"] >= 7000
        ),
        runs[0],
    )
    out = {
        "meta": {
            "prereg": "results/PREREG_ROUND13.md P-13B",
            "sizes": NS,
            "primary_n": primary["meta"]["n_base"],
            "primary_rationale": "harness convention: 8000 base + 1000 queries",
        },
        "runs": runs,
        "verdict": primary["verdict"],
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log(json.dumps(primary["verdict"], indent=1))
    log("R13_STAGE1_DONE")


if __name__ == "__main__":
    main()
