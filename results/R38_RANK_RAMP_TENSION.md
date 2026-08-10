# Rank and ramp pull against each other, and g5 follows neither

> **Corrected by `R40`.** The claim that g5 "responds to nothing tried" is
> **withdrawn**. g5 is governed by the within-article *variance*, which is
> `fil_scale` — held at 0.45 in every arm below. Varying it moves g5 from 2.658
> to 1.348, through real's 1.369. `eff_rank` follows the same knob (75.7 →
> 284.9), so the rank-versus-ramp opposition recorded here is an artifact of
> having moved rank with `d_glob`; `fil_scale` moves rank further at a fraction
> of the cost to the ramp. The measurements below stand; the conclusions drawn
> from them do not.

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/tension_probe.py`; record
`results/tension.json`. Follows `R37`.

## The risk that was flagged, now tested

`R37` ended with two statements marked untested: that fixing `eff_rank` might
fix the mandatory g5 relative-contrast gate, and that spreading the variance
might not leave the §3b profile intact — "the same over-constraint that closed
the cascade family in `R33`". Both are now measured. **The first is wrong and
the second is right.**

Sweeping `d_glob` with per-cluster orientations, measuring the gates on 210k
rows and the §3b ladder on 600k, in the same build:

| d_glob | eff_rank | dims90 | g5 | g1 | g6 | b=100 ratio | ratio span |
|---|---|---|---|---|---|---|---|
| **real** | **182.3** | **359** | **1.369** | **17.23** | **1.696** | **4.050** | **+2.397** |
| 90 | 111.1 | 448 | 2.670 | 17.34 | 1.596 | 5.248 | +4.849 |
| 150 | 151.6 | 461 | 2.671 | 17.37 | 1.597 | 6.979 | +6.148 |
| 250 | 190.9 | 475 | 2.672 | 17.53 | 1.594 | 8.865 | +8.088 |
| 400 | 227.1 | 480 | 2.674 | 17.80 | 1.584 | 10.627 | +11.006 |

## Rank and ramp are in direct tension

Both move monotonically with `d_glob`, in opposite directions relative to their
targets. `eff_rank` reaches real's 182.3 near `d_glob` ≈ 235; interpolating, the
b=100 ratio there is **8.45 against a target of 4.050**, and the ratio span is
roughly +7.6 against +2.397.

There is no setting of `d_glob` at which both hold. Worse, the ramp is already
too high at the *smallest* `d_glob` tried (5.248 at 90), so the tension cannot be
escaped by going lower — and going lower is what `eff_rank` least tolerates.

This is the same structural situation as `R33`: a construction with fewer
effective degrees of freedom than the targets require. There the autocorrelation
and `s(r)` were one constraint wearing two hats; here the global subspace
dimension sets both the eigenvalue spread and the cross-article radius that the
ramp is measured against.

## Per-cluster orientations cost the ramp

`R37` introduced per-cluster orientations to fix the spectral tail, and measured
gates only. Re-measuring §3b on that variant shows the cost: at matched
parameters (`d_glob` 90, `fil_dim` 22) the b=100 ratio is **5.248** where the
linear variant of `R36` gave **4.580**. The orientation change improved `dims90`
by 1.6 log units and moved the ramp ~15% away from target.

So the `R36` result — ramp matched to 3.7% — belongs to the linear variant,
which is the one that fails `dims90` by 1.38 log units. The two best results in
this family are held by two different, incompatible builds.

## g5 is not a rank effect

**`g5` sits at 2.670, 2.671, 2.672, 2.674 across a 2x range of `eff_rank`.** Four
significant figures, no response whatsoever. The `R37` conjecture that relative
contrast would follow the rank deficit is refuted.

It is also unmoved by `fil_dim` (`R37`: 2.522 → 2.581 across 16–30) and by the
linear-to-per-cluster change (2.522 → 2.653). Nothing tried in this family moves
g5, and it is 1.95x real on a **mandatory** gate.

That is the more serious of the two findings. A quantity that does not respond
to any available knob is not a tuning problem.

## What survives

g1 and g6, the other two mandatory gates, hold across the entire sweep — g1
between 17.34 and 17.80 against real's 17.23, g6 between 1.584 and 1.597 against
1.696. They are insensitive to `d_glob`, which is itself informative: the
neighbourhood structure that `R34`–`R36` built is robust, and it is the
*ambient* structure that the family cannot get right.

## Status of the family

Not a candidate, and now with a demonstrated internal tension rather than a list
of unmet targets:

* rank and ramp cannot be satisfied together,
* g5 (mandatory) responds to nothing tried,
* the two best partial results belong to incompatible builds.

The neighbourhood-scale work stands: article size 23 and super-cluster size 110
are measured constants, the adjacency mechanism (`R31`) is established, and g1
and g6 hold. What is not in hand is any construction that carries that
neighbourhood structure inside an ambient geometry resembling real's.

## What is not established

* Whether a knob outside those swept (`w_loc`, `fil_scale`, `per_super`, the
  direction-pool size) decouples rank from ramp. Four parameters were held fixed
  during this sweep, so "over-constrained" is demonstrated for `d_glob` and
  conjectured in general.
* What does drive g5. Relative contrast is a ratio of far to near distances; the
  family's near distances are set by `fil_scale` and its far distances by the
  normalisation, and neither was varied against g5 directly.
* Whether real's eff_rank of 182 alongside intrinsic dimension ~36 requires
  curvature that no union-of-linear-patches can supply, which would close the
  family outright rather than by parameter exhaustion.
