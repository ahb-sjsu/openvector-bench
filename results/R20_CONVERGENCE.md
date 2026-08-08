# Round 20 — the convergence is refuted, and the family is closed

Measured 2026-08-08 on Atlas. Driver
[`r20_convergence.py`](../harness/rc1/r20_convergence.py), record
[`r20_convergence.json`](r20_convergence.json), registered in
[`PREREG_ROUND20.md`](PREREG_ROUND20.md). Growth exponent fixed at 0.48,
`local_dim` 24, cluster levels 300, 450 and 650, seeds 300 to 331.

**P-20G fails at every level. P-20H fails at every level. P-20C, the
convergence, is refuted.**

Preconditions held everywhere. Achieved levels 301, 450 and 649 at the
reference rung, growth exponents +0.486 to +0.493 against a nominal 0.48, and
sub-floor shares of 2.6, 5.1 and 10.7 percent.

## Intrinsic dimension

| level | ratio at 25k / 50k / 100k / 200k | G1 in absolute terms |
|---|---|---|
| 300 | 1.19 1.46 1.73 1.93 | 31.6 33.3 34.4 35.5 |
| 450 | 1.12 1.39 1.64 1.87 | 29.8 31.6 32.7 34.5 |
| 650 | 1.07 1.33 1.58 1.79 | 28.6 30.4 31.4 32.9 |

Real is 26.64, 22.78, 19.92, 18.42, falling by a third across the ladder.

Every level produces a G1 that **rises** with n. Adding clusters lowers the
whole curve and does not bend it, which is the same result
[`R19_LOCALDIM_FIT.md`](R19_LOCALDIM_FIT.md) found for `local_dim` and for the
same reason. Both are level parameters.

## The extrapolation that motivated this round was wrong

[`R19B_G1_FLOOR.md`](R19B_G1_FLOOR.md) fitted G1 against cluster count as
`k^−0.368` over a range from 1 to 256 clusters, and extrapolated to the 454
clusters that would put G1 on target. Fitting the same relationship inside
this round's range, across levels 300, 450 and 650 at the reference rung,
gives an exponent near **−0.14**. The power law has largely saturated by 300
clusters.

Carrying the weaker exponent through the trend requirement pushes the needed
growth rate from about 1.1 to roughly **3**, meaning a cluster count growing
as the cube of corpus size. That is not a parameter setting, it is an
impossibility.

R19b flagged the extrapolation as running past its measured range and I built
a round on it anyway. The caveat was correct and recording it was not the same
as acting on it.

## Hub scaling, and what can be read from it

| level | slope | bootstrap SE | per-seed range |
|---|---|---|---|
| 300 | −1.169 | 0.346 | −11.5 to +3.1 |
| 450 | −3.481 | 1.097 | −29.0 to +34.9 |
| 650 | +2.371 | 1.375 | −9.0 to +36.1 |

**Only the first row is interpretable.** At level 300 the median is estimated
tightly enough to trust, and it says hub scaling is −1.17 against a target of
+0.51. At 450 and 650 the bootstrap standard errors are 1.1 and 1.4, with
per-seed slopes spanning sixty units, so those medians are estimator noise and
no reading should rest on them.

What the readable row supports is that **hub scaling depends on the cluster
level**, and depends on it strongly. Round 17c swept the growth exponent from
0.22 to 0.55 at a level near 78 and found the arms indistinguishable, pooling
to +0.514. Holding the exponent and raising the level to 300 moves the slope
to −1.17.

So round 17c's finding was true and incomplete. Hub scaling is flat in the
growth exponent at a fixed level, and the level was carrying the effect all
along. Round 18 is consistent with this rather than contradicted, since its
GROWING arm reached 132 clusters at the top rung against FIXED's 78, which is
a short span of the same relationship.

## The estimator has a bounded domain, which is a third distinct failure

`attractiveness_skew` deconvolves a Poisson observation and divides by the
recovered variance to the power of three halves. At high cluster counts each
cluster holds few points, hub structure thins, and that variance falls toward
zero. The standard errors rising from 0.35 to 1.4 as the level goes from 300
to 650 is the expected signature.

This is the third distinct way the campaign's instrumentation has defeated a
round. Round 17b lacked power, round 17c had a decision rule a true positive
could not pass, and round 20 runs the estimator outside its usable domain. The
missing precondition is a **domain check**, establishing before a run that the
estimator is usable across the whole parameter range the round will sweep, not
only at its starting point. The dispersion diagnostic written for round 17b
would answer it cheaply.

## What is closed

The round-8 family and everything derived from it, including the
capacity-limited variant, fails both mandatory gates that this campaign can
currently measure, and fails them for structural reasons rather than
mis-set parameters.

Intrinsic dimension is flat where real's falls, and no level parameter bends a
trend. Hub scaling can be put on target only in a narrow band of cluster
counts near 78 to 168, which is far below what intrinsic dimension needs even
before the trend problem is considered. **The two gates want opposite cluster
counts.**

Round 18's finding survives as a statement about that family, that cluster
count growth lowers hub scaling. Round 17c's +0.514 survives as a measurement
at its own cluster level. Neither is a route to admission.

The recommendation is to stop here rather than register a round 21. Three
rounds have now been spent on a lineage whose intrinsic dimension cannot be
made to fall, and the useful output of all of them is instrument work rather
than a family.
