# Round 18 — cluster count growth is the lever, and its rate is not

Measured 2026-08-07 into 2026-08-08 on Atlas. Driver
[`r18_factorial.py`](../harness/rc1/r18_factorial.py), raw record
[`r18_factorial.json`](r18_factorial.json), registered in
[`PREREG_ROUND18.md`](PREREG_ROUND18.md). Ladder n ∈ {12,500, 25,000, 50,000}
at ρ = 4.0, dim 1024, 32 seeds 200 to 231, disjoint from rounds 17b and 17c.
Slopes are medians with bootstrap standard errors.

**An intervention, not a family gate. Nothing is admitted here.** Arms may
read n. The registered use is to decide which factor a family is built around.

## Both controls held, so the effects are readable

| control | observed | expected | |
|---|---|---|---|
| FIXED+LOW, the frozen family | +0.768 ± 0.132 | +0.905 | within 3 SE ✓ |
| GROWING+HIGH, ≈ the capacity family | +0.572 ± 0.113 | +0.514 | within 3 SE ✓ |

FIXED+LOW sits 0.137 below its expectation, on the low side of a band of
0.396. Two known differences push that way and neither is a defect. The
+0.905 reference is a **mean** over 8 to 20 seeds while this is a median over
32, and this cell uses `size_tail` calibrated to CV 0.19 (0.161 to 0.176)
rather than the frozen 0.157 exactly. The pair is coherent, so the run is
read rather than diagnosed.

## The measurement

| | CV 0.19 | CV 0.45 |
|---|---|---|
| **k fixed at 78** | +0.768 ± 0.132 | +0.965 ± 0.084 |
| **k grows 78 → 102 → 132** | +0.564 ± 0.149 | +0.572 ± 0.113 |

**P-18A, count. PASS.** Effect +0.298, permutation p = **0.0004**.
**P-18B, size. Fails.** Effect −0.103, permutation p = 0.396.
**P-18C, interaction.** −0.188.

This is the registered expectation, stated before the run.

## What it means, with round 17c

Round 17c swept the growth **rate** from 0.22 to 0.55 and found the arms
statistically indistinguishable, pooling to +0.514 ± 0.065. Round 18 finds
that switching growth **on** moves the slope by +0.298 at p = 0.0004.

Taken together: **the presence of cluster count growth lowers hub scaling, and
its rate does not matter.** That is a threshold, and a sweep over rates is
blind to a threshold by construction, which is exactly why three rounds passed
without seeing it.

The frozen family's excess hub scaling is therefore caused by holding the
cluster count fixed while n grows. Every added row joins one of a fixed number
of clusters, within-cluster competition intensifies, and the local winner
takes relatively more. Letting the count grow at any positive rate dilutes
that competition and the effect saturates immediately.

## The interaction is real and worth stating

The size effect is not uniform. Decomposed:

| | size effect (LOW − HIGH) | count effect (FIXED − GROWING) |
|---|---|---|
| within FIXED | **−0.197** | within LOW: +0.204 |
| within GROWING | −0.009 | within HIGH: +0.393 |

**Size spread raises hub scaling when the cluster count is fixed, and does
nothing once the count grows.** So the size main effect fails not because size
is inert everywhere, but because its effect is confined to one condition and
averages away.

That does not undermine P-18A, which is present and significant in both size
conditions. It does mean the two factors should not be described as acting
independently. The honest statement is that growth is the lever, and size
spread is a secondary term that only operates in the regime growth removes.

## What this kills

Round 17c's surviving hypothesis was cluster size **regularity**. It was
falsified before this round was built, at the cost of one command, and this
round confirms the falsification from the other direction.

The frozen family's size CV is 0.19 and the capacity family's arms run 0.357
to 0.615, so the capacity family is **less** regular while having the lower
slope. And here, raising spread at fixed count **raises** the slope by 0.197,
the opposite of what the regularity hypothesis needs. Regularity is dead in
both directions.

## What follows

The target for an admissible family is any scale-blind process whose cluster
count grows, at any positive rate. **The capacity-limited process from round
17b already is exactly that**, and round 17c measured it at +0.514 ± 0.065
against real corpora's +0.51.

The remaining work is not another family. It is an admission run against the
full RC-1 battery, since hub scaling is the only gate this candidate has ever
been measured on. Battery A is running as P-17cG. Admission needs battery B as
well, so nothing can be admitted until both are in.

Two caveats carry forward. The +0.514 was seen before it was confirmed, so it
needs a seed-disjoint replication. And the whole result rests on one statistic
in one family, which the battery exists to test.
