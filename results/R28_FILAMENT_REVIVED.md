# The filament shape is live again — R21C's exclusion was a parameterisation artifact

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-09. Driver
[`harness/rc1/filament_occupancy.py`](../harness/rc1/filament_occupancy.py);
records `filament_occupancy.json`, `filament_fine.json`, `filament_fine2.json`,
`filament_fine3.json`, `filament_dup.json`, `real_mu.json`.

## What forced the revisit

`R27` matched the profile trend with recursive near-duplicates and could not fix
G1. Measuring real's local geometry explains why, and closes that family:

| statistic | real @ n=20k |
|---|---|
| r₁ median | 0.7911 |
| μ = r₂/r₁ median | **1.0523** |
| fraction μ > 1.5 | **1.7%** |
| fraction r₁ < 0.5 | 3.4% |

μ ≈ 1.05 means first and second neighbours sit within 5% of each other — a
smooth ~17-dimensional local structure, exactly what G1 ≈ 17 implies. Real has
**essentially no near-duplicates**. R27 put 60% of points in ultra-close pairs.
It matched the scored statistic through a mechanism real does not use, and the
ultra-close pairs generating its ramp are precisely what suppressed its G1.

If the ramp is not duplicates it must be smooth multi-scale structure — low
dimension locally, high dimension in the arrangement. That is the **filament**
shape, which `R21C` excluded because `s_lo` rises with n where real's falls.

## R21C's exclusion does not survive

R21C held the thread count **fixed**, so points-per-thread grew with n. Sweeping
occupancy directly, with thread count scaling as pool size:

**`s_lo` falls with n in 120 of 120 arms measured across four sweeps** — real's
direction. The transition is governed by occupancy exactly as predicted: below
~4 points per thread it falls, above ~12 it rises. R21C tested only the rising
regime. **The exclusion was a parameterisation artifact, not a property of the
shape.**

## Where the family stands

Targets are real's, same protocol (`small_rung_targets.json`, `real_mu.json`).

| arm | trend | G1 | G1 exp | μ | μ>1.5 |
|---|---|---|---|---|---|
| **target** | **+0.978** | **17.7** | **−0.073** | **1.052** | **0.017** |
| pt4.0 fd48 ad40 fs0.200 | +1.146 | 20.9 | −0.171 | **1.052** | 0.000 |
| pt4.5 fd48 ad40 fs0.200 | +1.566 | 20.0 | **−0.077** | **1.052** | 0.000 |
| pt4.0 fd48 ad40 fs0.225 | **+0.865** | 24.0 | −0.273 | 1.048 | 0.000 |
| pt4.0 fd32 ad40 fs0.250 | **+1.005** | **19.0** | −0.278 | 1.062 | 0.001 |

Each target is individually reachable, and **μ matches real exactly (1.052) at
fil_dim 48** — this family produces the ramp through smooth structure, which is
real's actual mechanism, not through duplicates. No single configuration matches
trend, G1 and the G1 exponent simultaneously; it is a three-way trade.

`fil_scale` is a genuine second axis rather than a re-parameterisation of
occupancy: at fixed occupancy, 0.1 → 0.5 moves G1 from 5 to 81 while leaving the
trend far less affected.

## A small duplicate population is compatible — R27 failed on proportion alone

The pure filament family has `μ>1.5` = 0.000 where real has 0.017, so it is
*missing* a component real demonstrably has. Overlaying duplicates at realistic
strength:

| dup fraction | μ>1.5 | trend | G1 | G1 exp |
|---|---|---|---|---|
| 0.00 | 0.000 | +0.865 | 24.0 | −0.273 |
| 0.02 | 0.032 | +0.891 | 23.1 | −0.297 |
| 0.04 | 0.067 | +0.914 | 22.7 | −0.342 |

2% duplicates add the μ population while costing almost nothing elsewhere, and
~1% would land real's 0.017 exactly. So the two mechanisms **coexist** at
realistic strength: R27's failure was one of proportion (35x too many), not of
kind. Real appears to be a smooth filament-like structure *plus* a ~2%
near-duplicate population.

## Search budget, disclosed

`GENERATOR_SEARCH.md` §5.3 requires this. **~158 arms across five sweeps, scored
against five targets, all at reduced rungs (5k/10k/20k).** That is a substantial
multiple-comparisons load: a well-placed point in a 158-arm search is a weaker
evidential object than a confirmed prediction, and the results above should be
read accordingly.

Two things partially offset it. The **μ guard** is not something the search tunes
toward — it falls out of the construction, and it caught R27. And the parameters
are interpretable quantities a real corpus has (local semantic dimension,
topical arrangement dimension, passages per topic), not free coefficients.

## What is not established

1. **No simultaneous match.** Trend, G1 and G1 exponent trade three ways.
2. **Reduced rungs only.** Everything is 5k/10k/20k against small-rung targets
   from a 60k pool. `PROFILE.md`'s registered targets come from a 600k pool, and
   `R24` established that **density**, not row count, governs this profile — so
   these are not the same target and this is not a candidate until re-tuned
   there.
3. **The build does not scale yet.** `build()` loops over threads in Python; the
   registered protocol needs ~174,000 threads at a 600k pool. The fix is a
   construction change — a shared pool of direction vectors indexed by hash per
   thread, rather than an independent basis per thread — which also makes the
   family bit-exact and random-access, but must be shown equivalent at tested
   scale first.

## Next

Shared-basis vectorisation, verify equivalence at reduced scale, then **re-tune**
(not merely re-measure) against `PROFILE.md`'s registered targets at a 600k pool.
Only then is there a candidate worth adversarial validation.
