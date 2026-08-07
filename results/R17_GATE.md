# Round 17 gate — the mechanism is right and the experiment was confounded

Measured 2026-08-07 on NRP. Driver [`r17_gate.py`](../harness/rc1/r17_gate.py),
raw record [`r17_gate.json`](r17_gate.json). Ladder n ∈ {12,500, 25,000,
50,000} at constant ρ = 4.0, dim 1024, 12 seeds per arm.

**P-17M passes. P-17O fails. The family is closed under this registration.**
P-17G never ran, being gated behind P-17O.

## The measurement

| `cluster_growth` | measured growth exponent | slope |
|---|---|---|
| 0.25 | 0.245 ✓ | +9.195 ± 2.505 |
| 0.35 | 0.381 ✓ | +12.044 ± 4.887 |
| 0.45 | 0.448 ✓ | −7.233 ± 5.202 |
| 0.60 | 0.631 ✓ | +2.116 ± 1.391 |

The mechanism check passes cleanly at every value. The outcome is not merely
off target, it is wild and non-monotone with standard errors of 2.5 to 5.2.
That pattern is not a family missing a target. It is a broken experiment.

## What went wrong

The frozen round-8 family has **78 clusters**. The arms produced:

| `cluster_growth` | n=12,500 | 25,000 | 50,000 |
|---|---|---|---|
| 0.25 | 13 | 14 | 18 |
| 0.35 | 33 | 40 | 52 |
| 0.45 | 90 | 111 | 148 |
| 0.60 | 338 | 533 | 816 |

**Every arm changed the cluster count's level as well as its growth rate.**
The sweep was never a one-parameter sweep. At `cluster_growth` = 0.25 the
family has a sixth of the frozen family's clusters and each holds roughly
2,000 points, which is extreme densification and drives the slope to +9. At
0.60 it has ten times as many, each holding as few as 13 points against a
local subspace dimension of 94, so the local geometry is degenerate and the
measurement is noise. The two effects move in opposite directions and meet in
the middle, which is why the sweep is non-monotone.

The intervention that motivated this round did not have this defect. Its
GROWING arm scaled `log2_clusters` directly and was **matched to the frozen
value at the bottom rung**, so it varied the growth rate alone. That is why
it produced a clean +0.393 ± 0.102 where this sweep produces chaos.

## What this does and does not license

**It does not refute the mechanism.** The intervention's result stands: at
matched level, growing the cluster count moves the slope onto real's value.
This gate did not test that claim, because its arms never held the level.

**It does close the family as registered.** P-17O failed, and the
registration says failure closes the family with no second parameterisation
inside the round. Two defects are now known and both are design rather than
mechanism:

1. **Level and growth are confounded.** The family needs a separate level
   parameter, calibrated so occupancy matches the frozen 78 at a reference n,
   with `cluster_growth` controlling only the rate of change from there.
2. **Cluster size can fall below the local dimension.** With `d_local` ≈ 94,
   any arm whose clusters hold fewer than about 100 points has degenerate
   local geometry. A corrected family needs a floor tying minimum cluster
   size to `d_local`, and the gate needs a precondition rejecting any arm
   that violates it before its slope is read.

A corrected family is a new registration, not a retry. Its predictions should
include the level as an explicit check, since that is the term this round
failed to control.

## The pattern this is the third instance of

The mechanism check passed and the outcome failed, for the third time today.
Round 16 grew its atom count correctly and did not move the slope. Round 17's
intervention identified the right variable and this gate then failed to vary
it cleanly. In each case the knob did exactly what it claimed.

The lesson is that verifying a knob is necessary and nowhere near sufficient,
because a family can vary something else that was never parameterised at all.
The corrected discipline is to check, before reading any outcome, that
everything the family is supposed to hold fixed actually held. Here that
would have been one table of cluster counts, computable in seconds and
without a cluster run, and it would have caught this before the gate was
submitted.
