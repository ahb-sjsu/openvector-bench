"""Calibration: can the cascade's per-level dimension decay be made to work?

`R21C_FILAMENT_CALIBRATION.md` excluded the filament family because one
characteristic scale saturates: `s_lo` RISES as n resolves the thread, where
real's FALLS (27.4 -> 15.7). Matching real needs structure at every scale with
dimension DECREASING toward finer scales — a hierarchy with a per-level
dimension decay, which is exactly `bitmap_gen`'s `dim_decay` and which has never
functioned.

## Why it never functioned, and the regime never tested

Two failures, each with a different cause, and their union left a gap:

* `scale_decay` 1.6-2.0 WITH `noise` 0.02: the structured displacement is ~1e-4
  by the depth where neighbours separate, three orders under the noise floor.
  TwoNN read 1024-d noise; G1 pinned near 220 regardless of any knob.
* `scale_decay` 1.0-1.08 with `noise` 0: amplitudes flat, so a neighbour
  difference spans the WHOLE tail from l* to L with equal weight. No single
  level dominates, `dim_decay` is swamped, and the drift is finite-depth
  truncation going as 1/(L - log_B n).

**Moderate amplitude decay with a zero noise floor was never run.** That is the
regime where the level at the separating depth should dominate: at
`scale_decay` 1.3 level l* carries ~40% of tail energy and each deeper level
less, so the local dimension should read `m_{l*}` rather than the tail sum.

## The registered prediction

If level l* dominates, dimension ~ `m0 * exp(-dd * l*)` with `l* ~ log_B n`, so

    dlog(s_lo) / dlog(n)  =  -dim_decay / ln B  =  -1.443 * dim_decay   (B=2)

Real's is `ln(15.7/27.4)/ln(8) = -0.268`, which back-solves to
`dim_decay ~ 0.186`. So the test is not "does s_lo fall" but "does its exponent
TRACK -1.443*dd" — a construction constant, which extrapolates, versus a fitted
slope, which does not. That distinction is the whole reason for preferring a
cascade, and it is what R19b's `k^-0.368` lacked.

Falsified if `s_lo`'s n-exponent stays >= 0 across the whole sweep, or if it is
negative but flat in `dim_decay` (i.e. driven by truncation again).

Target (real, `scale_probe4.json`): G1 25.97 -> 18.28 over 25k -> 200k
(exponent -0.168); s_lo 27.4 -> 15.7 (exponent -0.268); s_hi stable ~35-37.
"""

from __future__ import annotations

import gc
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.bitmap_gen import BITMAP_PARAMS, bitmap_corpus  # noqa: E402
from openvector_bench.geometry import id_twonn, knn  # noqa: E402

OUT = os.environ.get("CAL_OUT", "/home/claude/ovb_scale/calib_dimdecay.json")
N = int(os.environ.get("CAL_N", "25000"))
NQ = int(os.environ.get("CAL_NQ", "10000"))
KMAX = int(os.environ.get("CAL_KMAX", "500"))
SEED = int(os.environ.get("CAL_SEED", "11"))
DIM = 1024

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})
LOG_B = math.log(2.0)

BASE = dict(
    log2_branch=1.0,
    depth=60.0,
    scale_decay=1.30,
    dim_decay=0.15,
    m0_frac=0.02,
    split_tail=1.0,
    noise=0.0,
)

N_SWEEP = [10000, 25000, 60000, 140000]


def params(**kw) -> dict:
    p = dict(zip([s[0] for s in BITMAP_PARAMS], [s[3] for s in BITMAP_PARAMS]))
    p.update(BASE)
    p.update(kw)
    return p


def cell(p: dict, n: int) -> dict:
    x = bitmap_corpus(p, n + NQ, DIM, SEED)
    d, _ = knn(x[:n], x[n:], KMAX)
    r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
    s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
    out = {
        "g1": float(id_twonn(d)),
        "s_lo": float(s[0]),
        "s_hi": float(s[-1]),
        "r_lo": float(r[0]),
        "r_hi": float(r[-1]),
        "beta": float(np.log(s[-1] / max(s[0], 1e-9)) / np.log(r[-1] / r[0])),
        "usable_mu_frac": float((d[:, 1] / np.maximum(d[:, 0], 1e-12) > 1.0).mean()),
    }
    del x, d
    gc.collect()
    return out


def main() -> int:
    print(f"base {BASE}  n={N} nq={NQ}", flush=True)
    print(
        "TARGET real: n=25k G1 25.97 s 27.4->35.2 | ladder exponents "
        "G1 -0.168, s_lo -0.268\n",
        flush=True,
    )
    res: dict[str, dict] = {"scale_decay": {}, "dim_decay": {}, "m0": {}, "n_sweep": {}}

    # 1. Does a moderate amplitude decay make the level at l* dominate?
    for sd in [1.0, 1.15, 1.30, 1.60, 2.00]:
        c = cell(params(scale_decay=sd), N)
        res["scale_decay"][str(sd)] = c
        print(
            f"scale_decay={sd:5.2f}  G1={c['g1']:8.2f}  s {c['s_lo']:7.1f}->"
            f"{c['s_hi']:7.1f}  beta={c['beta']:+6.2f}  r {c['r_lo']:.3f}.."
            f"{c['r_hi']:.3f}  mu_ok={c['usable_mu_frac']:.2f}",
            flush=True,
        )

    # 2. Does dim_decay move anything now?
    print("", flush=True)
    for dd in [0.0, 0.05, 0.10, 0.20, 0.35]:
        c = cell(params(dim_decay=dd), N)
        res["dim_decay"][str(dd)] = c
        print(
            f"dim_decay  ={dd:5.2f}  G1={c['g1']:8.2f}  s {c['s_lo']:7.1f}->"
            f"{c['s_hi']:7.1f}  beta={c['beta']:+6.2f}",
            flush=True,
        )

    # 3. Level control, to place s_lo near real's 27.4 at n=25k.
    print("", flush=True)
    for m0 in [0.01, 0.02, 0.04, 0.08]:
        c = cell(params(m0_frac=m0), N)
        res["m0"][str(m0)] = c
        print(
            f"m0_frac    ={m0:5.3f}  G1={c['g1']:8.2f}  s {c['s_lo']:7.1f}->"
            f"{c['s_hi']:7.1f}",
            flush=True,
        )

    # 4. THE decisive test: does s_lo FALL with n, and does its exponent track
    #    the construction constant -1.443 * dim_decay?
    print("", flush=True)
    for dd in [0.0, 0.10, 0.20, 0.35]:
        label = f"dd{dd}"
        res["n_sweep"][label] = {}
        s_los, g1s = [], []
        for n in N_SWEEP:
            c = cell(params(dim_decay=dd), n)
            res["n_sweep"][label][str(n)] = c
            s_los.append(c["s_lo"])
            g1s.append(c["g1"])
            print(
                f"  dd={dd:4.2f} n={n:6d}  G1={c['g1']:8.2f}  "
                f"s {c['s_lo']:7.1f}->{c['s_hi']:7.1f}",
                flush=True,
            )
        ok = np.array(s_los) > 0
        e_slo = (
            float(
                np.polyfit(
                    np.log(np.array(N_SWEEP)[ok]), np.log(np.array(s_los)[ok]), 1
                )[0]
            )
            if ok.sum() > 1
            else float("nan")
        )
        e_g1 = float(np.polyfit(np.log(N_SWEEP), np.log(g1s), 1)[0])
        pred = -dd / LOG_B
        res["n_sweep"][label]["exp_s_lo"] = e_slo
        res["n_sweep"][label]["exp_g1"] = e_g1
        res["n_sweep"][label]["predicted"] = pred
        print(
            f"  -> dd={dd:4.2f}: exp(s_lo)={e_slo:+.3f}  predicted={pred:+.3f}  "
            f"exp(G1)={e_g1:+.3f}   [real: s_lo -0.268, G1 -0.168]\n",
            flush=True,
        )

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "n": N,
                    "nq": NQ,
                    "kmax": KMAX,
                    "base": BASE,
                    "n_sweep": N_SWEEP,
                    "kgrid": KGRID,
                },
                "results": res,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("CALIB_DIMDECAY_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
