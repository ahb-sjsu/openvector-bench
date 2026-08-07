"""Where does the round-8 family's hub-scaling rise actually come from?

The plan's amendment asserts that the family's only defect on this axis is
its Zipf cluster-choice law, and proposes replacing that law. The assertion
was not measured. It has a plausible competitor: the cluster COUNT is fixed
at ``2**log2_clusters`` while n grows, so every cluster densifies, and the
rise could be a within-cluster competition effect that changing the
between-cluster law would not touch.

Intervening on the wrong term is how rounds 15 and 16 were spent. This
decomposes the attractiveness variance before anything is built.

Method. A first version tried an observational decomposition, splitting the
attractiveness variance into within-neighbourhood and between-neighbourhood
terms. It was wrong and its smoke run said so, reporting a within term larger
than the total. The law of total variance needs a partition, and overlapping
k-nearest-neighbour sets are not one.

This is an intervention instead, which is both sounder and more direct. Two
arms differing in exactly one thing.

    FIXED    the frozen point, cluster count held at 2**log2_clusters
    GROWING  the same point with log2_clusters raised so the cluster count
             scales as n**0.5, every other parameter identical

If the slope falls toward real under GROWING, the rise is a densification
effect of a fixed cluster count and the cluster-choice law is the wrong
target. If the slope is unchanged, the fixed count is exonerated and the
choice law stands accused.

Reported, not gated. The registered use is to decide which law round 17
should modify.

Env: R17D_OUT, R17D_FROZEN, R17D_NS, R17D_DIM, R17D_SEEDS, R17D_RHO, R17D_K.
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
from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.hubness import attractiveness_skew  # noqa: E402

OUT = os.environ.get("R17D_OUT", "results/r17_decompose.json")
FROZEN = os.environ.get("R17D_FROZEN", "results/r14_frozen_corpus.json")
NS = json.loads(os.environ.get("R17D_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R17D_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R17D_SEEDS", "[0, 1, 2, 3, 4, 5, 6, 7]"))
RHO = float(os.environ.get("R17D_RHO", "4.0"))
K = int(os.environ.get("R17D_K", "10"))


def log(m: str) -> None:
    print(m, flush=True)


def slope_lin(xs, ys) -> float:
    x = np.log10(np.asarray(xs, float))
    y = np.asarray(ys, float)
    ok = np.isfinite(y)
    return float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float("nan")


def main() -> None:
    params = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    log("R17 INTERVENTION — is the rise caused by a fixed cluster count?")
    log(f"ladder {NS} at rho={RHO}, dim={DIM}, seeds={SEEDS}")

    n_ref = min(NS)
    base_log2 = float(params["log2_clusters"])
    rows = []
    for arm in ("FIXED", "GROWING"):
        per_seed = []
        for sd in SEEDS:
            vals = []
            for n in NS:
                pr = dict(params)
                if arm == "GROWING":
                    # cluster count proportional to sqrt(n), matched to the
                    # frozen value at the bottom rung so the arms coincide there
                    pr["log2_clusters"] = base_log2 + 0.5 * np.log2(n / n_ref)
                nq = max(50, int(round(RHO * n / K)))
                gen_n = int(round((n + nq) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, sd)
                b, q = normalize(x[:n]), normalize(x[n : n + nq])
                _, idx = knn(b, q, K)
                c = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
                vals.append(attractiveness_skew(c))
            per_seed.append(slope_lin(NS, vals))
        m = float(np.nanmean(per_seed))
        sem = float(np.nanstd(per_seed, ddof=1) / np.sqrt(len(per_seed)))
        rows.append({"arm": arm, "slope": m, "sem": sem, "per_seed": per_seed})
        log(f"  {arm:8s} slope={m:+.3f} +/- {sem:.3f}")

    fixed, growing = rows[0]["slope"], rows[1]["slope"]
    sem_diff = float(np.hypot(rows[0]["sem"], rows[1]["sem"]))
    moved = bool((fixed - growing) > 2 * sem_diff)

    if moved and abs(growing - 0.51) <= 0.2:
        reading = (
            "Growing the cluster count moves the slope to real's value. The "
            "rise is a densification effect of a fixed cluster count, and the "
            "cluster-choice law is the wrong target. The plan's amendment "
            "needs revising before round 17 is built."
        )
    elif moved:
        reading = (
            "Growing the cluster count moves the slope but not to real's "
            "value. The fixed count is part of the cause and not all of it, "
            "so a one-parameter modification of either law is unlikely to "
            "suffice on its own."
        )
    else:
        reading = (
            "Growing the cluster count does not move the slope. The fixed "
            "count is exonerated and the cluster-choice law stands accused, "
            "so the plan's amendment stands as written."
        )
    log(reading)

    out = {
        "meta": {
            "question": "does the round-8 family's hub-scaling rise come from "
            "the between-cluster choice law or from within-cluster "
            "densification at fixed cluster count?",
            "frozen_source": FROZEN,
            "ns": NS,
            "dim": DIM,
            "rho": RHO,
            "k": K,
            "seeds": SEEDS,
            "note": "reported, not gated; decides which law round 17 modifies",
        },
        "arms": rows,
        "slope_difference": fixed - growing,
        "sem_of_difference": sem_diff,
        "moved": moved,
        "reading": reading,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R17_DECOMPOSE_DONE")


if __name__ == "__main__":
    main()
