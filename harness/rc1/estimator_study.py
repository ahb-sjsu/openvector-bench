"""Which location estimator should the campaign use for per-seed slopes?

Round 17b was defeated by its estimator rather than by its family. Var(w) was
healthy in every cell, but the third moment that attractiveness_skew divides
by it depends on the extreme upper tail of the count distribution, so a single
draw can produce a per-seed slope of -19 against a typical +0.5. A mean over
twelve such seeds is not a usable summary.

This picks the replacement. There is a contamination problem to handle first
and it is stated rather than hidden. **The r17b medians have already been
seen**, and they happen to rescue that round's verdict. So the choice cannot
be made on r17b's arms without the choice being circular.

The estimator is therefore selected on synthetic data with known ground truth.
The noise model is calibrated from r17b's per-seed spreads, which is what
pilot variance is for and is not the same as tuning on the outcome. Nothing
here reads r17b's slopes or its verdict.

Model. Per-seed slopes are drawn as a contaminated normal,

    (1 - eps) * Normal(mu, sigma) + eps * Normal(mu_out, sigma_out)

with mu the true slope, sigma from r17b's well-behaved seeds, and the
contaminating component large and negative, matching the -19.1, -5.0 and -4.5
seeds observed. Contamination rates are swept because the true rate is not
known.

Reported for each estimator: bias, root mean squared error, and the power to
separate two families differing by 0.5, which is the effect the campaign needs
to resolve. The seed count that reaches 80 percent power is read off directly
and becomes the registered seed count.

Reported, not gated. Its output is an amendment to the spec, not an admission.

Env: ES_OUT, ES_TRIALS, ES_SEEDS_GRID, ES_EPS_GRID, ES_EFFECT.
"""

from __future__ import annotations

import json
import os

import numpy as np

OUT = os.environ.get("ES_OUT", "results/estimator_study.json")
TRIALS = int(os.environ.get("ES_TRIALS", "20000"))
SEEDS_GRID = json.loads(os.environ.get("ES_SEEDS_GRID", "[12, 20, 32, 48, 64]"))
EPS_GRID = json.loads(os.environ.get("ES_EPS_GRID", "[0.0, 0.04, 0.08, 0.17]"))
EFFECT = float(os.environ.get("ES_EFFECT", "0.5"))

# Calibrated from round 17b's well-behaved seeds, which span roughly -1.6 to
# +1.5 around a centre near +0.5, and from its three contaminating draws at
# -19.1, -5.0 and -4.5. Fixed here before any estimator is compared.
MU_TRUE = 0.5
SIGMA = 0.7
MU_OUT = -8.0
SIGMA_OUT = 6.0


def log(m: str) -> None:
    print(m, flush=True)


def draw(rng, n, mu, eps):
    """One experiment's worth of per-seed slopes under contamination."""
    x = rng.normal(mu, SIGMA, size=n)
    if eps > 0:
        hit = rng.random(n) < eps
        x[hit] = rng.normal(MU_OUT, SIGMA_OUT, size=int(hit.sum()))
    return x


def trimmed(x, frac=0.2):
    y = np.sort(x)
    c = int(np.floor(len(y) * frac))
    return float(y[c : len(y) - c].mean()) if len(y) - 2 * c > 0 else float(y.mean())


def huber(x, c=1.345, iters=25):
    """Huber M-estimate with a MAD scale, the standard robust default."""
    m = float(np.median(x))
    s = 1.4826 * float(np.median(np.abs(x - m))) or 1e-9
    for _ in range(iters):
        r = (x - m) / s
        w = np.where(np.abs(r) <= c, 1.0, c / np.maximum(np.abs(r), 1e-12))
        m_new = float((w * x).sum() / w.sum())
        if abs(m_new - m) < 1e-12:
            break
        m = m_new
    return m


ESTIMATORS = {
    "mean": lambda x: float(x.mean()),
    "median": lambda x: float(np.median(x)),
    "trimmed20": trimmed,
    "huber": huber,
}
# Breakdown point, the fraction of arbitrary contamination each tolerates.
BREAKDOWN = {"mean": 0.0, "median": 0.5, "trimmed20": 0.2, "huber": 0.5}


def main() -> None:
    log("ESTIMATOR STUDY - synthetic, ground truth known, r17b outcomes unread")
    log(
        f"true slope {MU_TRUE}, sigma {SIGMA}, contaminant "
        f"N({MU_OUT}, {SIGMA_OUT}), effect to resolve {EFFECT}"
    )

    rng = np.random.default_rng(12345)
    rows = []
    for eps in EPS_GRID:
        for n in SEEDS_GRID:
            a = np.stack([draw(rng, n, MU_TRUE, eps) for _ in range(TRIALS)])
            b = np.stack([draw(rng, n, MU_TRUE - EFFECT, eps) for _ in range(TRIALS)])
            for name, fn in ESTIMATORS.items():
                ea = np.array([fn(v) for v in a])
                eb = np.array([fn(v) for v in b])
                bias = float(ea.mean() - MU_TRUE)
                rmse = float(np.sqrt(((ea - MU_TRUE) ** 2).mean()))
                # Power: how often the two arms are correctly ordered by more
                # than half the effect, which is the campaign's usable signal.
                power = float((ea - eb > EFFECT / 2).mean())
                rows.append(
                    {
                        "eps": eps,
                        "n_seeds": n,
                        "estimator": name,
                        "breakdown_point": BREAKDOWN[name],
                        "bias": bias,
                        "rmse": rmse,
                        "power": power,
                    }
                )
            best = max(
                (r for r in rows if r["eps"] == eps and r["n_seeds"] == n),
                key=lambda r: r["power"],
            )
            log(
                f"  eps={eps:.2f} n={n:>3}  best={best['estimator']:<10} "
                f"power={best['power']:.3f}  "
                + "  ".join(
                    f"{r['estimator']}={r['power']:.2f}"
                    for r in rows
                    if r["eps"] == eps and r["n_seeds"] == n
                )
            )

    # The registered choice: highest worst-case power across contamination
    # rates, tie-broken by breakdown point. Decided by rule, not by inspection.
    worst = {}
    for name in ESTIMATORS:
        per_n = {}
        for n in SEEDS_GRID:
            per_n[n] = min(
                r["power"] for r in rows if r["estimator"] == name and r["n_seeds"] == n
            )
        worst[name] = per_n
    chosen = max(
        ESTIMATORS,
        key=lambda nm: (max(worst[nm].values()), BREAKDOWN[nm]),
    )
    need = [n for n in SEEDS_GRID if worst[chosen][n] >= 0.80]
    n_req = min(need) if need else None

    log(f"chosen estimator: {chosen} (breakdown {BREAKDOWN[chosen]})")
    log(
        "worst-case power by seed count: "
        + ", ".join(f"n={n}:{worst[chosen][n]:.2f}" for n in SEEDS_GRID)
    )
    log(f"seeds for 80 percent worst-case power: {n_req}")

    out = {
        "meta": {
            "question": "which location estimator and seed count should the "
            "campaign register for per-seed slopes?",
            "contamination_note": "the r17b medians were already seen, so the "
            "choice is made on synthetic data with known ground truth; only "
            "r17b's per-seed SPREAD is used, as pilot variance",
            "model": {
                "mu_true": MU_TRUE,
                "sigma": SIGMA,
                "mu_out": MU_OUT,
                "sigma_out": SIGMA_OUT,
            },
            "effect": EFFECT,
            "trials": TRIALS,
            "decision_rule": "highest worst-case power across contamination "
            "rates, tie-broken by breakdown point",
        },
        "grid": rows,
        "worst_case_power": worst,
        "chosen_estimator": chosen,
        "seeds_for_80pct_power": n_req,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("ESTIMATOR_STUDY_DONE")


if __name__ == "__main__":
    main()
