# Round 17c gate — closed as registered, on a criterion that could not pass

Measured 2026-08-07 on Atlas. Driver [`r17c_gate.py`](../harness/rc1/r17c_gate.py),
raw record [`r17c_gate.json`](r17c_gate.json), registered in
[`PREREG_ROUND17C.md`](PREREG_ROUND17C.md). Ladder n ∈ {12,500, 25,000,
50,000} at ρ = 4.0, dim 1024, **32 seeds** per arm, seeds 100 to 131, disjoint
from round 17b's. Statistic summarised by the median with a bootstrap standard
error, per [`spec/ESTIMATOR.md`](../spec/ESTIMATOR.md).

**P-17cM passes. P-17cO returns outcome C. The family is closed as
registered.**

## The measurement

| nominal α | measured α | slope (median ± bootstrap SE) |
|---|---|---|
| 0.22 | +0.213 ✓ | +0.667 ± 0.144 |
| 0.30 | +0.295 ✓ | +0.433 ± 0.227 |
| 0.38 | +0.379 ✓ | +0.750 ± 0.223 |
| 0.46 | +0.462 ✓ | +0.305 ± 0.138 |
| 0.55 | +0.554 ✓ | +0.518 ± 0.104 |

Preconditions held exactly as in round 17b, at 1.28% reference-rung level
spread and 12.9% worst sub-floor share. The process delivered its promised
growth exponent within 0.02 at every setting for the third round running.

The registered decision was not monotone, spread 0.445, and not every arm on
target, so outcome C.

## The estimator change worked

Round 17b measured the α = 0.46 arm at **−1.923 ± 1.677** and was destroyed by
it. The same arm here is **+0.305 ± 0.138**, the second tightest in the sweep.
Same family, same parameter, different estimator and seed count.

That is direct confirmation that round 17b's failure was instrumentation
rather than the family, which is what [`spec/ESTIMATOR.md`](../spec/ESTIMATOR.md)
predicted from synthetic data before this round was run.

## The registered criterion could not have passed

Outcome B, the flat outcome, was registered as a range on point estimates,
`max − min ≤ 0.15`. The supplementary analysis in
[`r17c_homogeneity.json`](r17c_homogeneity.json) measures what that criterion
does under its own null.

**A genuinely flat family clears the 0.15 band 1.7% of the time.**

So outcome C was very nearly predetermined. A verdict from a test that a true
positive fails 98.3% of the time carries almost no information about the
family. The criterion tested dispersion of estimates when what outcome B
claims is that the arms are indistinguishable, and those are not the same
thing when each arm carries a standard error near 0.2.

This is the third consecutive round defeated by its own instrument. Round 17
by a confound, 17b by power, 17c by a mis-specified decision rule. The
registrations have been careful about the outcome and careless about the rule
that reads it.

## What the arms actually say

**Outside the registration. This licenses no claim.** It is recorded because
the registered verdict is uninformative and something must be said about why.

Both homogeneity tests agree that the arms are not distinguishable.

| test | result |
|---|---|
| permutation on the registered range statistic | p = 0.254, null mean range 0.368 |
| Cochran's Q | Q = 4.68 on 4 df, p = 0.322, I² = 14.5% |
| **pooled slope** | **+0.514 ± 0.065** |

Real corpora sit at **+0.51**. The pooled estimate is **0.06 standard errors
away**.

Read plainly, the family's hub scaling lands on real corpora's value and does
not depend on the growth exponent anywhere in the range 0.22 to 0.55. The
frozen family it was built from sits at +0.905, so something in the capacity
process moved it, and that something is not cluster-count growth.

The remaining candidate is the process's other change. The frozen family
allocates cluster sizes by a multinomial, which spreads them, while the
capacity process bounds every cluster to a common capacity, which regularises
them. **Cluster size regularity, not cluster count growth, is the surviving
hypothesis.**

That reverses the direction the round-17 intervention pointed. The
intervention was not wrong about its own arms, since it varied count growth
and the slope moved. But it varied count growth by scaling `log2_clusters`
directly, which also changes how sizes are distributed at any fixed n, so it
never isolated the two. This round holds the count-growth exponent across a
wide range and sees nothing, which is evidence the count was the passenger.

## What is not claimed

The pooled value has now been seen. It cannot be used as confirmation of
anything, and no admission follows from it. It is a hypothesis with a number
attached.

Three things are required before any claim, and they belong to a new
registration.

1. **An isolating intervention.** Two arms at matched cluster count and
   matched everything else, differing only in whether sizes are multinomial or
   capacity-bounded. If regularity is the lever, the arms separate. This is a
   cleaner experiment than anything in rounds 17 through 17c because it varies
   one thing the frozen family already has a value for.
2. **A decision rule that a true positive can pass**, stated as
   indistinguishability with a declared test rather than as a range on point
   estimates, with its power computed before the run.
3. **Fresh seeds**, disjoint from 100 to 131.

## Standing

The round-17 intervention's mechanism claim, that growing the cluster count
moves the slope toward real, is now **contradicted** on this family across a
wide exponent range, though not refuted as a statement about its own arms.

The frozen family's excess hub scaling has a candidate explanation for the
first time that is both admissible and quantitative. It is untested.
