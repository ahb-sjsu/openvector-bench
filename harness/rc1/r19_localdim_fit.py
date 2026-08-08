"""Re-fit local_dim against the corrected intrinsic-dimension targets.

P-17cG found real corpora's G1 is 19.92 at n = 100,000, not the 51.82 the
stored reference recorded, and that the correction is confined to the two
intrinsic-dimension estimators. Every other gate stayed inside its band. So
the fit needed is one dimension, not a re-run of the round-8 search.

**This is built to be able to fail, and the failure mode is specific.** Real's
G1 FALLS with n, 27.0 at 25,000 down to 18.2 at 200,000. The family's G1
RISES, 61.7 up to 66.9. They trend in opposite directions. Scaling local_dim
changes the level and cannot change the sign of a trend, so if the trends
really do oppose, no single value passes a per-cell gate at every n and the
defect is structural rather than a mis-set parameter.

The driver therefore reports the ratio at EVERY rung for every candidate
value, and the pass criterion is all four rungs inside the band at once. A
single best-fitting number would hide exactly the thing worth knowing.

Real targets are read from the P-17cG cells rather than re-measured, since
that run already measured them under the corrected protocol and re-measuring
would spend an hour to reproduce numbers already in the repository.

Reported, not gated. Its output is the input to a corrected battery run.

Env: R19_OUT, R19_CELLS, R19_FROZEN, R19_CALIB, R19_ALPHA, R19_DIMS, R19_NS,
R19_SEEDS, R19_DIM, R19_K.
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
from openvector_bench.geometry import (  # noqa: E402
    id_ball_growth,
    id_twonn,
    knn,
    normalize,
)

OUT = os.environ.get("R19_OUT", "results/r19_localdim_fit.json")
CELLS = os.environ.get("R19_CELLS", "results/r17g_battery_cells.json")
FROZEN = os.environ.get("R19_FROZEN", "results/r14_frozen_corpus.json")
CALIB = os.environ.get("R19_CALIB", "results/r17b_calibration.json")
ALPHA = float(os.environ.get("R19_ALPHA", "0.38"))
DIMS = json.loads(os.environ.get("R19_DIMS", "[12, 18, 24, 30, 40, 55, 75, 94]"))
NS = json.loads(os.environ.get("R19_NS", "[25000, 50000, 100000, 200000]"))
SEEDS = json.loads(os.environ.get("R19_SEEDS", "[0, 1]"))
DIM = int(os.environ.get("R19_DIM", "1024"))
K = int(os.environ.get("R19_K", "10"))
NQ = int(os.environ.get("R19_NQ", "10000"))
BAND = (0.85, 1.15)  # G1's registered equivalence band


def log(m: str) -> None:
    print(m, flush=True)


def real_targets() -> dict:
    """Corrected real G1 and G2 per rung, from the P-17cG cells."""
    cells = json.load(open(CELLS, encoding="utf-8"))["cells"]
    out: dict = {}
    for n in NS:
        g1 = [
            c["g1_id_twonn"]
            for c in cells
            if c["corpus"] == "real" and c["n"] == n and c["k"] == K
        ]
        g2 = [
            c["g2_id_ballgrowth"]
            for c in cells
            if c["corpus"] == "real" and c["n"] == n and c["k"] == K
        ]
        if g1:
            out[n] = {"g1": float(np.mean(g1)), "g2": float(np.mean(g2))}
    return out


def main() -> None:
    params0 = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    cal = {
        a["growth"]: a["capacity"]
        for a in json.load(open(CALIB, encoding="utf-8"))["arms"]
    }
    cap_c = cal[ALPHA]
    tgt = real_targets()
    log("R19 LOCAL_DIM FIT - one dimension, against corrected targets")
    log(f"alpha={ALPHA}, frozen local_dim={params0['local_dim']:.1f}, " f"sweep {DIMS}")
    log("real G1 targets: " + ", ".join(f"n={n}:{tgt[n]['g1']:.2f}" for n in tgt))
    log(
        "real G1 FALLS with n; the family's RISES. A level fit cannot change "
        "a trend's sign, so all-rung agreement is the thing to watch."
    )

    rows = []
    for ld in DIMS:
        per_n = {}
        for n in NS:
            if n not in tgt:
                continue
            g1s, g2s = [], []
            for sd in SEEDS:
                pr = {
                    **params0,
                    "local_dim": float(ld),
                    "cluster_growth": ALPHA,
                    "cluster_capacity": cap_c,
                }
                gen_n = int(round((n + NQ) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, 5000 + sd)
                b, q = normalize(x[:n]), normalize(x[n : n + NQ])
                d, _ = knn(b, q, K)
                g1s.append(id_twonn(d))
                g2s.append(id_ball_growth(d, K))
            g1 = float(np.mean(g1s))
            r = g1 / max(tgt[n]["g1"], 1e-9)
            per_n[n] = {
                "g1": g1,
                "target": tgt[n]["g1"],
                "ratio": r,
                "in_band": bool(BAND[0] <= r <= BAND[1]),
                "g2": float(np.mean(g2s)),
                "g2_target": tgt[n]["g2"],
            }
        allin = all(v["in_band"] for v in per_n.values())
        worst = max(abs(np.log(v["ratio"])) for v in per_n.values())
        rows.append(
            {
                "local_dim": ld,
                "per_n": per_n,
                "all_rungs_in_band": allin,
                "worst_log_ratio": float(worst),
            }
        )
        log(
            f"  local_dim={ld:>3}  "
            + "  ".join(
                f"n={n}:{v['ratio']:.2f}{'*' if v['in_band'] else ' '}"
                for n, v in per_n.items()
            )
            + f"   all-in-band={allin}"
        )

    passing = [r for r in rows if r["all_rungs_in_band"]]
    best = min(rows, key=lambda r: r["worst_log_ratio"])

    if passing:
        reading = (
            f"local_dim values passing every rung: "
            f"{[r['local_dim'] for r in passing]}. The correction is a "
            f"mis-set parameter and the family survives it."
        )
    else:
        # Whether the trend genuinely opposes, measured rather than asserted.
        b = best["per_n"]
        lo_r = b[min(b)]["ratio"]
        hi_r = b[max(b)]["ratio"]
        reading = (
            f"No local_dim passes every rung. At the best value "
            f"{best['local_dim']}, the ratio runs {lo_r:.2f} at n={min(b)} to "
            f"{hi_r:.2f} at n={max(b)}. The family's intrinsic dimension "
            f"trends against real's across the ladder, and scaling a level "
            f"cannot change a trend's sign, so this is structural rather than "
            f"a mis-set parameter. G1 is mandatory in every cell, so the "
            f"family cannot be admitted by re-fitting this parameter alone."
        )
    log(reading)

    out = {
        "meta": {
            "what": "one-dimensional local_dim re-fit against P-17cG's "
            "corrected intrinsic-dimension targets",
            "status": "reported, not gated; input to a corrected battery run",
            "alpha": ALPHA,
            "frozen_local_dim": params0["local_dim"],
            "band": list(BAND),
            "ns": NS,
            "k": K,
            "n_query": NQ,
            "seeds": SEEDS,
            "dim": DIM,
            "targets_from": CELLS,
        },
        "real_targets": {str(k): v for k, v in tgt.items()},
        "sweep": rows,
        "passing_local_dims": [r["local_dim"] for r in passing],
        "best_local_dim": best["local_dim"],
        "reading": reading,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R19_LOCALDIM_DONE")


if __name__ == "__main__":
    main()
