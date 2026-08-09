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

## 4. Scope conditions — where the target is and is not defined

These are registered as limits, not caveats to be relaxed later.

* **Density, not row count.** The target is defined for a *dense* contiguous
  sample. Drawing 600k rows uniformly from 41M (1.5% density) collapses the
  ramp to −0.003 and doubles G1 to ≈49 (`R24`). Subsampling a large corpus does
  not produce a smaller corpus of the same geometry — this is
  `CAPACITY_CONJECTURE.md` C3 measured directly. Any comparison between corpora
  must hold density fixed.
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

---

## 6. Status of any match

**A profile match is a fitting signal, not a verdict.** This criterion may be
optimised against during generator search, and any such search must disclose its
budget under `GENERATOR_SEARCH.md` §5.3. The verdict remains RC-2, opened once,
against a generator frozen and hashed beforehand. Passing §3 licenses exactly
one sentence: *the generator reproduces the registered scale-resolved dimension
profile of Cohere Embed-V3 on dense Wikipedia text across the registered ladder.*
