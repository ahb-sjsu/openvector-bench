"""Fix the G1 slope: heavy-tailed duplicate separations.

`R27` matched the profile trend (+0.987 +/- 0.086 against +0.978, replicated
over four seeds) but G1 falls 10-17x too steeply — exponent -0.72 to -1.24
against real's -0.073 — and G1 sits at ~6 against real's ~17.

The diagnosis is specific. With a single perturbation scale and a duplicate
fraction of 0.6, *most* rows have a sigma-close partner, so `r1` is ~sigma for
almost every point and TwoNN reads a degenerate dimension. Worse, as n grows the
tree deepens and such pairs accumulate, so G1 keeps falling. A real corpus is
not like that: a few passages are near-exact duplicates, more are paraphrases,
many are merely same-topic. Most points have *no* extremely close neighbour.

So the separation should be drawn from a **heavy-tailed distribution** rather
than fixed:

    sigma_i = sigma0 * exp(tau * xi_i),   xi ~ N(0, 1)

`tau = 0` recovers R27's fixed-sigma construction exactly and is retained as a
control — if it does not reproduce +0.99 with G1 ~6, the harness differs from
R27 and nothing else here can be trusted.

Larger `tau` spreads separations across orders of magnitude: a few very close
pairs supply the fine structure the ramp needs, while the bulk sit far enough
out that `r1` does not collapse for every point. The prediction is that G1's
*level* rises toward 17 and its *slope* flattens toward -0.073, while the trend
survives.

Three quantities are now scored, because R27 showed trend alone is satisfiable
while the rest is wrong:

* trend        target +0.978
* G1 level     target 17.7 (mean over rungs)
* G1 exponent  target -0.073   <- the defect being fixed

Env: HT_DIM, HT_NS, HT_NQ, HT_SEEDS, HT_OUT.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("HT_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

DIM = int(os.environ.get("HT_DIM", "1024"))
NS = json.loads(os.environ.get("HT_NS", "[5000, 10000, 20000]"))
NQ = int(os.environ.get("HT_NQ", "2000"))
SEEDS = json.loads(os.environ.get("HT_SEEDS", "[21, 22]"))
OUT = os.environ.get("HT_OUT", "results/dup_heavytail.json")
TARGETS = os.environ.get("HT_TARGETS", "results/small_rung_targets.json")


def build(n, dim, rng, base_dim, frac, cos_target, tau):
    """Low-dim base + recursive duplication at a TARGET PARENT-CHILD COSINE.

    sigma is not an interpretable knob: a source row with base_dim=20 has norm
    ~sqrt(20)=4.5, while a sigma-perturbation in 1024 dims has norm 32*sigma, so
    sigma=0.15 already exceeds the signal (cosine ~0.68) and means something
    different at every base_dim. The sweep then runs from near-duplicate to
    noise-dominated without that being visible in the parameter.

    Parameterising by the parent-child cosine fixes that and is directly
    comparable to the data: real's 4-NN sits at r = 0.93, i.e. cosine ~0.57.
    For unit-normalised parent u and isotropic noise, cos = 1/sqrt(1+s^2) where
    s is the perturbation norm relative to the parent's, so s = sqrt(1/c^2 - 1).
    """
    n_base = max(1, int(round(n * (1.0 - frac))))
    basis = np.linalg.qr(rng.standard_normal((dim, base_dim)))[0].astype(np.float32)
    x = np.empty((n, dim), dtype=np.float32)
    x[:n_base] = rng.standard_normal((n_base, base_dim)).astype(np.float32) @ basis.T
    filled, block = n_base, max(256, n_base // 8)
    while filled < n:
        take = min(block, n - filled)
        src = rng.integers(0, filled, take)
        # relative perturbation implied by the target cosine, jittered when
        # tau > 0 (in cosine space, clipped to stay a duplicate rather than noise)
        c = np.clip(
            cos_target
            * np.exp(np.float32(tau) * rng.standard_normal(take).astype(np.float32)),
            0.05,
            0.999,
        ).astype(np.float32)
        rel = np.sqrt(1.0 / c**2 - 1.0).astype(np.float32)
        parent = x[src]
        pnorm = np.linalg.norm(parent, axis=1, keepdims=True)
        noise = rng.standard_normal((take, dim)).astype(np.float32)
        noise /= np.maximum(np.linalg.norm(noise, axis=1, keepdims=True), 1e-12)
        x[filled : filled + take] = parent + (rel[:, None] * pnorm) * noise
        filled += take
    return x


def arm(base_dim, frac, sigma0, tau) -> dict:
    trends, g1_exps, g1_means = [], [], []
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        nmax = max(NS)
        x = normalize(build(nmax + NQ, DIM, rng, base_dim, frac, sigma0, tau))
        q = x[nmax:]
        ratios, g1s = [], []
        for n in NS:
            r2 = np.random.default_rng(sd * 7 + n)
            bi = r2.choice(nmax, size=n, replace=False)
            d, _ = knn(x[bi], q, max(PROFILE_KGRID))
            ratios.append(profile_ratio(d))
            g1s.append(float(id_twonn(d)))
        trends.append(float(np.polyfit(np.log(NS), ratios, 1)[0]))
        g1_exps.append(
            float(np.polyfit(np.log(NS), np.log(np.maximum(g1s, 1e-3)), 1)[0])
        )
        g1_means.append(float(np.mean(g1s)))
    return {
        "trend": float(np.mean(trends)),
        "trend_sd": float(np.std(trends, ddof=1)) if len(trends) > 1 else 0.0,
        "g1_exp": float(np.mean(g1_exps)),
        "g1_mean": float(np.mean(g1_means)),
    }


def main() -> int:
    tg = json.load(open(TARGETS))
    ns_ok = [n for n in NS if str(n) in tg]
    t_trend = float(
        np.polyfit(np.log(ns_ok), [tg[str(n)]["ratio"] for n in ns_ok], 1)[0]
    )
    t_g1 = [tg[str(n)]["g1"] for n in ns_ok]
    t_g1_exp = float(np.polyfit(np.log(ns_ok), np.log(t_g1), 1)[0])
    t_g1_mean = float(np.mean(t_g1))
    print(
        f"TARGET  trend {t_trend:+.3f}   G1 mean {t_g1_mean:.1f}   "
        f"G1 exponent {t_g1_exp:+.3f}\n",
        flush=True,
    )

    def score(v):
        return (
            abs(v["trend"] - t_trend) / abs(t_trend)
            + abs(np.log(max(v["g1_mean"], 1e-3) / t_g1_mean))
            + abs(v["g1_exp"] - t_g1_exp) / 0.3
        )

    res, t0 = {}, time.time()
    print(
        f"{'arm':34s} {'trend':>14s} {'G1 mean':>8s} {'G1 exp':>8s} {'score':>7s}",
        flush=True,
    )
    for base_dim in (20, 40):
        for frac in (0.6, 0.85):
            for sigma0 in (0.95, 0.85, 0.70, 0.57):
                for tau in (0.0, 0.3):
                    name = f"d{base_dim}_f{frac}_cos{sigma0}_t{tau}"
                    v = arm(base_dim, frac, sigma0, tau)
                    v["score"] = score(v)
                    res[name] = v
                    print(
                        f"{name:34s} {v['trend']:+7.3f}+/-{v['trend_sd']:.3f} "
                        f"{v['g1_mean']:8.1f} {v['g1_exp']:+8.3f} {v['score']:7.3f}",
                        flush=True,
                    )

    best = min(res.items(), key=lambda kv: kv[1]["score"])
    ctrl = {k: v for k, v in res.items() if k.endswith("_t0.0")}
    print(
        f"\ncontrol (tau=0, should reproduce R27): "
        f"trend {np.mean([v['trend'] for v in ctrl.values()]):+.3f}, "
        f"G1 mean {np.mean([v['g1_mean'] for v in ctrl.values()]):.1f}",
        flush=True,
    )
    print(
        f"best: {best[0]}  trend {best[1]['trend']:+.3f} (target {t_trend:+.3f})  "
        f"G1 mean {best[1]['g1_mean']:.1f} (target {t_g1_mean:.1f})  "
        f"G1 exp {best[1]['g1_exp']:+.3f} (target {t_g1_exp:+.3f})",
        flush=True,
    )
    improved = best[1]["score"] < min(v["score"] for v in ctrl.values())
    print(f"heavy tail improves on fixed sigma: {improved}", flush=True)
    print(f"({time.time()-t0:.0f}s)", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {"dim": DIM, "ns": NS, "nq": NQ, "seeds": SEEDS},
                "target": {"trend": t_trend, "g1_mean": t_g1_mean, "g1_exp": t_g1_exp},
                "arms": res,
                "best": best[0],
                "heavy_tail_improves": bool(improved),
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("DUP_HEAVYTAIL_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
