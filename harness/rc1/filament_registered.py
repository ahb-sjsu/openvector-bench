"""The filament family at the REGISTERED protocol — the test that decides.

Everything in `R28` was measured at reduced rungs (5k/10k/20k) against targets
from a 60k pool. `R24` established that **density**, not row count, governs this
profile: the same corpus gives trend +0.978 from a 60k pool and +0.440 from a
600k pool. So the registered target is not a stricter version of what the family
was tuned against — it is a *different point*, and this is a re-tune rather than
a re-measurement.

Registered targets, measured under the registered protocol
(`registered_targets.json`, 600k pool, 10k holdout, uniform per-rung draws):

    n=25k   ratio 1.287   G1 25.97   mu 1.0300   mu>1.5 0.0123
    n=50k   ratio 1.609   G1 22.84   mu 1.0340   mu>1.5 0.0124
    n=100k  ratio 1.897   G1 20.40   mu 1.0398   mu>1.5 0.0175

    trend +0.440   G1 mean 23.1   G1 exponent -0.174   mu 1.035   mu>1.5 0.014

The pool is 600k so that **density at each rung matches the registered
protocol** — using a smaller pool would change the very variable R24 identified
as governing.

Prediction, before the run: the current best arm already sits at G1 exponent
-0.171 against -0.174, but its trend is +1.146 against +0.440 — 2.6x too high.
`fil_scale` lowers trend while raising G1, and G1 also needs to rise (20.9 ->
23.1), so both errors point the same way. The registered-optimal `fil_scale`
should therefore be well above the 0.20 that won at reduced scale. If no
`fil_scale` brings the trend down at acceptable G1, the family fits at reduced
scale and fails at registered scale, and that is the honest end of it.

Env: FR_FS, FR_PT, FR_FD, FR_AD, FR_CAP, FR_NS, FR_NQ, FR_OUT.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("FR_THREADS", "6"))

from openvector_bench.filament_gen import (  # noqa: E402
    FILAMENT_POOL_PARAMS,
    filament_pool_corpus,
)
from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    growth_slope,
    id_twonn,
    knn,
    profile_ratio,
)

CAP = int(os.environ.get("FR_CAP", "600000"))
NS = json.loads(os.environ.get("FR_NS", "[25000, 50000, 100000]"))
NQ = int(os.environ.get("FR_NQ", "10000"))
FS = json.loads(os.environ.get("FR_FS", "[0.25, 0.35, 0.45]"))
PT = json.loads(os.environ.get("FR_PT", "[4.0]"))
FD = json.loads(os.environ.get("FR_FD", "[48]"))
AD = json.loads(os.environ.get("FR_AD", "[40]"))
OUT = os.environ.get("FR_OUT", "results/filament_registered.json")
TARGETS = os.environ.get("FR_TARGETS", "results/registered_targets.json")
SEED = 41
DIM = 1024


def params(pt, fd, ad, fs):
    p = dict(
        zip([s[0] for s in FILAMENT_POOL_PARAMS], [s[3] for s in FILAMENT_POOL_PARAMS])
    )
    p.update(
        points_per_thread=pt,
        fil_dim=fd,
        arrange_dim=ad,
        fil_scale=fs,
        log2_basis=13.0,
        dup_frac=0.01,
        dup_cos=0.95,
    )
    return p


def evaluate(x) -> dict:
    """Registered protocol: uniform holdout, uniform per-rung draws."""
    hr = np.random.default_rng(7)
    h = hr.choice(len(x), NQ, replace=False)
    m = np.zeros(len(x), dtype=bool)
    m[h] = True
    q, pool = x[m], x[~m]
    ratios, g1s, mus, mufr, slo = [], [], [], [], []
    for n in NS:
        r2 = np.random.default_rng(10_000 + n)
        bi = r2.choice(len(pool), min(n, len(pool)), replace=False)
        d, _ = knn(pool[bi], q, max(PROFILE_KGRID))
        ratios.append(profile_ratio(d))
        g1s.append(float(id_twonn(d)))
        _, s = growth_slope(d)
        slo.append(float(s[0]))
        mu = d[:, 1] / np.maximum(d[:, 0], 1e-12)
        mus.append(float(np.median(mu)))
        mufr.append(float((mu > 1.5).mean()))
    ln = np.log(NS)
    return {
        "ratios": ratios,
        "g1": g1s,
        "s_lo": slo,
        "trend": float(np.polyfit(ln, ratios, 1)[0]),
        "g1_exp": float(np.polyfit(ln, np.log(g1s), 1)[0]),
        "g1_mean": float(np.mean(g1s)),
        "mu_med": float(np.mean(mus)),
        "mu_frac": float(np.mean(mufr)),
    }


def main() -> int:
    tg = json.load(open(TARGETS))
    ns_ok = [n for n in NS if str(n) in tg]
    t_ratios = [tg[str(n)]["ratio"] for n in ns_ok]
    t_g1 = [tg[str(n)]["g1"] for n in ns_ok]
    ln = np.log(ns_ok)
    T = {
        "trend": float(np.polyfit(ln, t_ratios, 1)[0]),
        "g1_mean": float(np.mean(t_g1)),
        "g1_exp": float(np.polyfit(ln, np.log(t_g1), 1)[0]),
        "mu_med": float(np.mean([tg[str(n)]["mu_med"] for n in ns_ok])),
        "mu_frac": float(np.mean([tg[str(n)]["mu_frac"] for n in ns_ok])),
    }
    print(
        f"REGISTERED TARGET  trend {T['trend']:+.3f}  G1 {T['g1_mean']:.1f}  "
        f"G1exp {T['g1_exp']:+.3f}  mu {T['mu_med']:.4f}  "
        f"mu>1.5 {T['mu_frac']:.4f}",
        flush=True,
    )
    print(f"pool {CAP}, rungs {NS}, nq {NQ} — density matches registered\n", flush=True)

    def score(v):
        return (
            abs(v["trend"] - T["trend"]) / abs(T["trend"])
            + abs(np.log(max(v["g1_mean"], 1e-3) / T["g1_mean"]))
            + abs(v["g1_exp"] - T["g1_exp"]) / 0.3
            + abs(v["mu_med"] - T["mu_med"]) / 0.05
            + abs(v["mu_frac"] - T["mu_frac"]) / 0.05
        )

    res = {}
    for pt in PT:
        for fd in FD:
            for ad in AD:
                for fs in FS:
                    name = f"pt{pt}_fd{fd}_ad{ad}_fs{fs}"
                    t0 = time.time()
                    x = filament_pool_corpus(params(pt, fd, ad, fs), CAP, DIM, SEED)
                    tg_ = time.time() - t0
                    v = evaluate(x)
                    v["score"] = score(v)
                    res[name] = v
                    del x
                    print(
                        f"{name:26s} trend {v['trend']:+7.3f}  "
                        f"G1 {v['g1_mean']:6.2f}  G1exp {v['g1_exp']:+7.3f}  "
                        f"mu {v['mu_med']:.4f}  mu>1.5 {v['mu_frac']:.4f}  "
                        f"score {v['score']:6.2f}  ({tg_:.0f}s gen, "
                        f"{time.time()-t0:.0f}s total)",
                        flush=True,
                    )

    best = min(res.items(), key=lambda kv: kv[1]["score"])
    print(f"\nbest: {best[0]}  score {best[1]['score']:.2f}", flush=True)
    print(
        f"  ratios {[round(r,3) for r in best[1]['ratios']]} "
        f"(target {[round(r,3) for r in t_ratios]})",
        flush=True,
    )
    print(
        f"  G1     {[round(g,2) for g in best[1]['g1']]} "
        f"(target {[round(g,2) for g in t_g1]})",
        flush=True,
    )

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "target": T,
                "config": {"cap": CAP, "ns": NS, "nq": NQ, "seed": SEED},
                "arms": res,
                "best": best[0],
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("FILAMENT_REGISTERED_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
