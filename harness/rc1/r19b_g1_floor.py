"""Why does G1 bottom out at ~37 however small local_dim gets?

R19 swept local_dim from 94 down to 12 and G1 fell only from about 62 to
about 41, bottoming near local_dim 18 to 24 at G1 around 37 and rising again
below that. Something other than local_dim sets the measured dimension at the
bottom of the range. A floor at 37 against a target reaching 18.4 would block
a corrected family too, so it is worth one cheap diagnostic before any family
is designed.

The hypothesis is **between-cluster geometry**. A query's k nearest neighbours
need not all lie in one cluster. When they span clusters, the two-NN estimator
reads the arrangement of cluster centres in ambient space rather than the
within-cluster subspace, and that arrangement does not care what local_dim is.

Three arms, and the prediction for each is registered here before the run.

    PURE     local_dim swept, ONE cluster. No between-cluster geometry exists,
             so if the hypothesis holds G1 should track local_dim all the way
             down and show no floor.
    FROZEN   local_dim swept at the frozen 78 clusters. Should reproduce the
             floor near 37.
    KSWEEP   cluster count swept at local_dim fixed low. If the hypothesis
             holds G1 should RISE with cluster count, since more centres means
             a richer between-cluster arrangement for neighbours to span.

Also measured per configuration: **neighbour purity**, the fraction of each
query's k nearest neighbours drawn from the same cluster as its nearest
neighbour overall. Purity near 1 means neighbourhoods stay inside a cluster
and the hypothesis is wrong. Purity well below 1 means they span, which is the
mechanism the hypothesis needs.

Purity is the direct measurement and the arms are the intervention. Reporting
both means the mechanism is not inferred from the outcome alone, which is the
mistake rounds 15 through 17 kept making.

Reported, not gated.

Env: R19B_OUT, R19B_FROZEN, R19B_N, R19B_DIM, R19B_SEEDS, R19B_K, R19B_NQ.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    hier_query_corpus,
)
from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

OUT = os.environ.get("R19B_OUT", "results/r19b_g1_floor.json")
FROZEN = os.environ.get("R19B_FROZEN", "results/r14_frozen_corpus.json")
N = int(os.environ.get("R19B_N", "25000"))
DIM = int(os.environ.get("R19B_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R19B_SEEDS", "[0, 1]"))
K = int(os.environ.get("R19B_K", "10"))
NQ = int(os.environ.get("R19B_NQ", "10000"))

LDS = json.loads(os.environ.get("R19B_LDS", "[6, 12, 24, 48, 94]"))
LOG2KS = json.loads(os.environ.get("R19B_LOG2KS", "[0, 2, 4, 6.2812, 8]"))
LD_LOW = float(os.environ.get("R19B_LD_LOW", "12"))
REAL_G1_AT_N = 26.64  # P-17cG corrected target at n = 25,000


def log(m: str) -> None:
    print(m, flush=True)


def run(params0: dict, local_dim: float, log2k: float, seed: int):
    """G1 and neighbour purity for one configuration."""
    pr = dict(params0)
    pr["local_dim"] = float(local_dim)
    pr["log2_clusters"] = float(log2k)
    pr.pop("cluster_growth", None)  # plain path; count is set, not emergent
    gen_n = int(round((N + NQ) / (1.0 - QUERY_FRAC)))
    x = hier_query_corpus(pr, gen_n, DIM, seed)
    b, q = normalize(x[:N]), normalize(x[N : N + NQ])
    d, idx = knn(b, q, K)
    g1 = id_twonn(d)

    # Purity without needing the generator's labels: cluster each base point by
    # its nearest of the k_clusters centres is unavailable here, so use the
    # neighbour graph itself. For each query, the fraction of its k neighbours
    # that are also among the k neighbours of its own top-1 neighbour. If
    # neighbourhoods sit inside one tight cluster this is high; if they span
    # clusters it falls.
    top1 = idx[:, 0]
    _, nidx = knn(b, b[top1], K)
    purity = float(
        np.mean([len(set(idx[i]) & set(nidx[i])) / K for i in range(len(idx))])
    )
    return g1, purity


def main() -> None:
    params0 = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    k_frozen = float(params0["log2_clusters"])
    log("R19b G1 FLOOR - is between-cluster geometry setting the floor?")
    log(
        f"n={N} dim={DIM} k={K} nq={NQ} seeds={SEEDS}; real G1 here = "
        f"{REAL_G1_AT_N}"
    )

    out: dict = {
        "meta": {
            "question": "what sets G1 when local_dim is small?",
            "hypothesis": "between-cluster geometry; neighbours span clusters so "
            "the two-NN estimator reads the arrangement of centres",
            "n": N,
            "dim": DIM,
            "k": K,
            "n_query": NQ,
            "seeds": SEEDS,
            "real_g1_at_n": REAL_G1_AT_N,
            "status": "reported, not gated",
        },
        "arms": {},
    }

    for arm, lds, log2k in (
        ("PURE", LDS, 0.0),
        ("FROZEN", LDS, k_frozen),
    ):
        rows = []
        for ld in lds:
            g = [run(params0, ld, log2k, s) for s in SEEDS]
            g1 = float(np.mean([a for a, _ in g]))
            pu = float(np.mean([b for _, b in g]))
            rows.append({"local_dim": ld, "g1": g1, "purity": pu})
            log(f"  {arm:<7} local_dim={ld:>3}  G1={g1:>6.2f}  purity={pu:.3f}")
        out["arms"][arm] = rows

    rows = []
    for lk in LOG2KS:
        g = [run(params0, LD_LOW, lk, s) for s in SEEDS]
        g1 = float(np.mean([a for a, _ in g]))
        pu = float(np.mean([b for _, b in g]))
        kk = int(round(2**lk))
        rows.append({"log2_clusters": lk, "clusters": kk, "g1": g1, "purity": pu})
        log(f"  KSWEEP  clusters={kk:>4}  G1={g1:>6.2f}  purity={pu:.3f}")
    out["arms"]["KSWEEP"] = rows

    pure = out["arms"]["PURE"]
    froz = out["arms"]["FROZEN"]
    ks = out["arms"]["KSWEEP"]
    pure_tracks = bool(pure[0]["g1"] < 0.6 * froz[0]["g1"])
    k_raises = bool(ks[-1]["g1"] > 1.3 * ks[0]["g1"])
    spans = bool(np.mean([r["purity"] for r in froz]) < 0.8)

    if pure_tracks and k_raises:
        reading = (
            f"Confirmed. With one cluster G1 falls to {pure[0]['g1']:.1f} at "
            f"local_dim {pure[0]['local_dim']}, against {froz[0]['g1']:.1f} at "
            f"the frozen cluster count, and G1 rises from {ks[0]['g1']:.1f} to "
            f"{ks[-1]['g1']:.1f} as clusters go from {ks[0]['clusters']} to "
            f"{ks[-1]['clusters']}. Between-cluster geometry sets the floor. A "
            f"corrected family must therefore control how neighbourhoods span "
            f"clusters, not just the within-cluster dimension, and lowering "
            f"local_dim alone will never reach real's G1."
        )
    elif pure_tracks:
        reading = (
            "Partly confirmed. Removing clusters removes the floor, but the "
            "cluster-count sweep does not raise G1 proportionately, so the "
            "floor depends on the presence of between-cluster structure rather "
            "than on how much of it there is."
        )
    elif k_raises:
        reading = (
            "Partly confirmed. Cluster count raises G1, but a single cluster "
            "does not remove the floor, so between-cluster geometry adds to a "
            "floor it did not create. Something within the cluster also resists "
            "low local_dim."
        )
    else:
        reading = (
            "Refuted. Neither removing clusters nor sweeping their count moves "
            "the floor, so between-cluster geometry is not what sets G1 at low "
            "local_dim. The floor lives inside the cluster construction and the "
            "next diagnostic should look there."
        )
    log(
        f"mean purity at frozen clusters = "
        f"{np.mean([r['purity'] for r in froz]):.3f} "
        f"({'neighbourhoods span clusters' if spans else 'neighbourhoods stay local'})"
    )
    log(reading)

    out["neighbourhoods_span_clusters"] = spans
    out["pure_removes_floor"] = pure_tracks
    out["cluster_count_raises_g1"] = k_raises
    out["reading"] = reading
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R19B_FLOOR_DONE")


if __name__ == "__main__":
    main()
