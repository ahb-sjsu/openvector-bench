# Round 17b registration — emergent cluster growth at matched level

Registered 2026-08-07, before the run. Supersedes round 17, which is closed.
This is a new registration and not a retry, because the family is a different
process rather than the same process with different arguments.

## Why round 17 could not be repaired in place

Round 17 swept a power-law occupancy and its arms produced 13, 33, 90 and 338
clusters against the frozen family's 78. Every arm moved the cluster count's
level as well as its growth rate, so the sweep was never a one-parameter
sweep, and its slopes were correspondingly wild and non-monotone.

Two further parameterisations were tried before this registration and both
failed at design time, which is the cheap place to fail.

A Pitman-Yor process has two parameters and separates level from exponent in
principle, so it looked like the fix. It is not. Solving its concentration for
78 clusters at the reference rung peaked at about 20 clusters and was not even
monotone in the concentration. The reason is general and worth stating,
because it rules out a whole class of candidates. Any exchangeable process
whose cluster count grows as a power of n has a heavy-tailed occupancy, so
most of its clusters hold a handful of points. Three things this round needs
are then jointly unsatisfiable: a cluster count near 78, clusters larger than
the local subspace dimension of 94, and a count that grows without the
generator reading n. At the reference rung 78 clusters over 11,111 points
averages 141 against a floor of 94, which demands near-balanced clusters, and
heavy tails cannot supply them.

Folding the sub-floor tail into the survivors was tried as a repair and made
things worse. It turns the cluster count into a discontinuous and non-monotone
function of the family's parameters, which destroys the calibration that pins
the level.

## The family

Cluster membership follows a capacity-limited growth process. Each row joins a
uniformly chosen cluster unless that cluster has reached capacity `c * K**beta`,
where `K` is the number of clusters drawn so far, in which case the row starts
a new cluster. Cluster sizes are bounded by a common capacity rather than
spread over a power law, so the process is balanced by construction.

The count follows `n ~ c * K**(1+beta)`, so the growth exponent is
`alpha = 1/(1+beta)` and the capacity `c` sets the level without touching the
exponent. That is the separation the round needs.

Nothing in the process reads n. The row loop stops when the corpus is
exhausted, but every decision depends only on the state built so far, so a
prefix of the draw is the same process as the whole. This is what keeps
subsampling and direct generation equivalent, which is the constraint that
closed the intervention's own fix in `R17_INTERVENTION.md`.

`c` is a family constant, calibrated against the reference rung before the run
and recorded in [`r17b_calibration.json`](r17b_calibration.json). The
generator performs no calibration and reads no corpus size.

## Preconditions, checked before any outcome is read

The campaign plan's §4a requires that everything the family is supposed to
hold fixed is shown to have held, before a slope is looked at. Round 17 is the
reason that rule exists. These are computed from the cluster process alone and
need no corpus.

| nominal alpha | capacity | n=12,500 | 25,000 | 50,000 | measured alpha | points below floor |
|---|---|---|---|---|---|---|
| 0.22 | 3.973e-05 | 79 | 90 | 105 | +0.205 | 5.9% |
| 0.30 | 8.074e-03 | 78 | 96 | 119 | +0.305 | 7.5% |
| 0.38 | 1.926e-01 | 78 | 101 | 132 | +0.379 | 10.2% |
| 0.46 | 1.562e+00 | 78 | 108 | 149 | +0.467 | 10.5% |
| 0.55 | 8.548e+00 | 78 | 115 | 168 | +0.553 | 12.9% |

Reference-rung level spread is 1.28% against the frozen 78. Arms are matched
at the reference rung and diverge above it, which is the intended behaviour of
a growth sweep, so the level is checked there and not at the top.

The floor check is a share and not a minimum. A minimum cannot be met by any
growing process, because the youngest clusters have always just been spawned.
What made round 17 unreadable was arms whose clusters held 13 points on
average against a local dimension of 94, and degeneracy matters in proportion
to how many points experience it.

**Precondition gate.** Reference-rung levels within 10% of each other, and
points below the floor at most 15% in every cell. If either fails, no outcome
is read and the round is closed on the precondition.

## Predictions

**P-17bM, mechanism.** The cluster-growth exponent measured on the generated
corpora is within ±0.05 of nominal for every arm.

**P-17bO, outcome.** The hub-scaling slope falls monotonically as the growth
exponent rises, and at least one arm lands within ±0.15 of real corpora's
**+0.51**.

The bracket comes from the round-17 intervention, which measured +0.905 at a
fixed cluster count and +0.393 at a count growing as n^0.5. Linear in the
exponent that is `slope ~ 0.905 - 1.024 * alpha`, giving +0.51 at
**alpha ~ 0.385**. The registered prediction is therefore that the **0.38 arm
wins**. The fitted value will be reported as fitted.

**P-17bG, geometry.** If P-17bO passes, the winning arm must still pass the
RC-1 battery on the frozen point's other gates. A family that fixes hub
scaling by breaking the geometry it already had is not progress.

## Protocol

Ladder n ∈ {12,500, 25,000, 50,000} at constant ρ = 4.0, dim 1024, k = 10, 12
seeds per arm. The statistic is `attractiveness_skew`, which is the only
budget-invariant form measured in `spec/QUERY_BUDGET.md`. Slopes are per seed
and aggregated as mean ± SEM across seeds, following the correction recorded
in round 17 where a max-min range was used and grew with the seed count.

Failure of P-17bO closes the family. No second parameterisation inside this
round.

## Confirmation

If P-17bO and P-17bG both pass, the winning arm is re-measured on twelve
seed-disjoint seeds before anything is claimed. The campaign has twice had a
result move under a seed change.
