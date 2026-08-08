# Round 20 registration — does one parameter satisfy two gates?

Registered 2026-08-08, before the run.

## The claim being tested

Two independent gate failures have pointed at the same knob, which has not
happened before in this campaign.

[`R19_LOCALDIM_FIT.md`](R19_LOCALDIM_FIT.md) found the family's intrinsic
dimension is flat where real's falls, and that no `local_dim` fixes it.
[`R19B_G1_FLOOR.md`](R19B_G1_FLOOR.md) then found what does move G1: cluster
count, as **G1 ≈ 253 · k^−0.368**. Extrapolating to real's corrected targets
needs about 454, 695, 1001 and 1238 clusters across the ladder, an implied
growth exponent of **0.482**.

[`R17C_GATE.md`](R17C_GATE.md) swept the growth exponent from 0.22 to 0.55 and
found hub scaling statistically indistinguishable throughout, pooling to
+0.514 ± 0.065 against real's +0.51. **0.482 lies inside that range.**

So the claim is that cluster count growing as roughly n^0.48, at a level near
450 at n = 25,000, satisfies **both** gates at once.

## The family

The capacity-limited process of round 17b, unchanged in form. Growth exponent
fixed at **0.48**. Three cluster levels are swept because the extrapolation
that produced 450 runs past its measured range, which topped out at 256
clusters, and a point prediction from an extrapolation would be overconfident.

`local_dim` is set to **24**, the measured minimum of the U in
[`R19B_G1_FLOOR.md`](R19B_G1_FLOOR.md), chosen by the rule "the value
minimising G1" rather than by inspection of any outcome.

Capacity constants calibrated before the run:

| nominal level | capacity | achieved levels (25k / 50k / 100k / 200k) | exponent | mean size at 25k |
|---|---|---|---|---|
| 300 | 0.2859 | 301, 417, 588, 825 | +0.486 | 74 |
| **450** | **0.1201** | **450, 633, 885, 1243** | **+0.488** | **49** |
| 650 | 0.05499 | 649, 917, 1290, 1810 | +0.493 | 34 |

The 450 level reproduces the required counts closely, 450/633/885/1243 against
454/695/1001/1238.

## Preconditions, checked before any outcome

Achieved levels within 10% of nominal at the reference rung, growth exponent
within 0.05 of 0.48, and at most 15% of points in clusters smaller than
`local_dim`. The last matters more here than in round 17b: at level 650 the
mean cluster holds 34 points against a `local_dim` of 24, which is the closest
this campaign has come to the degeneracy that made round 17 unreadable.

## Predictions

**P-20G, intrinsic dimension.** For at least one level, the G1 ratio against
real's corrected targets lies inside [0.85, 1.15] at **all four** rungs.
Targets are 26.64, 22.78, 19.92, 18.42. Measured at 10,000 queries per rung,
matching real's budget exactly, which is the defect that invalidated
[`R17G_BATTERY.md`](R17G_BATTERY.md).

**P-20H, hub scaling.** At that **same** level, the slope is within ±0.15 of
+0.51, measured on round 17c's protocol: ladder 12,500 / 25,000 / 50,000 at
ρ = 4.0, `attractiveness_skew`, median of per-seed slopes with a bootstrap
standard error, 32 seeds.

**P-20C, the convergence.** P-20G and P-20H hold at the same level.

This is the point of the design. Both predictions descend from one parameter,
so **a level that passes one and fails the other refutes the convergence
rather than half-confirming it.** If G1 passes at 650 while hub scaling passes
at 300, the two gates want different families and the claim is dead even
though each gate was individually satisfied.

## Protocol

Dim 1024, k = 10. Seeds **300 to 331**, disjoint from rounds 17b (0–11), 17c
(100–131) and 18 (200–231). G1 uses 3 seeds per cell, since
[`R19B_G1_FLOOR.md`](R19B_G1_FLOOR.md) showed it varies little across seeds,
and the expensive rungs run to n = 200,000. Hub scaling uses the registered 32.

## What each outcome licenses

**P-20C passes.** The family reaches real corpora on two of the three
mandatory gates from a single mechanism. That earns a full battery run on both
batteries, not another diagnostic.

**P-20G and P-20H pass at different levels.** The convergence is refuted. The
gates are governed by cluster count in incompatible ways and the family needs
a second independent parameter, which is a different and worse position than
this round assumes.

**Neither passes anywhere.** The G1 extrapolation was wrong outside its
measured range, and the honest conclusion is that this family has been pursued
far enough.
