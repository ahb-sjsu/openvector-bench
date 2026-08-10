# A corpus as a trajectory: the G1 half solved, the ramp untouched

> **Follow-up (`R33`).** The ramp is not reachable from here. `slow_dim` was
> calibrated against a G1 of 26, but G1 is a k = 1,2 statistic and real's
> large-k dimension is ~36 — hence `s(500)` = 18 against real's 35. More
> fundamentally, an index cascade pins the neighbour count (`2^L` rows within
> gap `2^L`), so `s(r)` is a function of the level weights alone and the
> autocorrelation match already consumes that freedom. The family is closed.
> The §3b log G1 result below is unaffected.

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Generator `openvector_bench/twoscale_gen.py`; records
`results/cascade.json`, `twoscale.json`. Follows `R31`.

## What was built, and why it is not a fit

`R31` gave a description of real rather than a target to hit: two nested regimes
(within-article G1 ≈ 15, cross-article G1 ≈ 26) with a graded decay between
them, and groups contiguous in row index. This round builds to that description
and then checks the `PROFILE.md` §3b spans, **which were deliberately excluded
from the construction**.

### First attempt: groups of balls — refuted

`twoscale_corpus` places each group's rows i.i.d. in a low-dimensional ball
around a group centre, with all centres in one `arr_dim`-dimensional frame. The
arrangement calibrates cleanly — at `arr_dim` 24 the centre cloud measures G1
27.20 against real's 26.09, and the calibration sweep at 1024 dimensions is in
`cascade.json` — which is already an improvement on `R30`, where a requested
`arrange_dim` of 40 delivered a measured 6–13.

It still fails the cross regime outright: **G1 7.2 against 26.1**. At
`group_size` 100 over 600k rows a b = 1 clumping draw still takes ~6 rows per
group, and because those rows are i.i.d. in a tight ball they collapse the local
dimension. Real is not flat within a group — `R30` measured cosine decaying
0.598 → 0.304 → 0.236 across index gaps 1 → 16 → 128.

### Second attempt: a trajectory indexed by row

`cascade_corpus` treats the corpus as a path in embedding space rather than a
bag of clusters:

```
x(i) = sum_s w_s * v(s, i >> s) + w_glob * m
```

Two rows share the level-`s` component iff `i >> s == j >> s`, so cosine falls
off with index gap exactly as the weights dictate. The weights were fitted by
NNLS to `R30`'s measured autocorrelation and reproduce it to three decimals
(0.5976 / 0.5305 / 0.4504 / 0.3677 / 0.3052 vs 0.598 / 0.530 / 0.449 / 0.367 /
0.304).

**That agreement is not evidence.** The fit has sixteen free non-negative
parameters against eight measured gaps -- NNLS drives all but nine to zero, but
the model still interpolates by construction. What it buys is a corpus whose
autocorrelation is real's *by design*, so that G1, the ratio and the §3b spans
become a genuine out-of-sample test.

Fast levels live in a `fast_dim` subspace and slow levels in a wider `slow_dim`
one. Without that split the per-row component would sit in the ambient 1024 and
the local dimension would be 1024, not 15.

## Result: the G1 half lands, unfitted

| arm | cross G1 (b=1) | within G1 (b=100) | ratio span | log G1 span |
|---|---|---|---|---|
| **real** | **26.09** | **15.85** | **+2.397 ± 0.085** | **−0.494 ± 0.054** |
| f12_s26 | 33.82 | 19.87 | +0.123 | **−0.425** |
| f15_s26 | 37.01 | 20.19 | +0.147 | **−0.454** |
| f20_s26 | 41.35 | 20.55 | +0.191 | **−0.563** |
| f12_s40 | 38.25 | 18.33 | +0.132 | −0.608 |
| f15_s40 | 40.62 | 18.35 | +0.179 | −0.689 |
| f20_s40 | 44.71 | 18.04 | +0.220 | −0.751 |

**Three arms put the log G1 span inside the registered ±2 sd band
[−0.602, −0.386] without it being fitted.** No generator in thirty-one rounds
has matched a §3b span before, and `R28`–`R30` could not even get its sign
right. The G1 ladder runs in real's direction (22.5 → 34.4 as density falls,
against real's 16.3 → 26.7), and cross-regime G1 exceeds within-regime G1 —
the ordering `R30` had backwards.

Two things follow. The ordering hypothesis of `R30` and the adjacency mechanism
of `R31` are jointly supported: build a trajectory with real's autocorrelation
and real's density–G1 relationship appears on its own. And the sign error that
closed the filament family was a property of the group-of-balls construction,
not of generators in general.

## Result: the ramp is untouched

**The ratio span is +0.12 to +0.22 against a target of +2.397 — off by a factor
of 10 to 20.** The regime ratios are ~0.8 (cross) and ~1.0 (within) against
real's 1.28 and 4.05. The generator's growth dimension is essentially constant
across the k grid: it has no ramp at all.

This is the oldest open problem in the project — `R21B` measured |trend| ≤ 0.13
for every synthetic family tried, and this construction does no better despite
reproducing the autocorrelation exactly and the G1 response well.

The negative result is informative. Real's index autocorrelation and real's
density–G1 relationship are **jointly insufficient** for the ramp. A corpus can
have real's correlation structure at every index scale, and real's
dimension-versus-density behaviour, and still show `s(500)/s(4) ≈ 1`. Whatever
carries the ramp is not visible in either.

## Where this leaves things

**Not a candidate.** One of the two §3b summaries is matched and the other is
out by an order of magnitude; G1 levels run ~30% high throughout.

**A partial mechanism, established.** The density–G1 relationship is reproduced
by construction from measured inputs, and the parameters that control it
(`fast_dim`, `slow_dim`, the level weights) are interpretable rather than fitted
coefficients. Six arms is a light multiple-comparisons load for a two-number
prediction, and the span was not among the quantities tuned.

**The ramp is now isolated.** It is the single remaining discrepancy, it is
large, and it survives a construction that gets everything else structurally
right. That makes it a cleaner target than it has ever been: previous rounds
missed the ramp *and* the dimension response *and* the ordering together.

## What is not established

* Why real has a ramp at all. Nothing here explains `s(500)/s(4) = 4.05`.
* Whether the ~30% G1 level offset is a tuning matter or another structural
  gap. It was not investigated.
* Bit-exactness and random access. `cascade_corpus` is *structured* for random
  access — every component is indexed by `i >> s` — but uses a numpy RNG and
  materialised tables, so it is not yet byte-reproducible.
