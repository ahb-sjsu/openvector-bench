"""Campaign stage 0: does the round-8 family already scale correctly?

CAMPAIGN_PLAN_ROUNDS_17_19 §2. Round 8's winning point is the campaign's
best result and the basis of round 14, and its hub-scaling slope has never
been measured. It is a corpus/query construction rather than a popularity
draw, so the round-16 exclusion does not apply to it, and it may already
have the property rounds 17 to 19 exist to obtain.

This is the shared instrument of §3 applied to one already-frozen point.
Nothing is fitted. The corpus parameters come from
``results/r14_frozen_corpus.json`` unchanged.

Registered outcomes, from the plan:

  slope within +/-0.15 of +0.51  -> the corpus/query split already scales
                                    correctly; rounds 17 to 19 are not run
                                    and round 14 proceeds directly.
  slope near +2.9                -> the problem is deeper than any family
                                    so far; rounds 17 to 19 proceed.
  anything between               -> report the value and decide with data
                                    rather than by the plan.

The tail-shape diagnostic of §3 is reported alongside, because skew alone
cannot distinguish a sub-power-law tail from one that happened to land
somewhere. It gates nothing here; it is the baseline the three families
will be compared against.

Env: R17S0_OUT, R17S0_FROZEN, R17S0_NS, R17S0_DIM, R17S0_SEEDS, R17S0_RHO,
R17S0_K.
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
from openvector_bench.hubness import (  # noqa: E402
    attractiveness_skew,
    rho,
    tail_excess,
)

OUT = os.environ.get("R17S0_OUT", "results/r17_stage0.json")
FROZEN = os.environ.get("R17S0_FROZEN", "results/r14_frozen_corpus.json")
NS = json.loads(os.environ.get("R17S0_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R17S0_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R17S0_SEEDS", "[0, 1, 2, 3, 4]"))
RHO = float(os.environ.get("R17S0_RHO", "4.0"))
K = int(os.environ.get("R17S0_K", "10"))

TARGET, TOL = 0.51, 0.15
CODEBOOK_REFERENCE = 2.9  # rounds 15 and 16 both landed near here


def log(m: str) -> None:
    print(m, flush=True)


def slope(xs, ys) -> float:
    x = np.log10(np.asarray(xs, float))
    y = np.asarray(ys, float)
    ok = np.isfinite(y)
    return float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float("nan")


def tail_shape(counts: np.ndarray) -> dict:
    """Power law versus stretched exponential on the upper decile.

    Positive log-likelihood ratio favours the power law, which is the
    scale-invariant shape rounds 15 and 16 failed with. Negative favours a
    stretched exponential, the sub-power-law shape saturation should give.
    Reported, not gated, and fitted on counts above the ninetieth percentile
    where the two families actually differ.
    """
    c = np.asarray(counts, dtype=np.float64)
    c = c[c > 0]
    if len(c) < 200:
        return {"n_tail": int(len(c)), "loglik_ratio": float("nan")}
    cut = np.quantile(c, 0.90)
    t = c[c >= cut]
    if len(t) < 50 or t.min() <= 0:
        return {"n_tail": int(len(t)), "loglik_ratio": float("nan")}
    x = t / t.min()
    # Power law: MLE exponent via Hill estimator.
    a = 1.0 + len(x) / max(np.log(x).sum(), 1e-12)
    ll_pl = len(x) * np.log(a - 1.0) - a * np.log(x).sum()
    # Stretched exponential with shape fitted on a coarse grid, scale by MLE.
    best = -np.inf
    for beta in np.linspace(0.2, 1.0, 17):
        lam = (np.power(x, beta).mean()) ** (-1.0 / beta)
        ll = (
            len(x) * (np.log(beta) + beta * np.log(lam))
            + (beta - 1.0) * np.log(x).sum()
            - np.power(lam * x, beta).sum()
        )
        best = max(best, float(ll))
    return {
        "n_tail": int(len(t)),
        "hill_exponent": float(a),
        "loglik_ratio": float(ll_pl - best),
        "favours": "power_law" if ll_pl > best else "stretched_exponential",
    }


def main() -> None:
    frozen = json.load(open(FROZEN, encoding="utf-8"))
    params = dict(frozen["params"])
    log("CAMPAIGN STAGE 0 — round-8 family hub scaling")
    log(f"frozen params from {FROZEN}")
    log(f"ladder {NS} at constant rho={RHO}, dim={DIM}, seeds={SEEDS}, k={K}")

    cells, per_seed = [], []
    for sd in SEEDS:
        vals = []
        for n in NS:
            nq = max(50, int(round(RHO * n / K)))
            total = n + nq
            # The family carries its own query block at QUERY_FRAC; generate
            # enough rows that the base is n after that split, then take the
            # query block this protocol needs from the tail.
            gen_n = int(round(total / (1.0 - QUERY_FRAC)))
            x = hier_query_corpus(params, gen_n, DIM, sd)
            base, q = normalize(x[:n]), normalize(x[n : n + nq])
            _, idx = knn(base, q, K)
            c = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
            a = attractiveness_skew(c)
            vals.append(a)
            cells.append(
                {
                    "seed": sd,
                    "n": n,
                    "nq": nq,
                    "rho": rho(nq, K, n),
                    "attractiveness_skew": a,
                    "tail_excess_1pct": tail_excess(c, n, 0.01),
                    "zero_frac": float((c == 0).mean()),
                    "tail_shape": tail_shape(c),
                }
            )
        s = slope(NS, vals)
        per_seed.append(s)
        log(f"  seed {sd}: skew {[round(v, 2) for v in vals]}  slope={s:+.3f}")

    mean_slope = float(np.nanmean(per_seed))
    spread = float(np.nanmax(per_seed) - np.nanmin(per_seed))
    # Conclusiveness is the standard error of the mean, not the max-min
    # range. Range was the first choice and it is the wrong statistic: it
    # grows with the number of seeds, so adding seeds would make a better
    # measurement look worse. SEM shrinks as 1/sqrt(seeds), which is what
    # "the mean is now a measurement" actually means.
    #
    # Checked before adopting, because changing a criterion after seeing a
    # result is the trap this campaign keeps paying for: at the five-seed
    # run that motivated the change, SEM was 0.15 and |mean - target| was
    # 0.22, so the switch does not manufacture a pass. It changes only
    # whether the run is allowed to claim anything at all.
    sem = float(np.nanstd(per_seed, ddof=1) / np.sqrt(len(per_seed)))
    conclusive = bool(sem <= TOL)
    hits = bool(conclusive and abs(mean_slope - TARGET) <= TOL)
    near_codebook = bool(conclusive and abs(mean_slope - CODEBOOK_REFERENCE) <= 0.6)

    if not conclusive:
        verdict = (
            f"Inconclusive. Standard error of the mean is {sem:.3f}, above "
            f"the {TOL} tolerance, so the mean cannot be placed against "
            "either registered outcome. More seeds or a wider ladder are "
            "needed before this decides anything."
        )
    elif hits:
        verdict = (
            "The round-8 corpus/query split already scales correctly. Rounds "
            "17 to 19 are not run; round 14's query-model search proceeds."
        )
    elif near_codebook:
        verdict = (
            "The round-8 family scales like the codebook families, so the "
            "problem is deeper than any family so far. Rounds 17 to 19 "
            "proceed as planned."
        )
    else:
        verdict = (
            "Between the two registered outcomes. Report the value and decide "
            "with data rather than by the plan."
        )

    log(
        f"\nslope={mean_slope:+.3f} (spread {spread:.3f}) against target "
        f"{TARGET:+.2f}+/-{TOL} and codebook reference {CODEBOOK_REFERENCE:+.1f}"
    )
    log(verdict)

    out = {
        "meta": {
            "plan": "results/CAMPAIGN_PLAN_ROUNDS_17_19.md stage 0",
            "family": "hier_query_corpus at the frozen round-8 point",
            "frozen_source": FROZEN,
            "target": TARGET,
            "tolerance": TOL,
            "codebook_reference": CODEBOOK_REFERENCE,
            "ns": NS,
            "dim": DIM,
            "rho": RHO,
            "k": K,
            "seeds": SEEDS,
            "note": "nothing fitted; the point is frozen and unchanged",
        },
        "cells": cells,
        "slope": mean_slope,
        "per_seed": per_seed,
        "spread": spread,
        "sem": sem,
        "conclusive": conclusive,
        "within_target": hits,
        "near_codebook_reference": near_codebook,
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R17_STAGE0_DONE")


if __name__ == "__main__":
    main()
