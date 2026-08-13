"""Calibration: the filament family's knob -> statistic transfer function.

Six probes in, four design constants have each been wrong and each was caught by
an expensive confirmatory run: the noise floor (bitmap), m0 by 10x (bitmap), a
mis-specified null (filament), and the fixed-F artifact (filament). All four
would have surfaced in a one-factor sweep costing minutes. This runs the
calibration that should have preceded `scale_probe5`.

The point is NOT to find a passing setting. It is to measure d(statistic)/d(knob)
so that parameters can be SOLVED for against the target instead of guessed, and
to establish -- before any expensive arm -- that each statistic responds to the
knob it is supposed to respond to.

Target (real, measured on the 600k pool, `scale_probe4.json`):

    n        G1      s_lo    s_hi    beta
    25,000   25.97   27.4    35.2    +1.80
    200,000  18.28   15.7    37.3    +4.80
    beta trend +1.41 per ln n; radius band 0.888..1.125

Design decisions, stated:

* One factor at a time around a base point, n = 25,000 with 10k queries and the
  registered k grid, so every cell is directly comparable to real's 25k row.
* Corpora are generated at n + NQ directly rather than drawn from a 600k pool.
  For this family that is nearly equivalent -- uniform subsampling preserves the
  points-per-filament ratio that drives the geometry -- and it makes ~25 cells
  affordable. Absolute values may shift slightly against the pool protocol.
* An n-sweep at two filament counts is included, because the failure that has
  killed every arm (beta trend) is a family x n interaction, not a parameter
  effect, and cannot be seen in a parameter-only sweep.
"""

from __future__ import annotations

import gc
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.filament_gen import FILAMENT_PARAMS, filament_corpus  # noqa: E402
from openvector_bench.geometry import id_twonn, knn  # noqa: E402

OUT = os.environ.get("CAL_OUT", "/home/claude/ovb_scale/calib_filament.json")
N = int(os.environ.get("CAL_N", "25000"))
NQ = int(os.environ.get("CAL_NQ", "10000"))
KMAX = int(os.environ.get("CAL_KMAX", "500"))
SEED = int(os.environ.get("CAL_SEED", "11"))
DIM = 1024

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})

BASE = dict(
    log2_filaments=14.0,
    fil_dim=8.0,
    arrange_dim=40.0,
    fil_scale=0.15,
    scale_spread=0.5,
    size_tail=1.0,
    noise=0.01,
)

# One factor at a time. Each entry: (knob, [values])
OFAT = [
    ("fil_dim", [2.0, 4.0, 8.0, 16.0, 32.0]),
    ("arrange_dim", [16.0, 40.0, 64.0, 128.0]),
    ("fil_scale", [0.05, 0.15, 0.30, 0.50, 0.80]),
    ("scale_spread", [0.0, 0.5, 1.0]),
    ("log2_filaments", [10.0, 12.0, 14.0, 16.0]),
]

N_SWEEP = [10000, 25000, 60000, 140000]
N_SWEEP_ARMS = [("F14", 14.0), ("F17", 17.0)]


def params(**kw) -> dict:
    p = dict(zip([s[0] for s in FILAMENT_PARAMS], [s[3] for s in FILAMENT_PARAMS]))
    p.update(BASE)
    p.update(kw)
    return p


def cell(p: dict, n: int) -> dict:
    x = filament_corpus(p, n + NQ, DIM, SEED)
    d, _ = knn(x[:n], x[n:], KMAX)
    r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
    s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
    beta = float(np.log(s[-1] / max(s[0], 1e-9)) / np.log(r[-1] / r[0]))
    # crossover: radius where s is halfway between its endpoints
    mid = 0.5 * (s[0] + s[-1])
    try:
        cross = float(np.interp(mid, s, r)) if s[-1] > s[0] else float("nan")
    except Exception:
        cross = float("nan")
    out = {
        "g1": float(id_twonn(d)),
        "s_lo": float(s[0]),
        "s_hi": float(s[-1]),
        "r_lo": float(r[0]),
        "r_hi": float(r[-1]),
        "beta": beta,
        "crossover_r": cross,
        # estimator domain check (the R20 precondition), per cell
        "usable_mu_frac": float((d[:, 1] / np.maximum(d[:, 0], 1e-12) > 1.0).mean()),
    }
    del x, d
    gc.collect()
    return out


def main() -> int:
    print(f"base {BASE}  n={N} nq={NQ} kmax={KMAX}", flush=True)
    print(
        "TARGET real n=25k: G1 25.97  s 27.4->35.2  beta +1.80  r 0.946..1.124\n",
        flush=True,
    )

    results: dict[str, dict] = {"ofat": {}, "n_sweep": {}}

    for knob, values in OFAT:
        results["ofat"][knob] = {}
        for v in values:
            c = cell(params(**{knob: v}), N)
            results["ofat"][knob][str(v)] = c
            print(
                f"{knob:16s}={v:7.2f}  G1={c['g1']:7.2f}  "
                f"s {c['s_lo']:6.1f}->{c['s_hi']:6.1f}  beta={c['beta']:+6.2f}  "
                f"r {c['r_lo']:.3f}..{c['r_hi']:.3f}  cross={c['crossover_r']:.3f}  "
                f"mu_ok={c['usable_mu_frac']:.2f}",
                flush=True,
            )
        # sensitivity: dlog(stat)/dlog(knob) across the swept range
        vs = np.array([float(v) for v in values])
        for stat in ("s_lo", "s_hi", "g1"):
            y = np.array([results["ofat"][knob][str(v)][stat] for v in values])
            ok = (y > 0) & (vs > 0)
            if ok.sum() >= 2:
                sl = float(np.polyfit(np.log(vs[ok]), np.log(y[ok]), 1)[0])
                print(
                    f"    sensitivity dlog({stat})/dlog({knob}) = {sl:+.2f}", flush=True
                )
        print("", flush=True)

    # The failure that killed every arm is a family x n interaction.
    for label, lf in N_SWEEP_ARMS:
        results["n_sweep"][label] = {}
        betas = []
        for n in N_SWEEP:
            c = cell(params(log2_filaments=lf), n)
            results["n_sweep"][label][str(n)] = c
            betas.append(c["beta"])
            print(
                f"{label} n={n:6d}  G1={c['g1']:7.2f}  "
                f"s {c['s_lo']:6.1f}->{c['s_hi']:6.1f}  beta={c['beta']:+6.2f}",
                flush=True,
            )
        tr = float(np.polyfit(np.log(N_SWEEP), betas, 1)[0])
        results["n_sweep"][label]["beta_trend"] = tr
        print(
            f"  -> {label} beta trend {tr:+.2f} per ln n   (real +1.41)\n", flush=True
        )

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "n": N,
                    "nq": NQ,
                    "kmax": KMAX,
                    "kgrid": KGRID,
                    "base": BASE,
                    "n_sweep": N_SWEEP,
                },
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("CALIB_FILAMENT_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
