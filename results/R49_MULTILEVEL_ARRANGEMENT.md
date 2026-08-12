# A multi-level arrangement fixes the middle of s(k), not its ends

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12. Driver `harness/rc1/arrlevels_probe.py`; record
`results/arrlevels.json`. Follows `R47`.

## The prediction under test

`R47` found that smearing the article — distributed extents, distributed
super-cluster occupancy, more path levels — makes `s(k)` *worse*, and relocated
the problem: since only ~23 neighbours are index-local (`R34`) yet real's `s(k)`
rises smoothly to k = 500, the smooth rise belongs to the **arrangement**, which
in every round from `R36` had exactly one clustering level.

The test replaces that single super-cluster level with `arr_levels` nested
scales, level L grouping `27 * branch^L` articles, weights decaying 0.72 per
level.

## Result: the prediction was right about the middle

| arr_levels | branch | g5 | eff_rank | g1 | g6 | ratio | **rms** | s(4) | s(14) | **s(53)** | s(100) | s(500) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **real** | | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** | — | **8.8** | **16.1** | **28.9** | **31.3** | **35.7** |
| 1 | 4 | 1.681 | 206.9 | 13.17 | 1.726 | 5.505 | 16.43 | 11.4 | 8.2 | 10.9 | 42.6 | 62.6 |
| 3 | 4 | 1.675 | 210.5 | 13.25 | 1.682 | 5.167 | 13.18 | 11.4 | 8.1 | 22.4 | 39.5 | 58.8 |
| 5 | 4 | 1.668 | 210.2 | 13.21 | 1.671 | 5.141 | 13.24 | 11.2 | 8.3 | 29.4 | 42.8 | 57.8 |
| **3** | **8** | 1.675 | 198.6 | 13.10 | **1.671** | **4.608** | **10.84** | 11.5 | 8.2 | 22.8 | 36.4 | 53.0 |

**`s(53)` moves 10.9 → 22.4 → 29.4 against real's 28.9** as levels are added.
The mid-curve was arrangement-limited exactly as `R47` diagnosed, and this is
the first mechanism in the arc that improves the *shape* rather than trading one
summary against another.

Wider branching helps more than more levels: `arr_levels` 3 with `branch` 8
gives the best rms (10.84) and the best ratio (4.608), better than either
`branch` 4 arm at any level count. Coarser separation between scales beats
finer subdivision.

**Comparability caveat.** The `arr_levels` = 1 arm here is *not* the `R46`
baseline. This round rewrote the centre construction — level 0 groups 27
articles where `R46` used `per_super` = 110 — so 16.43 against `R46`'s 11.32 is
not a regression, and only the within-round trend is meaningful. The `branch` 8
arm at 10.84 is the first number here directly comparable in magnitude to the
old baseline, and it beats it.

## Both ends remain wrong, and they are different problems

* **The k = 14 dip is untouched:** 8.2, 8.1, 8.3, 8.2 across every arm, against
  real's 16.1. Adding arrangement levels does nothing to it. This sits just past
  the article boundary, so it is the article-to-arrangement *transition*, not
  the arrangement itself.
* **The k = 500 overshoot persists:** 53.0 at best against real's 35.7. `s(500)`
  is set by the coarsest scale, and adding levels made it *better* (62.6 → 53.0)
  without approaching the target.

So the curve now has the right shape in its middle third and the wrong shape at
both ends, which is a more tractable position than a uniform oscillation but is
not a match.

## What is established

* The arrangement's single clustering level was the cause of the mid-curve
  collapse, and nesting fixes it: `s(53)` from 10.9 to 29.4 against 28.9.
* Wider branching (8) beats more levels (5) — best rms 10.84, best ratio 4.608.
* The k = 14 dip is insensitive to arrangement structure across four arms, so it
  belongs to the article/arrangement transition.
* g6 stays put (1.67-1.73 against 1.696) throughout, so the `R44` hubness fix
  survives the rewrite.

## What is not

* Whether the k = 14 dip can be filled at all. Nothing tried in `R47` or here
  moves it, and it is now the largest single error in the curve (−7.9).
* Whether `s(500)` can be brought to 35.7 without undoing the mid-curve gain.
* The g1 level regressed to ~13.1 against 17.23 in this rewrite and was not
  tuned back; `d_loc`, `fil_dim` and `w_loc` were held at the `R46` values
  throughout and are the obvious knobs.
* §3b spans were not measured for any arm here.
