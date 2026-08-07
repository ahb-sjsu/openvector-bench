# Campaign stage 0 — the round-8 family is close, and wrong in the same way

Measured 2026-08-07 on NRP. Driver
[`r17_stage0.py`](../harness/rc1/r17_stage0.py), raw record
[`r17_stage0.json`](r17_stage0.json). Ladder n ∈ {12,500, 25,000, 50,000} at
constant ρ = 4.0, dim 1024, **20 seeds**, k = 10. Nothing fitted. The corpus
parameters are the frozen round-8 point, unchanged.

## Result

| quantity | value |
|---|---|
| slope | **+0.904** per decade |
| standard error of the mean | 0.111 |
| 95% confidence interval | [+0.687, +1.121] |
| distance from real (+0.51) | 0.394, **3.6 SEM** |
| distance from codebook reference (+2.9) | 1.996, **18.0 SEM** |
| tail shape, all 60 cells | **power law** |

The measurement is conclusive by the registered criterion and lands in the
plan's third case, which instructs deciding with data rather than by the
plan.

## Two findings, and they point the same way

**The round-8 family is not in the codebook regime.** At 18 standard errors
from the codebook reference it is a categorically different construction.
Rounds 15 and 16 were built to escape a regime this family was never in. The
corpus/query split does most of the work, which is consistent with round 13's
measurement that hubness is almost entirely a query property.

**It is nevertheless wrong, and wrong in exactly the way rounds 15 and 16
were.** It scales at 1.8 times real's rate, significantly above it at 3.6
SEM, and the tail-shape diagnostic favours a **power law in all sixty
cells**. A power-law tail is a scale-invariant shape, and round 16
established that a scale-invariant shape sampled more deeply necessarily
concentrates faster than real does. The family is milder than the codebooks
by a factor of three but shares their defect.

The tail-shape diagnostic earned its registration immediately. Without it
the result would be a slope 1.8 times too large with no account of why, and
with it the cause is the same one already isolated.

## Consequence for the plan

The plan proposed three new families whose attractiveness saturates. The
measurement suggests something cheaper and better founded.

**The round-8 family already has everything except the saturation.** It holds
six gates in band with real anatomy on three fresh seeds, it carries a
genuine query model, and it scales in the right regime. Its only measured
defect on this axis is that its cluster-choice law is Zipf, which is
scale-invariant by construction.

**So the first move is to replace that one law rather than build three new
families.** Sublinear preferential attachment over cluster choice, at
exponent β < 1, is a one-parameter change to a family that already works.
Everything else stays frozen, which means the geometry gates and the anatomy
guard are inherited rather than re-earned, and P-14C's freeze baseline
already records what they must not move by.

Rounds 18 and 19 are held. They construct attractiveness from scratch, which
is only worth doing if modifying the best existing family fails.

## Instrument note, and it generalises

An earlier attempt at this measurement widened the ladder to n = 6,250 to buy
lever arm. It made the estimate worse. The coefficient of variation of
`attractiveness_skew` across seeds is

| n | CV |
|---|---|
| 6,250 | 0.356 |
| 12,500 | 0.111 |
| 25,000 | 0.074 |
| 50,000 | 0.073 |

The estimator destabilises below about n = 12,500 at ρ = 4, because the
deconvolution's third moment has too few points to stand on. Lever arm
bought through a cell five times noisier is a loss, and precision should be
bought with seeds, where cost is linear and the gain is one over root n.

The registered RC-1 ladder starts at 25,000 and is unaffected. Anything
below it is not.

## Method note

The conclusiveness criterion was changed mid-measurement, from the max-min
range of per-seed slopes to the standard error of the mean. Range grows with
the number of seeds, so adding seeds to improve a measurement would have
made it look worse. The change was checked against the run that motivated it
before being adopted, where it left the verdict unchanged, so it altered only
whether a run may claim anything rather than what it claims.
