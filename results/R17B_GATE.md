# Round 17b gate — the process is right and the estimator cannot resolve it

Measured 2026-08-07 on Atlas. Driver [`r17b_gate.py`](../harness/rc1/r17b_gate.py),
raw record [`r17b_gate.json`](r17b_gate.json), registered in
[`PREREG_ROUND17B.md`](PREREG_ROUND17B.md). Ladder n ∈ {12,500, 25,000,
50,000} at constant ρ = 4.0, dim 1024, 12 seeds per arm.

**P-17bM passes. P-17bO fails. The family is closed as registered.**
P-17bG never ran, being gated behind P-17bO.

## The measurement

| nominal α | measured α | slope (mean ± SEM) |
|---|---|---|
| 0.22 | +0.214 ✓ | +0.434 ± 0.224 |
| 0.30 | +0.295 ✓ | +0.456 ± 0.193 |
| 0.38 | +0.376 ✓ | +0.113 ± 0.285 |
| 0.46 | +0.462 ✓ | **−1.923 ± 1.677** |
| 0.55 | +0.548 ✓ | +0.441 ± 0.330 |

The preconditions held. Reference-rung level spread was 1.28% against the
frozen 78, and the worst sub-floor share was 12.9% against a 15% limit. The
capacity-limited process delivered its promised growth exponent everywhere,
within 0.02 of nominal at every setting, which is the cleanest mechanism
check the campaign has produced.

The registration predicted the 0.38 arm would win. It came in furthest from
target. The best arm was 0.30 at +0.456, which is inside the ±0.15 tolerance
of real corpora's +0.51, so what failed was monotonicity and not the target.

## Why the family is not what failed

A first reading blamed the estimator's denominator.
`attractiveness_skew` divides a recovered third moment by `Var(w)**1.5`, and
`Var(w)` goes to zero as counts approach Poisson, so the statistic diverges
where a family's hub signal weakens. Rising α weakens it. That reading was
measured and is **wrong**.

[`r17b_dispersion.json`](r17b_dispersion.json) reports the dispersion index
and recovered `Var(w)` per cell.

| α | n=12,500 | 25,000 | 50,000 |
|---|---|---|---|
| 0.22 | D=2.80, Var(w)=0.451 | 2.83, 0.458 | 3.12, 0.529 |
| 0.30 | 2.76, 0.440 | 2.79, 0.447 | 3.10, 0.525 |
| 0.38 | 2.66, 0.415 | 2.82, 0.456 | 3.11, 0.528 |
| 0.46 | 2.90, 0.474 | 2.79, 0.448 | 3.30, 0.574 |
| 0.55 | 2.73, 0.434 | 2.85, 0.464 | 3.29, 0.573 |

Every cell is readable. `Var(w)` runs nine to eleven times the registered
floor of 0.05, and the dispersion index sits near 3 against Poisson's 1. The
denominator never approached collapse in any arm.

The per-seed slopes say what actually happened.

| α | per-seed slopes, sorted |
|---|---|
| 0.22 | −1.4 −0.6 +0.1 +0.4 +0.4 +0.6 +0.7 +0.7 +1.0 +1.1 +1.2 +1.2 |
| 0.30 | −0.5 −0.5 −0.3 −0.1 +0.3 +0.6 +0.7 +0.7 +0.8 +1.1 +1.3 +1.4 |
| 0.38 | −1.6 −1.3 −1.3 −0.0 +0.3 +0.4 +0.4 +0.4 +0.7 +0.7 +1.1 +1.5 |
| 0.46 | **−19.1 −5.0 −4.5** +0.1 +0.3 +0.4 +0.4 +0.6 +0.7 +0.7 +1.2 +1.2 |
| 0.55 | −1.6 −0.8 −0.3 +0.1 +0.2 +0.3 +0.3 +0.6 +0.9 +1.2 +1.5 +2.9 |

The 0.46 arm's nine well-behaved seeds sit in the same band as every other
arm. Three seeds drag its mean to −1.923. The sweep is not a family
responding to its parameter, it is a handful of catastrophic seeds.

So the sensitivity is in the numerator rather than the denominator. `Var(w)`
is stable to three decimals across every arm and rises cleanly with n, while
the third moment depends on the extreme upper tail of the count distribution
and occasionally explodes on one draw. A statistic can be well behaved in
expectation and still be unusable at a practical seed count.

## What is not licensed

The per-arm medians are +0.65, +0.65, +0.40, +0.40, +0.45. That sequence is
nearly monotone and clustered around real's +0.51, so a median would convert
this failed prediction into a passing one.

**Switching to it now is not allowed.** The registration specifies mean ± SEM,
and choosing a location estimator after seeing which one rescues the result
is the analytic flexibility the whole registration discipline exists to
remove. The registered verdict stands and the family is closed.

The medians are recorded here because they are evidence about the estimator,
which is the thing to fix. They are not evidence about the family, because
this round cannot supply that.

## What this licenses instead

The campaign has now corrected its estimator twice. Round 17 replaced a
max-min range with a SEM after the range was found to grow with the seed
count. This round finds that the SEM of a mean is itself the wrong summary
when the per-seed distribution has heavy tails.

A follow-up needs three things declared before it runs, and none of them may
be chosen by looking at this data again.

1. **A robust location estimator**, declared in advance, with its breakdown
   point stated. A median or a trimmed mean is the obvious candidate.
2. **A seed count justified by a power calculation** rather than by
   convention. Twelve seeds cannot resolve a 0.5 effect against a per-seed
   spread of 2 to 4, which is knowable in advance from this round's spreads.
3. **A pre-registered outlier rule**, because a seed at −19.1 against a
   typical +0.5 is a diagnosable event and discarding it after the fact is
   not different from choosing the median after the fact.

The general precondition this adds to the plan is that **an estimator's
sampling behaviour must be characterised before its output is read**, not
only its regime of validity. This round checked the regime, found it healthy,
and was still defeated by sampling variance the check did not measure.

## Standing

The mechanism claim from [`R17_INTERVENTION.md`](R17_INTERVENTION.md), that
growing the cluster count moves the slope toward real, remains neither
confirmed nor refuted. Round 17 failed to vary the level cleanly. Round 17b
varied it cleanly and could not measure the outcome. The claim is now two
rounds old and still untested, which is itself the argument for fixing the
estimator before building a third family.
