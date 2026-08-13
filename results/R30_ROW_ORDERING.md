# The density response is a property of row ordering

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/density_ordering.py`; records
`results/density_ordering.json`, `density_fildim.json`. Follows `R29`, which
registered the density ladder as `PROFILE.md` §3b.

## The question `R29` left

§3b excludes i.i.d. generators a priori: rows that are identically distributed
regardless of pool size cannot respond to density. But the two filament arms
measured as controls also spanned ~0 (+0.013, +0.014) **despite having shared
thread structure**. Structure was evidently necessary but not sufficient, and
the reason mattered — it decides whether the criterion is satisfiable at all.

## Why the filament family has no density variable

`filament_gen.py:126`:

```python
owner = rng.integers(0, n_thread, n)
```

Thread membership is assigned uniformly at random across the row index, and
`n_thread` is fixed by the *generation* size rather than by the pool. A prefix
of P rows therefore contains **every** thread, thinned proportionally, so the
expected co-thread count in a draw of n rows is `n / n_thread` — independent of
P. The pool can be varied over an order of magnitude and nothing about the
sampled geometry changes.

Real is not like this, and the difference is measurable directly. Mean cosine
between rows at index gap g, against a random-pair baseline of 0.2279:

| gap | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 |
|---|---|---|---|---|---|---|---|---|
| cos | 0.598 | 0.530 | 0.449 | 0.367 | 0.304 | 0.267 | 0.246 | 0.236 |

A Wikipedia corpus is **ordered by article**: adjacent rows are passages of the
same article, and the correlation decays smoothly to the baseline over roughly
100 rows. So a prefix of P rows contains proportionally *fewer distinct
articles*, and subsampling genuinely thins the group inventory. That is what
makes density a variable for real and not for the generator.

**The density response is therefore a property of row ordering, not only of
shared structure.** This was not obvious in advance and is not something any
previous round tested: every family to date was scored on geometry alone, and
row order was treated as arbitrary.

## Ordering creates the response

Replacing the random owner with `owner(i) = i // points_per_thread` — cheaper
than the RNG draw, deterministic, and trivially random-accessible:

| family | ratio span | log G1 span |
|---|---|---|
| **real (target)** | **+2.397 ± 0.085** | **−0.494 ± 0.054** |
| filament, random owner, pt48 | +0.014 | +0.025 |
| filament, contiguous, pt48 | +4.531 | +0.173 |
| filament, contiguous, pt96 | +2.566 | +0.375 |

A statistic pinned at zero across every parameter setting becomes a live one
that overshoots the target and can be tuned back through it. The mechanism is
confirmed.

## A prediction, made in advance and refuted

The G1 span had the wrong sign. Real's G1 *rises* as the corpus thins (16.3 at
density 0.500 to 26.7 at 0.0417); every contiguous arm's *falls*. The proposed
explanation was that the sign is set by whether within-group dimension sits
below or above between-group dimension — real's within-article neighbourhoods
being lower-dimensional than its cross-article ones, while the generator had
`fil_dim` 48 against `arrange_dim` 40. The registered prediction was that
`fil_dim < arrange_dim` would flip the span negative.

It does not. At `arrange_dim` 40, `points_per_thread` 96:

| `fil_dim` | ratio span | log G1 span | G1 ladder (dense → sparse) |
|---|---|---|---|
| 8 | −0.925 | +0.421 | 9.5 → 6.2 |
| 14 | +0.549 | +0.419 | 14.3 → 9.4 |
| 24 | +1.672 | +0.448 | 21.0 → 13.4 |
| 48 | +2.566 | +0.375 | 32.3 → 22.2 |

`fil_dim` moves the G1 *level* almost exactly (it sets the dense end) and leaves
the span's **sign and magnitude essentially unchanged** — +0.42, +0.42, +0.45,
+0.38 across a 6x range that brackets `arrange_dim` on both sides. The
hypothesis was wrong, and it was wrong in a way the level-vs-shape distinction
should have anticipated: `fil_dim` is a level parameter, and the span is a shape
statistic.

Lognormal group sizes, tried on the reasoning that real's smooth ~100-row decay
is poorly modelled by hard blocks, made the ratio span substantially **worse**
(−11.5, −7.5, −3.9) rather than smoothing the ladder.

## Where this leaves the family

**Still failing, on two counts that no arm escapes.**

1. **The G1 span has the wrong sign in all eight contiguous arms.** Thinning
   raises real's apparent dimension and lowers the generator's. This is a
   direction-level mismatch, not a tuning gap.
2. **The ratio ladder is non-monotone in all eight**, humping near density
   0.125, where real falls monotonically across the whole range.

Real's behaviour has a natural reading — dense sampling brings in same-article
neighbours lying on a low-dimensional manifold, and thinning removes them to
expose higher-dimensional structure — but the obvious implementation of that
reading does not reproduce it, so the reading is not yet supported.

## What is established

* Row ordering, not just shared structure, governs whether a generator has a
  density response at all. This is a new constraint on the construction, and it
  costs nothing: contiguous ownership is cheaper and more random-access-friendly
  than the random draw it replaces.
* Real's corpus has a measured index correlation length of ~100 rows, decaying
  smoothly. Any generator claiming to match it must reproduce that decay, which
  is now measurable and was previously unexamined.
* `fil_dim` is a level parameter for G1 and does not affect the density-span
  shape. Recorded so it is not retried.

## What is not

* No candidate. The family fails §3b on sign and on monotonicity.
* The mechanism behind real's *negative* G1 span is unexplained. Until it is,
  tuning against §3b is search rather than construction, and the eight arms here
  are already a multiple-comparisons load on a two-number target.
