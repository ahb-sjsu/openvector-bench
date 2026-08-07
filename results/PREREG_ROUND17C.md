# Round 17c registration — the same family, powered

Registered 2026-08-07, before the run.

This is not a new family. Round 17b established that the capacity-limited
growth process is mechanically sound, delivering its promised exponent within
0.02 of nominal at every setting with the level held to 1.28% at the reference
rung. What it could not do was measure the outcome, because at 12 seeds the
best worst-case power available to any estimator was 0.72
([`spec/ESTIMATOR.md`](../spec/ESTIMATOR.md)).

Round 17c is that same family re-run under the registered estimator rule. The
family, the calibration constants, the ladder and the arms are unchanged.

## What changes

**Estimator.** Per-seed slopes are summarised by the **median**, with the
bootstrap standard error of the median over 2,000 resamples. No outlier is
discarded, because the estimator absorbs contamination by construction.

**Seeds.** 32 seeds per arm, meeting the registered floor for a gate-carrying
arm. They are **100 to 131, disjoint from round 17b's 0 to 11.** This matters:
round 17b's medians were seen before the estimator was chosen, so no result
may rest on those draws.

Nothing else changes. The calibration in
[`r17b_calibration.json`](r17b_calibration.json) is reused unmodified.

## Preconditions

Unchanged from round 17b and rechecked before any outcome is read.
Reference-rung levels within 10% of each other, and at most 15% of points
below the floor in every cell. Round 17b passed both at 1.28% and 12.9%.

## Predictions

**P-17cM, mechanism.** The measured cluster-growth exponent is within ±0.05
of nominal for every arm. Round 17b passed this at every setting.

**P-17cO, outcome.** Three outcomes are registered, because after round 17b
more than one is live and only naming them in advance keeps the reading
honest.

**P-17cO-A, the intervention's mechanism.** The slope falls monotonically as
the growth exponent rises, and crosses real corpora's +0.51 near α ≈ 0.385.
This is the prediction carried over from
[`R17_INTERVENTION.md`](R17_INTERVENTION.md), which measured +0.905 at a fixed
cluster count and +0.393 at a count growing as n^0.5. Passing confirms that
cluster-count growth is the operative variable.

**P-17cO-B, flat and on target.** The slope is roughly constant across α and
every arm sits within ±0.15 of +0.51. This would mean the family reaches real
corpora's hub scaling but that the **growth exponent is not the lever**. The
capacity process changes two things at once relative to the frozen family: it
grows the cluster count, and it bounds cluster sizes to a common capacity
instead of letting a multinomial spread them. Under B the second is doing the
work, and the finding is that **size regularity, not count growth, sets hub
scaling**. That would refine the intervention rather than refute it, and it
earns a follow-up isolating regularity at a fixed count.

**P-17cO-C, neither.** No monotone decline and no consistent agreement with
target. The family is closed.

I record that round 17b's already-seen medians were +0.65, +0.65, +0.40,
+0.40, +0.45, which lean toward B over A. Stating that in advance is the
honest handling of information I cannot un-see. It is a prior, not evidence,
and this round decides on disjoint seeds.

**P-17cG, geometry.** If A or B passes, the winning configuration must still
pass the RC-1 battery on the frozen point's other gates.

## Protocol

Ladder n ∈ {12,500, 25,000, 50,000} at constant ρ = 4.0, dim 1024, k = 10,
arms α ∈ {0.22, 0.30, 0.38, 0.46, 0.55}. The statistic is
`attractiveness_skew`, the only budget-invariant form measured in
[`spec/QUERY_BUDGET.md`](../spec/QUERY_BUDGET.md).

Under A or B, the winning configuration is re-measured on a further
seed-disjoint block before anything is claimed.
