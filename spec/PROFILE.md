# The scale-resolved dimension profile — registered statistic and bands

**Status: REGISTERED 2026-08-09.** Registered *before* being used as an
admission criterion, and before any generator has been searched against it.
Companion to `PREREG_RC1.md` (which registers the eight gates) and
`R21B`/`R23`/`R24`/`R25` in `results/` (which measured everything below).

This document exists because the profile was measured, used as a diagnostic,
and found to discriminate — and none of that licenses it as a *claim*. Until
now `s(r)` appeared nowhere in `spec/`, which made it a legitimate fitting
signal and nothing more. This fixes the statistic, the protocol and the bands
in advance so that a later match means something.

---

## 1. The statistic

For a corpus X and query set Q, with exact k-NN distances and `r(k)` the median
distance to the k-th neighbour:

```
s(r) = d log k / d log r(k)        the local growth dimension
```

`s` is the pre-limit form of **Local Intrinsic Dimensionality** (Houle, SISAP
2017), equivalently the continuous-radius generalisation of Karger–Ruhl
expansion dimension (STOC 2002) and the local slope of the Grassberger–Procaccia
correlation integral (1983). **It is not a new estimator and must not be
presented as one.** What is registered here is its use as a *curve* on a
retrieval-scale embedding corpus, and two summaries of that curve.

**Primary summary — the k-matched ratio and its trend:**

```
ratio(n) = s(k=500) / s(k=4)                    at corpus size n
trend    = d ratio / d ln n                     across the rung ladder
```

**Secondary summary — the intrinsic-dimension ladder:**

```
G1(n)        = TwoNN estimate at corpus size n
G1 exponent  = d log G1 / d log n
```

**Third summary — the density ladder (§3b):**

```
ratio(delta), G1(delta)    at FIXED n, with delta = n / pool
```

Both ladders above vary n at a fixed pool, so `delta` and `n` move together and
neither summary can say which is doing the work. §3b holds n fixed and varies
the pool, which separates them.

### Why the ratio and not beta

`beta = d log s / d log r` is **not** registered and must not be used for
cross-corpus comparison. It divides by each corpus's own log-radius span, and
corpora occupy disjoint bands with spans differing up to 6x — real at
r ∈ [0.86, 1.13], cascades at [1.27, 1.33], an isotropic Gaussian at
[1.32, 1.36]. That normalisation put a deep cascade 7% from real on beta while
a band-independent statistic put it 2x away (`R21B`, `R23`). The ratio is
matched in k, dimensionless, and does not divide by a corpus-dependent span.

---

## 2. The protocol — density is the controlled variable

1. **Pool:** a **contiguous** block of 600,000 rows. Contiguity is required, not
   incidental (§4).
2. **Queries:** 10,000 drawn uniformly from the pool as a holdout; base drawn
   uniformly from the remainder. Both must come from the *same* region — a
   non-exchangeable split moved measured G1 from 16.1 to 65.7 (`R23`).
3. **Rungs:** n = 25,000 / 50,000 / 100,000 / 200,000, each drawn uniformly
   from the base pool.
4. **Neighbours:** exact k-NN, k grid of 16 points log-spaced over 4…500, on
   L2-normalised vectors under the registered angular metric.
5. **Reported per arm:** `‖mean(X)‖` and effective rank, so any de-anisotropy or
   normalisation step is auditable rather than asserted (`R25`).

---

## 3. Registered target values

Measured across **four independent contiguous 600k blocks** at different corpus
offsets (`R24`), so the quoted uncertainty is real sampling variance rather than
a single-block point estimate.

| n | G1 (mean ± sd) | ratio (mean ± sd) |
|---|---|---|
| 25,000 | 26.62 ± 0.59 | 1.373 ± 0.099 |
| 50,000 | 23.04 ± 0.39 | 1.616 ± 0.056 |
| 100,000 | 20.53 ± 0.55 | 1.923 ± 0.087 |
| 200,000 | 18.71 ± 0.95 | 2.313 ± 0.123 |

| summary | mean | sd | **registered band (±2 sd)** |
|---|---|---|---|
| G1 exponent | −0.1696 | 0.0287 | **[−0.227, −0.112]** |
| ratio trend | +0.4512 | 0.0988 | **[+0.254, +0.649]** |

**Admission on this criterion requires both summaries inside their bands, and
the four per-rung ratios each within ±2 sd.** The bands are derived from
measured block-to-block variance; they were not chosen for convenience and must
not be widened after a candidate is seen.

### Discriminating power, for calibration

Every synthetic family measured to date sits far outside: |trend| ≤ 0.13 for
bit-cascades at two depths, an isotropic Gaussian, a low-rank null and a
Whitney-stratified corpus (`R21B`). A Gaussian carrying real's *exact* mean and
covariance gives +0.021 (`R25`). So the band is not trivially satisfiable.

---

## 3b. The density ladder — registered 2026-08-10

**Registered after §3 and after the R28 failure that motivated it, but before
any generator has been searched against it.** No candidate has been scored on
this criterion.

### Why a second ladder exists

§3 varies n at a fixed 600k pool, so a rung of n rows sits at density
`n/600k`: row count and density move together and `trend` is their *sum*. On a
factorial (n, pool) grid the two partials are large and opposite
(`results/density_grid.json`):

| response | ∂/∂log n | ∂/∂log density |
|---|---|---|
| ratio | −0.189 ± 0.176 (1.1σ) | **+0.844 ± 0.137 (6.1σ)** |
| log G1 | +0.073 ± 0.037 (2.0σ) | **−0.217 ± 0.029 (7.6σ)** |

So the registered `trend` of +0.451 is a near-cancellation of two larger terms,
and **G1 is, to measurement accuracy, a function of density alone** — its
row-count partial is consistent with zero. A family can land the lumped trend at
one operating point with both components wrong. That is exactly what the
filament family did: it fit at 91% rung/pool density and inverted the G1
exponent's sign at the registered 17% (`R28`, closing section).

### Protocol

As §2, with one change: **n is fixed at 25,000** and the pool varies over
50,000 / 100,000 / 200,000 / 400,000 / 600,000, giving densities 0.500 / 0.250 /
0.125 / 0.0625 / 0.0417. The holdout of 10,000 is drawn **from within each
pool**, never once from the largest — a single global holdout leaves the base a
head-slice of a corpus whose queries span all of it, the non-exchangeable split
of `R23`. It inflates G1 roughly 2x at the smallest pool and does so
monotonically, so the artifact reads as a clean density trend and is not
self-announcing (it was committed and caught during this measurement).

### Registered target values

Four independent contiguous 600k blocks at corpus offsets 0 / 10M / 20M / 30M
(`results/density_ladder.json`, `R29`), n = 25,000 throughout:

| density | pool | ratio (mean ± sd) | G1 (mean ± sd) |
|---|---|---|---|
| 0.5000 | 50,000 | 3.722 ± 0.074 | 16.27 ± 0.58 |
| 0.2500 | 100,000 | 2.582 ± 0.144 | 17.08 ± 0.39 |
| 0.1250 | 200,000 | 1.774 ± 0.068 | 19.52 ± 0.36 |
| 0.0625 | 400,000 | 1.464 ± 0.018 | 23.62 ± 0.24 |
| 0.0417 | 600,000 | 1.325 ± 0.026 | 26.66 ± 0.56 |

| summary (fixed endpoints 0.500 vs 0.0417) | mean | sd | **band (±2 sd)** |
|---|---|---|---|
| ratio span | +2.397 | 0.085 | **[+2.227, +2.567]** |
| log G1 span | −0.494 | 0.054 | **[−0.602, −0.386]** |

**Admission on this criterion requires both spans inside their bands and the
five per-density values each within ±2 sd.**

### Why a contrast and not a fitted slope

The response is strongly convex — the local slope of ratio against log density
runs +0.41, +0.46, +0.98, +1.79 across the four intervals. A slope fitted over
the ladder would therefore depend on which pools were chosen, which is the same
span dependence that disqualified `beta` in §1. The endpoints here are part of
the definition, so the contrast has no such freedom. A contrast over a shorter
span is a *different quantity*, not a noisier estimate of this one.

### Discriminating power — this criterion is structural

For any generator that emits rows **i.i.d.**, density is not a variable: n rows
drawn from a pool of 50,000 or of 600,000 are identically distributed, so both
spans are exactly zero up to sampling noise. No parameter setting changes this.
Real embeddings have a ratio span of +2.397 ± 0.085 — a ~28σ separation.

This is the first registered criterion that **excludes a whole construction
class a priori** rather than by measurement. It is only satisfiable by
generators whose geometry rests on finite *shared* structure that subsampling
genuinely thins — a fixed set of centres, threads or latents — because only then
does a pool exist to be dense or sparse in. Measured controls at the registered
protocol are in `R29`.

---

## 4. Scope conditions — where the target is and is not defined

These are registered as limits, not caveats to be relaxed later.

* **Density, not row count.** The target is defined for a *dense* contiguous
  sample. Drawing 600k rows uniformly from 41M (1.5% density) collapses the
  ramp to −0.003 and doubles G1 to ≈49 (`R24`). Subsampling a large corpus does
  not produce a smaller corpus of the same geometry — this is
  `CAPACITY_CONJECTURE.md` C3 measured directly. Any comparison between corpora
  must hold density fixed. §3b makes this quantitative: at *fixed* row count,
  varying density alone moves the ratio 2.8x and G1 1.6x, and on a factorial
  grid the row-count partial is not significant for the ratio at all. Density is
  the primary variable of this profile and row count is close to incidental.
* **Position-independent.** Four offsets across 41M rows reproduce the target
  within the sd above, so the head is an arbitrary but harmless choice (`R24`).
* **Not an anisotropy restatement.** Anisotropy is neither sufficient (exact-
  covariance Gaussian: +0.021) nor necessary (whitened real: +1.030; all-but-the
  -top: +0.624) (`R25`). The ramp is carried by structure beyond the first two
  moments — so any family whose geometry is determined by its covariance is
  excluded a priori.
* **Model-dependent in magnitude.** Cohere Embed-V3 +1.045, BGE-M3 +0.592,
  LeBSE-v1 +0.267, LaBSE +0.072 under a common protocol (`R23`). The registered
  target is Cohere Embed-V3 specifically; it is the strong end of the observed
  range, not a typical encoder value.

---

## 5. Falsifiers

The profile criterion should be considered unsound if any of these holds.

* **P1.** A fifth and sixth contiguous block fall outside the ±2 sd bands —
  the quoted variance would be an underestimate from n = 4.
* **P2.** The ratio trend proves sensitive to the k grid (4…500) such that a
  different grid reverses the ordering between real and the synthetic controls.
* **P3.** A corpus matching the eight registered gates within band is found that
  misses the profile bands, *and* is shown to be operationally equivalent for
  ANN search — which would make the profile a descriptor without consequence.
* **P4.** Real embeddings from three further encoders all fall outside the
  bands, making the target a property of one model rather than of embedding
  geometry.
* **P5.** The §3b spans prove sensitive to the fixed row count: measuring the
  density ladder at n = 50,000 instead of 25,000 moves either span outside its
  band. The spans are registered at n = 25,000 and are claimed only there, but a
  quantity that swings with an arbitrary protocol choice is a weak target even
  so.
* **P6.** An i.i.d. row generator is found with a non-zero §3b span. This should
  be impossible by construction — such rows are identically distributed
  regardless of pool size — so it would indicate the span is measuring an
  artifact of the subsampling procedure rather than corpus structure. The
  measured i.i.d. controls in `R29` are the standing check on this.

---

## 6. Status of any match

**A profile match is a fitting signal, not a verdict.** This criterion may be
optimised against during generator search, and any such search must disclose its
budget under `GENERATOR_SEARCH.md` §5.3. The verdict remains RC-2, opened once,
against a generator frozen and hashed beforehand. Passing §3 licenses exactly
one sentence: *the generator reproduces the registered scale-resolved dimension
profile of Cohere Embed-V3 on dense Wikipedia text across the registered ladder.*
