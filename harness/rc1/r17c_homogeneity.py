"""Are round 17c's arms distinguishable, or consistent with one common slope?

**Outside the registration.** This licenses no claim about the family. The
registered verdict in ``r17c_gate.json`` stands whatever this reports.

Why it is needed. Round 17c registered outcome B, the flat outcome, as a range
on point estimates, ``max - min <= 0.15``. That criterion is close to
unsatisfiable at the noise level the round already knew about. For five arms
each with a bootstrap standard error near 0.2, the expected range of five
draws from a SINGLE common mean is about 2.33 * sigma, roughly 0.47. So a
genuinely flat family would fail the flatness test most of the time, and a
verdict of C from a test that a true positive also fails carries no
information about the family.

The criterion was mis-specified. It tests dispersion of estimates when what
outcome B claims is that the arms are statistically indistinguishable. Fixing
it after seeing the data is not allowed, so the fix is not applied. This
measures how much the verdict should be believed instead.

Two tests, neither gating.

1. **Permutation, primary.** Pool every per-seed slope, reassign them across
   arms at random keeping the arm sizes, and recompute the range of arm
   medians. The fraction of permutations reaching the observed range is the
   probability that a family with no dependence on the growth exponent would
   look at least this spread out. This calibrates the registered criterion
   against its own null and assumes nothing about the distribution, which
   matters because the per-seed slopes are the heavy-tailed quantity that
   defeated round 17b.

2. **Cochran's Q, secondary.** The standard homogeneity statistic, reported
   for comparability with the meta-analysis convention. It assumes normal
   arm estimates, which the bootstrap medians approximately are even though
   the per-seed slopes are not.

Env: R17CH_OUT, R17CH_GATE, R17CH_PERMS.
"""

from __future__ import annotations

import json
import math
import os

import numpy as np

OUT = os.environ.get("R17CH_OUT", "results/r17c_homogeneity.json")
GATE = os.environ.get("R17CH_GATE", "results/r17c_gate.json")
PERMS = int(os.environ.get("R17CH_PERMS", "20000"))
FLAT_TOL = 0.15  # the registered flatness band, tested here rather than used


def log(m: str) -> None:
    print(m, flush=True)


def chi2_sf(x: float, df: int) -> float:
    """P(X > x) for chi-square. Exact series for even df, else Wilson-Hilferty."""
    if x <= 0:
        return 1.0
    if df % 2 == 0:
        k = df // 2
        t = math.exp(-x / 2.0)
        s, term = t, t
        for i in range(1, k):
            term *= (x / 2.0) / i
            s += term
        return min(1.0, max(0.0, s))
    z = ((x / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(
        2.0 / (9.0 * df)
    )
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def main() -> None:
    gate = json.load(open(GATE, encoding="utf-8"))
    arms = gate["arms"]
    groups = [np.asarray(a["per_seed"], float) for a in arms]
    groups = [g[np.isfinite(g)] for g in groups]
    meds = np.array([np.median(g) for g in groups])
    ses = np.array([float(a["sem"]) for a in arms])
    growths = [float(a["growth"]) for a in arms]

    obs_range = float(meds.max() - meds.min())
    log("R17c HOMOGENEITY - outside the registration, licenses no claim")
    log(
        f"arm medians {np.round(meds, 3).tolist()}  bootstrap SEs "
        f"{np.round(ses, 3).tolist()}"
    )
    log(
        f"observed range {obs_range:.3f} against the registered flat band "
        f"{FLAT_TOL}"
    )

    # 1. Permutation on the registered statistic itself.
    pool = np.concatenate(groups)
    sizes = [len(g) for g in groups]
    rng = np.random.default_rng(20260807)
    ge = 0
    null_ranges = np.empty(PERMS)
    for t in range(PERMS):
        p = rng.permutation(pool)
        i, ms = 0, []
        for s in sizes:
            ms.append(np.median(p[i : i + s]))
            i += s
        r = float(max(ms) - min(ms))
        null_ranges[t] = r
        if r >= obs_range - 1e-12:
            ge += 1
    p_perm = (ge + 1) / (PERMS + 1)
    exp_null = float(null_ranges.mean())
    band_rate = float((null_ranges <= FLAT_TOL).mean())

    log(f"permutation p = {p_perm:.4f}  (null mean range {exp_null:.3f})")
    log(
        f"a truly flat family clears the registered {FLAT_TOL} band "
        f"{band_rate:.1%} of the time"
    )

    # 2. Cochran's Q.
    w = 1.0 / np.maximum(ses, 1e-12) ** 2
    pooled = float((w * meds).sum() / w.sum())
    q = float((w * (meds - pooled) ** 2).sum())
    df = len(meds) - 1
    p_q = chi2_sf(q, df)
    i2 = max(0.0, (q - df) / q) if q > 0 else 0.0
    pooled_se = float(1.0 / math.sqrt(w.sum()))
    log(f"Cochran Q = {q:.3f} on {df} df, p = {p_q:.4f}, I^2 = {i2:.1%}")
    log(f"pooled slope {pooled:+.3f} +/- {pooled_se:.3f}")

    distinguishable = bool(p_perm < 0.05)
    agree = distinguishable == bool(p_q < 0.05)

    if not agree:
        # The two tests can disagree because they ask different questions. Q
        # asks whether the arm medians lie further apart than their own
        # sampling error allows. The permutation asks whether a family with no
        # arm structure reproduces the observed range, and it draws its null
        # from the POOLED per-seed slopes, whose spread is inflated by any real
        # arm differences. The permutation is therefore the conservative one.
        # A disagreement is reported rather than resolved, because resolving it
        # by preferring whichever test suits the outcome is the failure this
        # whole file exists to avoid.
        reading = (
            f"The two tests disagree. The permutation gives p = {p_perm:.4f} "
            f"and Cochran's Q gives p = {p_q:.4f}. Q compares the arm medians "
            f"against their own sampling error, while the permutation draws "
            f"its null from the pooled per-seed slopes and is inflated by any "
            f"real arm differences, so the permutation is the conservative "
            f"test and Q the sensitive one. No reading is asserted. What is "
            f"certain either way is that the registered flat band of "
            f"{FLAT_TOL} is passed by a truly flat family only "
            f"{band_rate:.1%} of the time, so the registered verdict carries "
            f"little information about the family."
        )
    elif distinguishable:
        reading = (
            "The arms are distinguishable on both tests, so the growth "
            "exponent does move the slope and the non-monotone ordering is a "
            "real feature rather than noise."
        )
    else:
        reading = (
            "The arms are not distinguishable on either test. Their spread is "
            "what a family with no dependence on the growth exponent produces "
            "at this seed count, so the registered verdict rests on a "
            "criterion a true positive would also have failed, and says "
            "nothing about whether the growth exponent is the lever."
        )
    log(reading)

    out = {
        "meta": {
            "status": "OUTSIDE THE REGISTRATION - licenses no claim; the "
            "registered verdict in r17c_gate.json stands regardless",
            "why": "outcome B was registered as a range on point estimates, "
            "max-min <= 0.15, which five arms with SE near 0.2 would fail "
            "most of the time even under a truly flat family",
            "gate_source": GATE,
            "permutations": PERMS,
            "flat_band": FLAT_TOL,
        },
        "growths": growths,
        "arm_medians": meds.tolist(),
        "bootstrap_ses": ses.tolist(),
        "observed_range": obs_range,
        "permutation": {
            "p_value": p_perm,
            "null_mean_range": exp_null,
            "flat_band_pass_rate_under_null": band_rate,
        },
        "cochran": {
            "Q": q,
            "df": df,
            "p_value": p_q,
            "I2": i2,
            "pooled_slope": pooled,
            "pooled_se": pooled_se,
        },
        "arms_distinguishable": distinguishable,
        "tests_agree": agree,
        "reading": reading,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R17C_HOMOGENEITY_DONE")


if __name__ == "__main__":
    main()
