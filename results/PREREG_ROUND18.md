# Round 18 registration — which factor moves hub scaling

Registered 2026-08-07, before the run. Replaces the held "competition
geometry" round 18.

**This is an intervention, not a family gate.** Its arms may read n, and no
admissible generator follows from it directly. Its registered use is to decide
which factor a later family should be built around. Round 17's intervention
had the same status and the same licence.

## Why a factorial and not the two-arm test first proposed

Round 17c left one surviving hypothesis, that cluster size **regularity**
rather than count growth sets hub scaling, since the frozen family allocates
sizes by a Zipf law and the capacity process bounds them. That hypothesis was
checked before it was built on, and it is **wrong in the direction proposed**.

The frozen family's size coefficient of variation is 0.19. The capacity
family's arms run 0.357 to 0.615, so the capacity family is **less** regular,
not more, while having the lower slope. Worse for the hypothesis, across round
17c's arms the size CV nearly doubled from 0.357 to 0.615 while the slope
stayed flat and homogeneous. **Neither the growth exponent nor the size
dispersion moved the slope inside that family.**

That leaves a factor round 17c could not see. Every one of its arms **grew**,
from 78 clusters to between 105 and 168, while the frozen family is pinned at
78 for all n. The difference between +0.905 and +0.514 may therefore be the
*presence* of growth rather than its rate, which is a threshold that a sweep
over rates is blind to by construction.

Two candidates remain and they must be separated rather than tested in turn.

## Design

A 2 × 2 factorial. Every cell uses the existing generator path, so nothing new
is built and nothing untested is introduced.

| factor | levels |
|---|---|
| **COUNT** | FIXED, k = 78 at every n · GROWING, k = 78 → 102 → 132 |
| **SIZES** | LOW, size CV = 0.19 · HIGH, size CV = 0.45 |

`size_tail` is calibrated per cell and per rung so the achieved CV hits its
target exactly. The calibrated values are below and are fixed before the run.

| cell | n=12,500 | 25,000 | 50,000 |
|---|---|---|---|
| FIXED+LOW | k=78, st=0.161 | k=78, st=0.172 | k=78, st=0.176 |
| FIXED+HIGH | k=78, st=0.356 | k=78, st=0.366 | k=78, st=0.367 |
| GROWING+LOW | k=78, st=0.161 | k=102, st=0.163 | k=132, st=0.169 |
| GROWING+HIGH | k=78, st=0.356 | k=102, st=0.354 | k=132, st=0.347 |

Achieved CV is 0.190 or 0.450 in all twelve cells.

**Two cells are controls with known values.** FIXED+LOW is the frozen family
and should reproduce **+0.905**, measured independently twice. GROWING+HIGH
approximates the capacity family and should land near **+0.514**. If either
control misses, the run is diagnosed before its main effects are read.

## Protocol

Ladder n ∈ {12,500, 25,000, 50,000} at ρ = 4.0, dim 1024, k = 10. **32 seeds
per cell**, seeds **200 to 231**, disjoint from round 17b's 0 to 11 and round
17c's 100 to 131. Slopes summarised by the median with a bootstrap standard
error, per [`spec/ESTIMATOR.md`](../spec/ESTIMATOR.md).

## Predictions

Registered as main effects, **not as a range on point estimates**. Round 17c's
flat band was passable by a true positive only 1.7% of the time, and that
mistake is not repeated. Each effect is tested by permuting its own factor
label while holding the other factor fixed, which is a valid test of that main
effect and needs no distributional assumption.

**P-18A, growth.** The COUNT main effect, mean(FIXED) − mean(GROWING), is
positive with permutation p < 0.05. Passing means the presence of cluster
count growth lowers hub scaling and that its rate does not matter, which is
consistent with everything round 17c saw.

**P-18B, size.** The SIZES main effect, mean(LOW) − mean(HIGH), is non-zero
with permutation p < 0.05. Round 17c's within-family evidence predicts this
**fails**, since doubling the CV there moved nothing. It is registered anyway
because 17c varied CV only alongside growth, and a factor can be inert in one
context and active in another.

**P-18C, interaction.** Reported for completeness. A significant interaction
with either main effect absent would mean neither factor acts alone and the
mechanism is joint, which would redirect rather than close the search.

The registered expectation is **A passes and B fails**. That is the reading
under which the frozen family's excess hub scaling is caused by holding the
cluster count fixed while n grows, and it is the one consistent with the
round-17 intervention, with round 17c's flatness, and with the CV evidence
that killed the regularity hypothesis.

## What follows

If A passes and B fails, the target for an admissible family is a process
whose cluster count grows at **any** positive rate without reading n. The
capacity-limited process from round 17b already is such a process, and round
17c measured it at +0.514 ± 0.065 against real's +0.51. The remaining work
would be a proper admission run on fresh seeds against the full RC-1 battery,
not a new family.

If B passes, the size law is implicated and the frozen family's Zipf
allocation becomes the target instead.

If neither passes with controls intact, both candidates are eliminated and the
difference between +0.905 and +0.514 lies somewhere neither round has
parameterised, which would be the strongest argument yet for abandoning this
family.
