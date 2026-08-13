# A row has ~23 index-local neighbours, and that produces the first ramp

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Drivers `harness/rc1/nn_index_gap.py`,
`harness/rc1/articles_probe.py`; records `results/nn_index_gap.json`,
`articles.json`. Follows `R33`.

## The measurement that closes the trajectory family

`R33` closed the index cascade because its weights already determine `s(r)`.
Before abandoning index-ordered constructions generally, the non-dyadic
generalisation deserved a check: with level ℓ changing every `g_l` rows rather
than every `2^l`, the count and the radius become separate schedules, and real's
own `r(k)` table supplies both — set `g_l = k` and `R(l) = r(k)`, and the
weights follow with no fitting.

The autocorrelation is then a prediction, and it fails: ρ(1) = 0.888 against a
measured 0.598, rms 0.188 across gaps 1…128. (The `s(k)` agreement such a
schedule shows is a tautology — `s` is the finite difference of the `(k, r)`
pairs it was built from.)

The reason is structural, and measuring it settles the family. Any sum of
block-constant components over the row index makes index proximity **equivalent**
to metric proximity. Real is under no such obligation. Measured on a plain
contiguous 200k block, k-NN index gaps:

| k | 1 | 4 | 8 | 16 | 32 | 100 | 500 |
|---|---|---|---|---|---|---|---|
| median \|Δindex\| | 3 | 5 | 9 | 55 | **14,880** | 39,095 | 52,340 |
| fraction \|Δ\| ≤ 128 | 0.862 | 0.769 | 0.661 | 0.519 | 0.369 | 0.176 | 0.045 |

There is a cliff between k = 16 and k = 32. Below it neighbours are index-local;
above it they are scattered across the corpus. At k = 500 only **22.7 of 500**
neighbours are index-local, and that count stops growing — an index-ordered
construction would give 128.

**A row's neighbourhood is a two-population mixture: ~23 same-article
neighbours, then the global cloud.** That is the ramp. `s(k)` climbs 8.82 → 35.73
precisely across the k = 16–32 crossover, as the neighbourhood leaves a
~23-member, ~9-dimensional article and enters a ~36-dimensional cloud.

Index-ordered constructions are therefore excluded as a class, not as a
parameter region: they cap index-local neighbours at `g_l`, which grows with k,
where real's cap is fixed at ~23.

## The first ramp

`R32`'s first attempt — groups of balls, `twoscale_corpus` — had the right shape
and a guessed constant: `group_size` 100 where real is ~23. Rebuilding at the
measured value, with the arrangement calibrated on **`s(500)`** rather than G1
(`R33`'s correction):

| arm | b=100 s(4) | b=100 s(500) | b=100 ratio | b=1 s(4) | ratio span |
|---|---|---|---|---|---|
| **real** | **8.82** | **35.73** | **4.050** | **27.40** | **+2.397** |
| g23 fd9 fs0.30 | 4.46 | 31.92 | 7.152 | 35.22 | +6.94 |
| g23 fd9 fs0.45 | 4.59 | **35.69** | 7.781 | 39.35 | +7.58 |
| g23 fd9 fs0.60 | 4.66 | 40.28 | 8.645 | 43.68 | +8.56 |
| g23 fd12 fs0.45 | 5.64 | 35.58 | 6.307 | 37.49 | +6.61 |

**Every family measured in thirty-three rounds gave ratio ≈ 1.** This gives
6.3–8.6 against a target of 4.05. The ramp overshoots by roughly 1.9x, which is
a different and far more tractable problem than its absence. `s(500)` lands at
35.69 against 35.73.

One measured constant, substituted for a guess, moved the oldest open quantity
in the project from absent to present.

## What still fails, and the diagnosis

* **b = 100 s(4) is 4.6 against 8.8** — the within-article manifold measures
  about half its requested `fil_dim`, so the ratio overshoots from below.
* **b = 1 s(4) is 39.4 against 27.4**, and **G1 is 4.25 against 26.09**. The
  cross-article regime is wrong.
* **The log G1 span has the wrong sign again** (+0.78 against −0.494).

The cross-article failure has a clean cause. Measuring the arrangement alone:

| arr_dim | 26 | 34 | 40 | 48 | 60 |
|---|---|---|---|---|---|
| s(4) | 19.09 | 23.29 | 26.83 | 30.78 | 36.68 |
| s(500) | 16.63 | 20.11 | 22.42 | 25.34 | 29.32 |
| s(500)/s(4) | 0.871 | 0.863 | 0.836 | 0.823 | **0.799** |

**A uniform cloud in a fixed subspace has a *decreasing* profile at every
dimension tried, where real's cross-article regime *increases* (1.282).** No
choice of `arr_dim` fixes this, because it is not a level problem — the
arrangement has the wrong shape.

So the structure above the article is not flat either. Real presumably carries
further nesting — sections, categories, topical domains — and the ~36-dimensional
"cloud" is itself a mixture across scales. That is consistent with the k-NN gap
table: beyond the article cliff the median gap keeps growing (14.9k → 52.3k),
rather than jumping straight to corpus-uniform.

## Status

**Not a candidate**, and the gaps are large. But the family is no longer
excluded on mechanism, which every previous family was:

* the ramp exists and is the right order,
* `s(500)` matches,
* the remaining errors are in one identified component (the arrangement), with a
  measured diagnosis of what is wrong with it.

## What is not established

* That adding hierarchy above the article level fixes the cross-article profile.
  It is the indicated next step, not a demonstrated one.
* The article size of ~23 is read off a k-NN gap cliff on one contiguous 200k
  block. It is not a distribution — real article lengths are certainly variable,
  and `size_spread` was held at 0 throughout.
* Bit-exactness and random access, untouched since `R32`.
