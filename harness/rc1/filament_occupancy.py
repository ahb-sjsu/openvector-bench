"""Was R21C's filament exclusion a fixed-F artifact? Sweep thread occupancy.

## Why revisit a closed family

`real_mu.json` establishes that real has **essentially no near-duplicates**:
mu = r2/r1 has median 1.052, only 1.7% of points exceed mu > 1.5, and only 3.4%
have r1 < 0.5, with a median nearest neighbour at 0.79. That is a smooth
~17-dimensional local structure, not a duplicate structure.

Which means the duplicate family (`R27`) matched the profile trend through a
mechanism real does not use — a Goodhart success — and it explains why no
parameterisation could fix G1: the ultra-close pairs generating the ramp are
exactly what suppresses G1.

If real's ramp is not duplicates, it must come from **smooth multi-scale
structure**: local dimension ~15 at r ~ 0.89 rising to ~37 at r ~ 1.06, with no
degeneracy anywhere. That is the filament shape — low-dimensional locally,
high-dimensional in the arrangement — and it is now the only shape consistent
with the mu data.

`R21C` excluded filaments because `s_lo` RISES with n where real's falls. But
that was measured with a **fixed** thread count, so points-per-thread grew with
n; the saturation may be a property of that parameterisation rather than of the
shape. This sweeps thread occupancy directly.

## What is swept, and what is scored

Occupancy is expressed as **points per thread in the pool**, so the thread count
scales with pool size rather than being fixed. Rungs subsample the pool exactly
as the registered protocol does, so per-thread occupancy at each rung follows
from the draw, as it does for real.

Five quantities are scored, not one. `R27` matched the trend while missing
everything else, so:

* trend            target +0.978
* G1 level         target 17.7
* G1 exponent      target -0.073
* **mu median**    target 1.052   <- the duplicate guard
* **frac mu>1.5**  target 0.017   <- ditto

An arm that hits the trend by manufacturing duplicates now fails visibly
instead of looking like progress.

Env: FO_DIM, FO_NS, FO_NQ, FO_SEEDS, FO_OUT.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("FO_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

DIM = int(os.environ.get("FO_DIM", "1024"))
NS = json.loads(os.environ.get("FO_NS", "[5000, 10000, 20000]"))
NQ = int(os.environ.get("FO_NQ", "2000"))
SEEDS = json.loads(os.environ.get("FO_SEEDS", "[31, 32]"))
OUT = os.environ.get("FO_OUT", "results/filament_occupancy.json")
TARGETS = os.environ.get("FO_TARGETS", "results/small_rung_targets.json")

# real, measured (real_mu.json)
T_MU_MED = 1.0523
T_MU_FRAC = 0.0167

PT_GRID = json.loads(os.environ.get("FO_PT", "[1.5, 4, 12, 40]"))
FD_GRID = json.loads(os.environ.get("FO_FD", "[8, 16]"))
AD_GRID = json.loads(os.environ.get("FO_AD", "[40, 90]"))
FS_GRID = json.loads(os.environ.get("FO_FS", "[0.25]"))
# Real carries a SMALL near-duplicate population (frac mu>1.5 = 0.017) that the
# pure filament family lacks entirely (0.000). R27 had 60% — 35x too many. This
# overlays duplicates at the proportion real actually exhibits.
DUP_GRID = json.loads(os.environ.get("FO_DUP", "[0.0]"))
DUPCOS_GRID = json.loads(os.environ.get("FO_DUPCOS", "[0.95]"))


def add_duplicates(x, rng, frac, cos_target):
    """Replace a small fraction of rows with near-copies of other rows."""
    if frac <= 0:
        return x
    n = len(x)
    k = int(round(n * frac))
    if k <= 0:
        return x
    tgt = rng.choice(n, k, replace=False)
    src = rng.integers(0, n, k)
    rel = float(np.sqrt(1.0 / cos_target**2 - 1.0))
    parent = x[src]
    pn = np.linalg.norm(parent, axis=1, keepdims=True)
    noise = rng.standard_normal((k, x.shape[1])).astype(np.float32)
    noise /= np.maximum(np.linalg.norm(noise, axis=1, keepdims=True), 1e-12)
    x[tgt] = parent + np.float32(rel) * pn * noise
    return x


def build(n, dim, rng, per_thread, fil_dim, arrange_dim, fil_scale,
          dup_frac=0.0, dup_cos=0.95):
    """Threads whose COUNT scales with n, so occupancy is the swept variable."""
    n_thread = max(2, int(round(n / max(per_thread, 1e-9))))
    basis_a = np.linalg.qr(rng.standard_normal((dim, arrange_dim)))[0].astype(np.float32)
    centres = rng.standard_normal((n_thread, arrange_dim)).astype(np.float32) @ basis_a.T
    centres /= np.maximum(np.linalg.norm(centres, axis=1, keepdims=True), 1e-12)
    owner = rng.integers(0, n_thread, n)
    # one low-dimensional direction set per thread, drawn on demand
    x = np.empty((n, dim), dtype=np.float32)
    order = np.argsort(owner)
    owner_sorted = owner[order]
    bounds = np.searchsorted(owner_sorted, np.arange(n_thread + 1))
    inv = np.sqrt(1.0 / dim).astype(np.float32)
    for t in range(n_thread):
        lo, hi = bounds[t], bounds[t + 1]
        if hi <= lo:
            continue
        b = rng.standard_normal((fil_dim, dim)).astype(np.float32) * inv
        u = rng.standard_normal((hi - lo, fil_dim)).astype(np.float32)
        x[order[lo:hi]] = centres[t] + np.float32(fil_scale) * (u @ b)
    return add_duplicates(x, rng, dup_frac, dup_cos)


def arm(per_thread, fil_dim, arrange_dim, fil_scale,
        dup_frac=0.0, dup_cos=0.95) -> dict:
    trends, g1e, g1m, mus, mufr, slos, shis = [], [], [], [], [], [], []
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        nmax = max(NS)
        x = normalize(build(nmax + NQ, DIM, rng, per_thread, fil_dim,
                            arrange_dim, fil_scale, dup_frac, dup_cos))
        q = x[nmax:]
        ratios, g1s, s_lo, s_hi = [], [], [], []
        for n in NS:
            r2 = np.random.default_rng(sd * 7 + n)
            bi = r2.choice(nmax, size=n, replace=False)
            d, _ = knn(x[bi], q, max(PROFILE_KGRID))
            ratios.append(profile_ratio(d))
            g1s.append(float(id_twonn(d)))
            from openvector_bench.geometry import growth_slope
            _, s = growth_slope(d)
            s_lo.append(float(s[0]))
            s_hi.append(float(s[-1]))
            if n == NS[-1]:
                mu = d[:, 1] / np.maximum(d[:, 0], 1e-12)
                mus.append(float(np.median(mu)))
                mufr.append(float((mu > 1.5).mean()))
        trends.append(float(np.polyfit(np.log(NS), ratios, 1)[0]))
        g1e.append(float(np.polyfit(np.log(NS), np.log(np.maximum(g1s, 1e-3)), 1)[0]))
        g1m.append(float(np.mean(g1s)))
        slos.append(s_lo)
        shis.append(s_hi)
    return {"trend": float(np.mean(trends)), "g1_exp": float(np.mean(g1e)),
            "g1_mean": float(np.mean(g1m)), "mu_med": float(np.mean(mus)),
            "mu_frac": float(np.mean(mufr)),
            "s_lo": [float(v) for v in np.mean(slos, axis=0)],
            "s_hi": [float(v) for v in np.mean(shis, axis=0)]}


def main() -> int:
    tg = json.load(open(TARGETS))
    ns_ok = [n for n in NS if str(n) in tg]
    t_trend = float(np.polyfit(np.log(ns_ok), [tg[str(n)]["ratio"] for n in ns_ok], 1)[0])
    t_g1 = [tg[str(n)]["g1"] for n in ns_ok]
    t_g1_exp = float(np.polyfit(np.log(ns_ok), np.log(t_g1), 1)[0])
    t_g1_mean = float(np.mean(t_g1))
    print(f"TARGET trend {t_trend:+.3f}  G1 {t_g1_mean:.1f}  G1exp {t_g1_exp:+.3f}  "
          f"mu {T_MU_MED:.3f}  mu>1.5 {T_MU_FRAC:.3f}\n", flush=True)

    def score(v):
        return (abs(v["trend"] - t_trend) / abs(t_trend)
                + abs(np.log(max(v["g1_mean"], 1e-3) / t_g1_mean))
                + abs(v["g1_exp"] - t_g1_exp) / 0.3
                + abs(v["mu_med"] - T_MU_MED) / 0.05
                + abs(v["mu_frac"] - T_MU_FRAC) / 0.05)

    res, t0 = {}, time.time()
    print(f"{'arm':30s} {'trend':>7s} {'G1':>6s} {'G1exp':>7s} {'s_lo':>14s} "
          f"{'mu':>6s} {'mu>1.5':>7s} {'score':>7s}", flush=True)
    for per_thread in PT_GRID:
        for fil_dim in FD_GRID:
            for arrange_dim in AD_GRID:
                for fil_scale in FS_GRID:
                  for dupf in DUP_GRID:
                   for dupc in DUPCOS_GRID:
                    name = (f"pt{per_thread}_fd{fil_dim}_ad{arrange_dim}"
                            f"_fs{fil_scale}_dup{dupf}c{dupc}")
                    v = arm(per_thread, fil_dim, arrange_dim, fil_scale,
                            dupf, dupc)
                    v["score"] = score(v)
                    res[name] = v
                    slo = "/".join(f"{s:.0f}" for s in v["s_lo"])
                    print(f"{name:30s} {v['trend']:+7.3f} {v['g1_mean']:6.1f} "
                          f"{v['g1_exp']:+7.3f} {slo:>14s} {v['mu_med']:6.3f} "
                          f"{v['mu_frac']:7.3f} {v['score']:7.2f}", flush=True)

    best = min(res.items(), key=lambda kv: kv[1]["score"])
    b = best[1]
    print(f"\nbest: {best[0]}", flush=True)
    print(f"  trend {b['trend']:+.3f} (t {t_trend:+.3f})  G1 {b['g1_mean']:.1f} "
          f"(t {t_g1_mean:.1f})  G1exp {b['g1_exp']:+.3f} (t {t_g1_exp:+.3f})",
          flush=True)
    print(f"  mu {b['mu_med']:.3f} (t {T_MU_MED:.3f})  mu>1.5 {b['mu_frac']:.3f} "
          f"(t {T_MU_FRAC:.3f})", flush=True)
    # does s_lo FALL with n, as real's does? that is R21C's exclusion criterion
    falls = {k: v for k, v in res.items() if v["s_lo"][-1] < v["s_lo"][0]}
    print(f"\narms where s_lo FALLS with n (real's direction): "
          f"{len(falls)} of {len(res)}", flush=True)
    if falls:
        for k, v in sorted(falls.items(), key=lambda kv: kv[1]["score"])[:4]:
            print(f"   {k:28s} s_lo {'/'.join(f'{s:.1f}' for s in v['s_lo'])} "
                  f"trend {v['trend']:+.3f} G1 {v['g1_mean']:.1f}", flush=True)
    print(f"\nR21C's exclusion was a fixed-F artifact: "
          f"{'SUPPORTED' if falls else 'NOT SUPPORTED — s_lo rises everywhere'}",
          flush=True)
    print(f"({time.time()-t0:.0f}s)", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"target": {"trend": t_trend, "g1_mean": t_g1_mean,
                              "g1_exp": t_g1_exp, "mu_med": T_MU_MED,
                              "mu_frac": T_MU_FRAC},
                   "arms": res, "best": best[0],
                   "n_arms_slo_falls": len(falls)}, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("FILAMENT_OCCUPANCY_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
