# The filament shape survives R21C, but fails the registered protocol

> **Outcome notice (added after registered-scale testing).** Everything below
> was measured at reduced rungs. At `PROFILE.md`'s registered protocol the
> family **fails**: see the closing section. The two findings that survive are
> that real has no near-duplicates, and that R21C's exclusion was a fixed-F
> artifact. The claim that the family was "close and needs re-tuning" does not
> survive and is retracted.

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


## Registered-protocol result: the family fails

`filament_registered2.json`, 600k pool so per-rung density matches the
registered protocol, 10k holdout, rungs 25k/50k/100k. Targets measured under the
same protocol (`registered_targets.json`): trend +0.440, G1 23.1, G1 exponent
−0.174, mu 1.0346.

| arm | trend | G1 | G1 exp | mu |
|---|---|---|---|---|
| target | +0.440 | 23.1 | −0.174 | 1.0346 |
| pt4 (reduced-scale optimum) | +0.113 | 100.2 | −0.597 | 1.008 |
| pt48 | +6.166 | 21.0 | **+0.158** | 1.047 |
| pt96 | +2.471 | 23.8 | **+0.260** | 1.042 |

**A parameterisation error found here, and it matters for reading everything
above.** Occupancy was defined as points-per-thread *in the pool*, but the
geometry responds to points-per-thread *in the rung*, and the rung/pool ratio
differs by a factor of five between protocols — 91% at reduced scale, 17%
registered. So `points_per_thread` does not mean the same thing in the two
settings, and the ~158 arms of reduced-scale tuning were optimising a quantity
that does not transfer.

Correcting it fixes the G1 *level* (21.0 and 23.8 against 23.1) and breaks
everything else: the trend runs 5-14x high, the **G1 exponent takes the wrong
sign** — G1 rises with n where real's falls — and the ratios become erratic and
non-monotonic (2.775 / 9.238 / 6.201). Across both registered attempts the
family gives either G1 five times too high with too little trend, or the right
G1 with far too much trend and an inverted exponent.

**The reduced-scale fit was an artifact of its density regime.** This is
consistent with `R24`, which found density — not row count — governs the profile
for *real* embeddings; it should not have been surprising that it governs the
generator too. The requirement that follows is stronger than the five-target
match pursued above: a candidate must reproduce **how the profile moves with
density**, not merely its values at one operating point. Nothing in twenty-three
rounds has been tested against that.
