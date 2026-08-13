"""Does the filament family reproduce real's rising dimension profile?

Same protocol as `scale_probe4.py`: 600k pool, one uniform 10k holdout, uniform
per-rung draws, identical k grid and estimator. Real's curve is read back from
`scale_probe4.json` so the comparison is against a matched measurement.

Readings, in the order that would kill the family:

1. **Sign.** Does s(r) RISE? Every prior family either fell (Whitney flags,
   null_lowrank) or was flat by construction (cascades, conformal, elliptic).
2. **Null.** `fil_dim == arrange_dim` removes the two-scale structure and must
   flatten the profile. A family that cannot express its own null is not being
   measured.
3. **n-trend.** Real's beta STRENGTHENS as n grows (~1.8 at 25k to ~4.8 at
   200k) because larger n reaches further down into the low-dimensional regime.
   A cascade's does not (bitmap_L60: +3.09 -> +2.22). Matching real's beta at
   one n is cheap; matching its trend is the real test, and it is the statistic
   that distinguishes a genuine two-scale construction from a flat one that
   happens to cross the same value.
4. **Level.** s_lo -> s_hi against real's ~15.7 -> ~37.8.
"""

from __future__ import annotations

import gc
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.filament_gen import FILAMENT_PARAMS, filament_corpus  # noqa: E402
from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

OUT = os.environ.get("SP_OUT", "/home/claude/ovb_scale/scale_probe5.json")
REF = os.environ.get("SP_REF", "/home/claude/ovb_scale/scale_probe4.json")
NS = json.loads(os.environ.get("SP_NS", "[25000, 50000, 100000, 200000]"))
NQ = int(os.environ.get("SP_NQ", "10000"))
KMAX = int(os.environ.get("SP_KMAX", "500"))
CAP = int(os.environ.get("SP_CAP", "600000"))
SEED = int(os.environ.get("SP_SEED", "11"))
DIM = 1024

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})

# (label, fil_dim, arrange_dim, fil_scale, scale_spread)
ARMS = [
    ("fd8_ad40", 8.0, 40.0, 0.15, 0.5),
    ("NULL_fd40_ad40", 40.0, 40.0, 0.15, 0.5),  # no two-scale structure
    ("fd4_ad40", 4.0, 40.0, 0.15, 0.5),
    ("fd8_ad40_wide", 8.0, 40.0, 0.30, 1.0),  # wider crossover -> gentler ramp
]


def main() -> int:
    hrng = np.random.default_rng(7)
    hidx = hrng.choice(CAP, size=NQ, replace=False)
    hmask = np.zeros(CAP, dtype=bool)
    hmask[hidx] = True

    ref = None
    if os.path.exists(REF):
        ref = json.load(open(REF))["results"].get("real")
        if ref:
            print("real reference (scale_probe4):", flush=True)
            for n in NS:
                c = ref["per_n"][str(n)]
                print(f"  real          n={n:6d} G1={c['g1_twonn']:7.2f} "
                      f"s {c['s_lo']:6.1f} -> {c['s_hi']:6.1f} beta={c['beta']:+7.2f}",
                      flush=True)

    results: dict[str, dict] = {}
    for label, fd, ad, fs, sp in ARMS:
        p = dict(zip([s[0] for s in FILAMENT_PARAMS], [s[3] for s in FILAMENT_PARAMS]))
        p.update(fil_dim=fd, arrange_dim=ad, fil_scale=fs, scale_spread=sp)
        x = filament_corpus(p, CAP, DIM, SEED)
        q = normalize(x[hmask])
        base_pool = x[~hmask]
        per_n = {}
        for n in NS:
            rng = np.random.default_rng(10_000 + n)
            bi = rng.choice(len(base_pool), size=min(n, len(base_pool)), replace=False)
            d, _ = knn(normalize(base_pool[bi]), q, KMAX)
            r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
            s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
            beta = float(np.log(s[-1] / max(s[0], 1e-9)) / np.log(r[-1] / r[0]))
            per_n[str(n)] = {"g1_twonn": float(id_twonn(d)), "r": r.tolist(),
                             "s": s.tolist(), "s_lo": float(s[0]), "s_hi": float(s[-1]),
                             "s_ratio": float(s[-1] / max(s[0], 1e-9)), "beta": beta}
            print(f"{label:16s} n={n:6d} G1={per_n[str(n)]['g1_twonn']:7.2f} "
                  f"s {s[0]:6.1f} -> {s[-1]:6.1f} (x{per_n[str(n)]['s_ratio']:.2f}) "
                  f"beta={beta:+7.2f}  r {r[0]:.3f}..{r[-1]:.3f}", flush=True)
        betas = [per_n[str(n)]["beta"] for n in NS]
        trend = float(np.polyfit(np.log(NS), betas, 1)[0])
        results[label] = {"per_n": per_n, "beta_mean": float(np.mean(betas)),
                          "beta_trend_per_ln_n": trend}
        print(f"  -> {label}: beta_mean {np.mean(betas):+.2f} "
              f"beta_trend {trend:+.2f} per ln n", flush=True)
        del x, q, base_pool
        gc.collect()

    if ref:
        rb = [ref["per_n"][str(n)]["beta"] for n in NS]
        rtrend = float(np.polyfit(np.log(NS), rb, 1)[0])
        print(f"\nreal beta_mean {np.mean(rb):+.2f} trend {rtrend:+.2f} per ln n",
              flush=True)
        for label in results:
            r_ = results[label]
            print(f"  {label:16s} beta_mean {r_['beta_mean']:+.2f} "
                  f"trend {r_['beta_trend_per_ln_n']:+.2f}", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"config": {"ns": NS, "nq": NQ, "cap": CAP, "kgrid": KGRID,
                              "seed": SEED, "arms": ARMS}, "results": results}, f,
                  indent=2)
    print(f"wrote {OUT}", flush=True)
    print("SCALE_PROBE5_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
