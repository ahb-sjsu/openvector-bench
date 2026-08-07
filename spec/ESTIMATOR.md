# Normative — the location estimator and seed count for per-seed slopes

Adopted 2026-08-07 after round 17b. Study
[`estimator_study.py`](../harness/rc1/estimator_study.py), record
[`estimator_study.json`](../results/estimator_study.json).

This is the campaign's second estimator correction. Round 17 replaced a
max-min range with a SEM after the range was found to grow with the seed
count. Round 17b found that the mean itself is the wrong summary when the
per-seed distribution has heavy tails.

## The rule

**Per-seed slopes are summarised by the median.** Uncertainty is reported as
the bootstrap standard error of the median, not the standard error of a mean.

**Gate-carrying arms use at least 32 seeds.** Fewer than 32 is reportable but
cannot carry a gate.

**No outlier is discarded.** The estimator absorbs contamination by
construction, so there is no rule to apply and no discretion to exercise.

## How it was chosen, and the contamination in choosing it

Round 17b's medians had **already been seen** when this study was written, and
they happen to rescue that round's verdict. A choice made by trying estimators
on r17b's arms would therefore have been circular, and saying otherwise would
have been false.

So the choice was made on synthetic data with known ground truth. Per-seed
slopes were drawn from a contaminated normal, `(1-eps) N(mu, 0.7) + eps
N(-8, 6)`, with the clean spread and the contaminant both calibrated from
round 17b's observed per-seed **spreads** rather than from its outcomes. Using
pilot variance to size an experiment is what pilot variance is for. The
decision rule was fixed before the run: highest worst-case power across
contamination rates, tie-broken by breakdown point.

The median won under that rule. It is the same estimator that would rescue
round 17b, and that coincidence is stated rather than buried. The protection
against it is procedural. **Any round adopting this rule runs on seeds
disjoint from round 17b's**, so no result rests on data whose answer was
already visible.

## What the study found

Power to correctly order two families differing by 0.5, at 20,000 trials.

| contamination | seeds | mean | median | trimmed 20% | Huber |
|---|---|---|---|---|---|
| 0.00 | 12 | **0.81** | 0.77 | 0.80 | 0.80 |
| 0.00 | 64 | **0.98** | 0.95 | 0.97 | 0.98 |
| 0.04 | 12 | 0.66 | 0.75 | 0.78 | **0.78** |
| 0.04 | 64 | 0.74 | 0.94 | 0.96 | **0.97** |
| 0.08 | 12 | 0.60 | 0.75 | 0.75 | **0.76** |
| 0.08 | 64 | 0.66 | 0.95 | **0.95** | 0.95 |
| 0.17 | 12 | 0.56 | **0.72** | 0.66 | 0.70 |
| 0.17 | 64 | 0.59 | **0.90** | 0.87 | 0.89 |

Worst-case power for the median by seed count: 0.72 at 12, 0.77 at 20, 0.83 at
32, 0.87 at 48, 0.90 at 64. Thirty-two is the smallest grid point clearing
0.80.

Two results matter more than the ranking.

**The mean does not converge under contamination.** At a 4 percent
contamination rate its power moves from 0.66 to 0.74 as seeds go from 12 to
64, while every robust estimator moves from about 0.78 to about 0.97. Adding
seeds does not repair a mean here. That is why round 17b's α = 0.46 arm could
not have been fixed by running longer.

**Round 17b was underpowered for every estimator.** At 12 seeds the best
worst-case power available was 0.72. The round could not have resolved its
effect no matter which summary it used, so its failure is a design failure and
not evidence about the family.

The median costs about four points of power against the mean on clean data,
which is the ordinary efficiency price of robustness and is accepted.

## The general precondition this adds

Round 17b checked that its estimator was in a valid regime, found it healthy
in every cell, and was still defeated. Validity is not sufficiency.

**An estimator's sampling behaviour must be characterised before its output is
read, not only its regime of validity.** For a gate this means stating, before
the run, the seed count at which the design has 80 percent power against the
effect it claims to detect, given a spread that has been measured rather than
assumed.
