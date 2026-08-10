# The index cascade is over-constrained: its weights already fix s(r)

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Drivers `harness/rc1/scurves.py`,
`harness/rc1/derive_level_dims.py`; records `results/scurves.json`,
`leveldims.json`. Follows `R32`. Reference: Blum, Hopcroft & Kannan,
*Foundations of Data Science*, §2.3–2.4 and the Gaussian Annulus Theorem
(Fig. 2.1).

## First: the s(k) curves, which correct `R31`

`R32` left the ramp as the single discrepancy but only ever measured its
summary, `s(500)/s(4)`. Measuring the curve itself:

| k | 4 | 8 | 14 | 28 | 53 | 100 | 263 | 500 |
|---|---|---|---|---|---|---|---|---|
| real b=1 | 27.40 | 30.74 | 33.82 | 36.32 | 37.02 | 37.69 | 36.95 | 35.13 |
| real b=100 | **8.82** | 11.46 | 16.08 | 23.40 | 28.88 | 31.29 | 34.82 | 35.73 |
| ratio | 3.11 | 2.68 | 2.10 | 1.55 | 1.28 | 1.20 | 1.06 | **0.98** |

**The two regimes converge.** Real's large-k dimension is ~35–37 regardless of
how the corpus is sampled; same-article neighbours drop `s(4)` from 27.4 to 8.8
and leave `s(500)` untouched. The ramp is entirely a small-k phenomenon.

This **corrects `R31`'s framing**. That round described "two nested regimes,
G1 ≈ 15 and G1 ≈ 26". The measurements are right but the reading is not: G1 is
TwoNN, a k = 1,2 statistic, so it reads the finest scale rather than the
manifold. Real is one ~36-dimensional cloud carrying a very low-dimensional
(~9) local structure that appears only when adjacent rows are sampled. `R32`
calibrated `slow_dim` = 26 against a G1 of 26 and duly produced `s(500)` = 18
against real's 35 — the arrangement came out half-size because the calibration
targeted the wrong scale.

## A prediction from the geometry, and its refutation

Blum et al. §2.3 gives near-orthogonality of independent components in high
dimension, so squared distances add; §2.4.1 gives volume growing as `r^d`. For a
sum-of-components construction, rows differing in levels 0..L sit at radius
`R(L) = sqrt(2 * sum_{l<=L} w_l^2)` and their difference spans the sum of those
levels' subspaces. That appears to give

```
s(R(L)) = cumulative dimension = sum_{l<=L} d_l
```

which inverts to a per-level schedule from a measured `s(r)`, and — the
attractive part — **decouples** the constraints: weights fixed by the
autocorrelation (`R30`), dimensions by the `s(r)` curve. `R32` had tied them
together through a two-way fast/slow split, which was the diagnosis for why it
produced no ramp.

Inverting real's b = 100 curve gave `d = (9, 1, 5, 17, 5, 1, 1, 1)`, cumulative
9 → 13.5 → 30.8 → 35.7. Four schedules were then built and measured, with
mutually orthogonal per-level subspaces so the cumulative sum could not collapse:

| schedule | s(4) b=100 | s(500) b=100 | ratio | rms vs real |
|---|---|---|---|---|
| **real** | **8.82** | **35.73** | **4.050** | — |
| derived (9,1,5,17,5,1,1,1) | 17.32 | 16.46 | 0.950 | 12.00 |
| derived×2 (…,3,3,3) | 19.73 | 18.69 | 0.947 | 10.78 |
| steeper (7,1,4,20,8,2,2,2) | 18.82 | 16.91 | 0.898 | 11.60 |
| smoother (9,2,4,8,10,6,3,2) | 20.10 | 19.91 | 0.990 | 10.11 |

**The prediction fails.** `s(4)` should have been 9 and measured 17.3; `s(500)`
should have been 40 and measured 16.5. More telling, the schedule barely matters
— a 6× change in `d_3` moves `s(4)` by 3 units and the ratio not at all.

## Why it fails, and what that means for the family

The error was treating the neighbour count `k` as free. **In an index cascade it
is pinned by the construction**: the rows within index gap `2^L` number exactly
`2^L`, and they sit at radius `R(L)`. So

```
s = dlog k / dlog r = ln 2 / ln( R(L+1) / R(L) )
```

which depends on the **weights alone**. Evaluating it on `CASCADE_WEIGHTS` gives
9.11, 7.34, 7.06, 9.71, 17.68, 33.06, 47.92 across levels — squarely the
measured range, and with no reference to any `d_l`. Subspace dimension governs
only the spread *within* a level, a second-order effect, which is exactly what
the four-schedule invariance shows.

The Gaussian Annulus Theorem is what makes this bite: each level's contribution
to the distance is concentrated in a thin shell, so a level behaves as a near-
discrete radius step rather than as a `d_l`-dimensional volume to be filled.

**So the family is over-constrained.** The autocorrelation determines the level
weights, the level weights determine `s(r)`, and there is no remaining freedom.
The two constraints I claimed were independent are the same constraint. Real's
autocorrelation and real's `s(r)` are jointly unsatisfiable by an index cascade,
and no schedule of dimensions changes that.

Worth noting the weight-implied `s` does rise 9 → 48 across levels, which is
qualitatively real's shape. The measured curves are flat at ~17–20 instead,
because a median-based `r(k)` blends neighbours drawn from several levels and
washes the staircase out. Both facts point the same way: the doubling structure
is too coarse a control over the radius–count relation.

## Status

**The index-cascade family is closed.** It joins the ten before it, but on a
sharper basis than most: not "no parameter setting was found" but "the
construction has one degree of freedom where two are needed, and this is
provable from the level structure".

`R32`'s partial success stands and is unaffected — three arms matched the §3b
log G1 span, unfitted, and that came from the ordering and adjacency structure
rather than from the level dimensions. What is now closed is the route from
there to the ramp.

## What is not established

* Whether *any* random-access construction can decouple the radius–count
  relation from the autocorrelation. A non-dyadic level structure, or variable
  group sizes, would give a finer control over `k` at a given radius; neither
  was tried.
* Why real's `s(4)` at b = 100 is 8.8 while its `s(500)` is 35.7 — the
  mechanism, as opposed to the measurement, remains unexplained.
* The correction to `R31` is a correction of framing only. Every measured value
  in that round stands.
