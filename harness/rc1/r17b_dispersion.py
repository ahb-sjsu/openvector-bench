"""Was the estimator in its stable regime when round 17b's gate read it?

Round 17b's arms produced standard errors from 0.19 to 1.68, and one arm
returned -1.923 +/- 1.677. That pattern is not a family with a wide effect,
it is an estimator dividing by something near zero.

``attractiveness_skew`` deconvolves a Poisson observation. With c|w ~
Poisson(rho*w) it recovers Var(w) = (Var(c) - rho) / rho**2 and divides the
recovered third moment by Var(w)**1.5. When a family's attractiveness signal
weakens, Var(c) falls toward rho, the dispersion index Var(c)/mean(c) falls
toward 1, and Var(w) approaches zero, so the ratio diverges. The guard in
``hubness.py`` only returns NaN below 1e-9, and just above that it returns
enormous finite numbers that a slope fit will happily consume.

This measures the dispersion index and the recovered Var(w) per cell, so the
gate's result can say which cells were readable instead of leaving the whole
sweep ambiguous. Reported, not gated.

Env: R17BD_OUT, R17BD_FROZEN, R17BD_CALIB, R17BD_NS, R17BD_DIM, R17BD_SEEDS,
R17BD_RHO, R17BD_K.
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

OUT = os.environ.get("R17BD_OUT", "results/r17b_dispersion.json")
FROZEN = os.environ.get("R17BD_FROZEN", "results/r14_frozen_corpus.json")
CALIB = os.environ.get("R17BD_CALIB", "results/r17b_calibration.json")
NS = json.loads(os.environ.get("R17BD_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R17BD_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R17BD_SEEDS", "[0, 1, 2, 3]"))
RHO = float(os.environ.get("R17BD_RHO", "4.0"))
K = int(os.environ.get("R17BD_K", "10"))

# Var(w) below this makes the cube-root-of-variance denominator dominate the
# estimate. Chosen as the value at which a 12-seed SEM exceeds the effect the
# sweep was designed to resolve, and recorded here so it is not tuned later.
VAR_W_FLOOR = 0.05


def log(m: str) -> None:
    print(m, flush=True)


def main() -> None:
    params0 = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    arms = json.load(open(CALIB, encoding="utf-8"))["arms"]

    log("R17b DISPERSION - was the estimator readable in each cell?")
    log(
        f"ladder {NS}, rho={RHO}, dim={DIM}, seeds={SEEDS}, "
        f"Var(w) floor {VAR_W_FLOOR}"
    )

    rows = []
    for arm in arms:
        a, cap = float(arm["growth"]), float(arm["capacity"])
        cells = []
        for n in NS:
            di, vw = [], []
            for sd in SEEDS:
                pr = {**params0, "cluster_growth": a, "cluster_capacity": cap}
                nq = max(50, int(round(RHO * n / K)))
                gen_n = int(round((n + nq) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, sd)
                b, q = normalize(x[:n]), normalize(x[n : n + nq])
                _, idx = knn(b, q, K)
                c = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
                m, v = float(c.mean()), float(c.var())
                di.append(v / max(m, 1e-12))
                vw.append((v - m) / max(m, 1e-12) ** 2)
            cells.append(
                {
                    "n": n,
                    "dispersion_index": float(np.mean(di)),
                    "var_w": float(np.mean(vw)),
                    "readable": bool(np.mean(vw) >= VAR_W_FLOOR),
                }
            )
            log(
                f"  alpha={a:.2f} n={n:>6} dispersion={np.mean(di):.3f} "
                f"Var(w)={np.mean(vw):.4f} "
                f"{'readable' if np.mean(vw) >= VAR_W_FLOOR else 'UNREADABLE'}"
            )
        rows.append(
            {
                "growth": a,
                "cells": cells,
                "all_readable": all(c["readable"] for c in cells),
            }
        )

    readable = [r["growth"] for r in rows if r["all_readable"]]
    log(f"arms readable in every cell: {readable}")

    out = {
        "meta": {
            "question": "was attractiveness_skew in its stable regime in the "
            "cells round 17b's gate read?",
            "ns": NS,
            "dim": DIM,
            "rho": RHO,
            "k": K,
            "seeds": SEEDS,
            "var_w_floor": VAR_W_FLOOR,
            "note": "reported, not gated; decides which of the gate's arms "
            "carry an interpretable slope",
        },
        "arms": rows,
        "readable_arms": readable,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R17B_DISPERSION_DONE")


if __name__ == "__main__":
    main()
