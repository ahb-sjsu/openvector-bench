# Density was never the variable — index adjacency is

> **Framing correction (added after `R33`).** The "two nested regimes, G1 ≈ 15
> and G1 ≈ 26" reading below is wrong, though every measured value stands. G1 is
> TwoNN, a k = 1,2 statistic, so it reads the finest scale and not the manifold.
> Measuring the full `s(k)` curve shows the two regimes **converge** at large k
> (35.13 vs 35.73 at k = 500): real is one ~36-dimensional cloud carrying a
> ~9-dimensional local structure that appears only when adjacent rows are
> sampled. The adjacency finding itself is unaffected.

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/clumpiness.py`; record
`results/clumpiness.json`. Follows `R29` (which registered the density ladder)
and `R30` (which found row ordering creates a density response but could not
reproduce real's sign).

## The question

`R29` registered a density ladder: at fixed row count, shrinking the pool moves
the ratio 2.8x and G1 1.6x. `R30` showed a generator only has such a response if
its latent groups are contiguous in row index. But real's **G1 rises as the
corpus thins** (16.3 → 26.7) and no generator reproduces that sign, so the
mechanism was unexplained and §3b was a filter rather than a specification.

If thinning works by removing same-article neighbours, then it should be
possible to produce the same effect **without changing density at all** — by
holding the span fixed and varying only how clumped the sample is.

## The experiment

Pool 600k, n = 25,000, span fixed. The 35,000-row support (25k base + 10k
queries) is drawn as `⌈35000/b⌉` runs of `b` **contiguous** rows spread over the
whole corpus, then split exchangeably. Only `b` varies. Alongside it, the
density ladder re-expressed as a *window* ladder: same n, same split
construction, contiguous window W varying.

| clumped, span 600k | ratio | G1 | μ | | window ladder | ratio | G1 | μ |
|---|---|---|---|---|---|---|---|---|
| b = 1 | 1.282 | 26.09 | 1.0293 | | W = 600,000 | 1.309 | 26.60 | 1.0291 |
| b = 2 | 1.493 | 14.06 | 1.0555 | | W = 400,000 | 1.500 | 23.99 | 1.0323 |
| b = 5 | 2.314 | 14.55 | 1.0615 | | W = 200,000 | 1.841 | 19.24 | 1.0412 |
| b = 10 | 3.465 | 15.25 | 1.0583 | | W = 100,000 | 2.393 | 16.98 | 1.0503 |
| b = 25 | 3.797 | 15.78 | 1.0580 | | W = 50,000 | 3.833 | 16.58 | 1.0551 |
| b = 100 | **4.050** | **15.85** | **1.0576** | | W = 35,000 | **4.090** | **16.54** | **1.0553** |
| b = 1000 | 3.778 | 15.71 | 1.0579 | | | | | |
| b = 5000 | 2.939 | 16.08 | 1.0545 | | | | | |

**The two ladders trace the same curve.** The extremes agree to within noise on
all three statistics — b = 1 against W = 600,000 (1.28/26.1/1.029 vs
1.31/26.6/1.029) and b = 100 against W = 35,000 (4.05/15.9/1.058 vs
4.09/16.5/1.055) — with the span held at 600,000 throughout the left-hand
column.

Density is not the mechanism. Shrinking the window mattered only because it
forces adjacent rows into the sample. At a fixed 600k span, clumping the draw
into runs of ten reproduces the dense geometry outright.

## What real actually is

The transition is startlingly sharp. Going from **no** adjacent neighbour to
**one** (b = 1 → 2) drops G1 from 26.09 to 14.06 and lifts μ from 1.0293 to
1.0555. It saturates by b ≈ 25 and is already ~90% complete at b = 10.

So the corpus has two nested regimes, and both are now measured:

| regime | G1 | μ | ratio | reached when |
|---|---|---|---|---|
| within-article passages | ≈ 15 | ≈ 1.057 | ≈ 4.0 | ≥ ~10 same-article rows sampled |
| cross-article structure | ≈ 26 | ≈ 1.029 | ≈ 1.29 | no adjacent rows sampled |

The registered §3 profile is a **mixture** of these two, weighted by how many
same-article neighbours survive sampling. This is why `R27` failed by putting
60% of points in ultra-close pairs and why `R28`'s μ guard mattered: μ is the
mixing coordinate, and the two regimes have distinguishable μ.

## Consequences for §3b

The registered criterion is unaffected as a *measurement* — the ladder, the
values and the bands in `PROFILE.md` §3b were all measured under a fixed
protocol and reproduce. What changes is the **interpretation**, and therefore
what a generator has to do.

* The i.i.d. exclusion stands and is if anything stronger. Adjacency is a
  property of the row *sequence*, which i.i.d. emission does not have.
* "Match the density span" is no longer the right target. The span is a
  consequence of the two-regime structure, not a thing to fit directly. A
  generator built with the regimes above should produce the span without it
  being scored.
* `R30`'s failure is explained. Contiguous ownership gave the generator a
  density response, but its groups were single-scale isotropic balls. Real has
  a **low-dimensional, high-μ within-group regime nested inside a
  higher-dimensional low-μ arrangement** — and the arrangement is the
  *higher*-dimensional of the two, which is the reverse of every filament
  configuration tried (`fil_dim` 48 against `arrange_dim` 40).

That last point identifies the sign error `R30` chased and failed to fix. The
prediction there was right in form and wrong in scale: `fil_dim` must be below
`arrange_dim`, but `arrange_dim` must also deliver a *measured* G1 near 26, and
at `arrange_dim` 40 the arrangement measured G1 6–13 rather than 26. The
parameter was set; the resulting geometry was never checked.

## An error worth recording, again

The first version of this experiment drew queries as a uniform holdout over the
whole 600k while the base was clumped. As `b` grows the base localises and the
queries do not, so the split becomes non-exchangeable and G1 inflates — it read
26.75 → 60.92, smooth and monotone, and pointed at the exact opposite
conclusion. The tell was that b = 1, the only arm where base and query support
coincide, reproduced the known-good 26.66.

This is the third occurrence in two days (`R29`'s factorial grid, `R30`'s
ordering test, and here), each time producing plausible monotone numbers. The
split construction has therefore been moved into
`geometry.exchangeable_split()`, which takes a support and partitions it, so
the support is chosen once and cannot diverge between base and queries.

## What is established

* The density response is an **adjacency** effect. Span and row count can be
  held fixed and the entire effect reproduced by clumping alone.
* Real's two regimes, with G1, μ and ratio measured for each, and the crossover
  located at ~10 same-article rows.
* One adjacent neighbour is worth ~12 units of G1. The first neighbour does
  nearly all the work.

## What is not

* **No generator.** This is a specification, not a candidate: build the two
  regimes with the measured constants and the density ladder should follow, but
  nothing here demonstrates that it does.
* Whether the ~100-row correlation length of `R30` and the ~10-row crossover
  here are the same structure seen two ways is not established.
* The within-article regime is characterised by three summary statistics, not
  identified. Many constructions have G1 15 and μ 1.057.
