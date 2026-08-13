# The dimension profile of an embedding corpus measures how the corpus was assembled, not how it was embedded

**Draft, 2026-08-13.** Sources are the `results/` rounds cited inline; every
number below is measured in this repository and its record is named.

---

## Abstract

Retrieval-scale text-embedding corpora show a pronounced *scale-resolved
dimension profile*: the local growth dimension `s(r) = d log k / d log r(k)`
rises with radius, so that `s(500)/s(4) ≈ 4` on Cohere Embed-V3 over Wikipedia.
It is natural to read this as a property of the embedding — evidence of nested
semantic manifolds, or of a model-specific geometry.

We show it is not. The profile is a **two-population mixture created by corpus
assembly**: a row's nearest neighbours are ~23 passages from its own article,
after which neighbours are drawn from the whole corpus, and the ramp is the
crossover between those populations. Three findings establish this.

1. **The profile responds to sampling density, not corpus size** — the same
   corpus at 1.5% density loses the ramp entirely and doubles its intrinsic
   dimension.
2. **Density is a proxy for index adjacency.** Holding corpus span and row count
   fixed and varying only how *clumped* the sample is reproduces the entire
   density ladder. A single adjacent row moves the TwoNN dimension from 26.1 to
   14.1.
3. **The adjacency budget is finite and small.** At k = 500 only 22.7 of 500
   neighbours are index-local, and that count saturates.

Two consequences follow. Any generative model whose rows are i.i.d. has *zero*
density response by construction, so the profile is unreproducible by such a
model at any parameter setting — a structural exclusion, not an empirical one.
And profile comparisons between corpora are only meaningful at matched sampling
density and matched ordering; the literature's practice of comparing intrinsic
dimension across corpora of different provenance is not well defined without
them.

We close the loop constructively: a registered, budget-disclosed search over
deterministic sequence-structured generators produced a frozen, bit-exact,
random-access family that — judged once, on held-out corpus blocks — matches
the fixed-density neighbourhood geometry (intrinsic dimension and distance
contrast in band; hubness within 1.4%) and is excluded by precisely the
density-response criteria the assembly explanation identifies as the hard
part. The negative is registered, held-out, and quantified.

---

## 1. The statistic, and what is not new about it

For a corpus `X` and query set `Q` with exact k-NN distances, let `r(k)` be the
median distance to the k-th neighbour and

```
s(r) = d log k / d log r(k)
```

`s` is the pre-limit form of **Local Intrinsic Dimensionality** (Houle, SISAP
2017), equivalently the continuous-radius generalisation of the Karger–Ruhl
expansion dimension (STOC 2002) and the local slope of the Grassberger–Procaccia
correlation integral (1983). **It is not a new estimator and we do not present
it as one.** What is registered here (`spec/PROFILE.md`) is its use as a *curve*
on a retrieval-scale corpus, and two summaries: the k-matched ratio
`s(500)/s(4)` and its trend in `ln n`.

We deliberately do **not** use `β = d log s / d log r`. It divides by each
corpus's own log-radius span, and corpora occupy disjoint bands with spans
differing up to 6× — real at r ∈ [0.86, 1.13], bit-cascades at [1.27, 1.33], an
isotropic Gaussian at [1.32, 1.36]. That normalisation placed a deep cascade 7%
from real while a band-independent statistic placed it 2× away (`R21B`, `R23`).

---

## 2. The observation

On Cohere Embed-V3 (1024-d) over Wikipedia, four independent contiguous 600k
blocks at different corpus offsets give (`R24`, `spec/PROFILE.md` §3):

| n | G1 (TwoNN) | ratio `s(500)/s(4)` |
|---|---|---|
| 25,000 | 26.62 ± 0.59 | 1.373 ± 0.099 |
| 50,000 | 23.04 ± 0.39 | 1.616 ± 0.056 |
| 100,000 | 20.53 ± 0.55 | 1.923 ± 0.087 |
| 200,000 | 18.71 ± 0.95 | 2.313 ± 0.123 |

with summaries `ratio trend +0.4512 ± 0.0988` and
`G1 exponent −0.1696 ± 0.0287`. The uncertainties are block-to-block, not
single-block point estimates.

### 2.1 Four challenges, defeated

* **Estimator bias.** Constant-dimension nulls move G1 *upward* with n; real
  falls at −0.168 (`R21B`).
* **Head sampling.** Four contiguous blocks across 41M rows reproduce the target
  within the sd above, so the head is arbitrary but harmless (`R24`).
* **Anisotropy.** Neither sufficient nor necessary: a Gaussian carrying real's
  *exact* mean and covariance gives trend +0.021; whitened real gives +1.030 and
  all-but-the-top gives +0.624 (`R25`). The ramp is carried by structure beyond
  the first two moments.
* **Model specificity.** Four of five encoders show it, graded: Cohere +1.045,
  BGE-M3 +0.592, e5-large +0.582, e5-base +0.523, LeBSE-v1 +0.267, LaBSE +0.072
  (`R23`).

### 2.2 It is training, not architecture

The graded encoder result invites a dimensional reading — wider embeddings, more
ramp. It is wrong. At fixed family and training, doubling width changes the ramp
11% (e5-base 768 → +0.523, e5-large 1024 → +0.582); at **fixed** 768 width,
training regime moves it 7× (LaBSE +0.072 → e5-base +0.523) (`R23`).

---

## 3. Density, not row count

The target is defined for a *dense contiguous* sample. Drawing 600k rows
uniformly from 41M — 1.5% density, identical row count — collapses the ramp to
−0.003 and doubles G1 to ≈49 (`R24`).

A factorial design in (row count, density) separates the two
(`results/density_grid.json`):

| response | ∂/∂log n | ∂/∂log density |
|---|---|---|
| ratio | −0.189 ± 0.176 (1.1σ) | **+0.844 ± 0.137 (6.1σ)** |
| log G1 | +0.073 ± 0.037 (2.0σ) | **−0.217 ± 0.029 (7.6σ)** |

**G1 is, to measurement accuracy, a function of density alone.** The registered
trend of +0.45 is a near-cancellation of two larger opposing terms, which is why
a model can match the lumped statistic with both components wrong.

Holding row count fixed at 25,000 and varying only the pool
(`results/density_ladder.json`, four blocks):

| density | ratio | G1 |
|---|---|---|
| 0.500 | 3.722 ± 0.074 | 16.27 ± 0.58 |
| 0.250 | 2.582 ± 0.144 | 17.08 ± 0.39 |
| 0.125 | 1.774 ± 0.068 | 19.52 ± 0.36 |
| 0.0625 | 1.464 ± 0.018 | 23.62 ± 0.24 |
| 0.0417 | 1.325 ± 0.026 | 26.66 ± 0.56 |

Row count is identical in every row of that table. The ratio still moves 2.8×.

---

## 4. Density is a proxy for adjacency

The central result. Hold the corpus **span** at 600,000 rows and the row count at
25,000, and vary only how clumped the draw is: the 35,000-row support is taken
as `⌈35000/b⌉` runs of `b` contiguous rows, then split exchangeably
(`results/clumpiness.json`).

| clumped, span 600k | ratio | G1 | | window ladder | ratio | G1 |
|---|---|---|---|---|---|---|
| b = 1 | 1.282 | 26.09 | | W = 600,000 | 1.309 | 26.60 |
| b = 100 | 4.050 | 15.85 | | W = 35,000 | 4.090 | 16.54 |

**The two ladders trace the same curve.** Shrinking the pool mattered only
because it forces adjacent rows into the sample. At fixed span, clumping the
draw into runs of ten reproduces the dense geometry outright.

The transition is sharp: going from **no** adjacent neighbour to **one**
(b = 1 → 2) drops G1 from 26.09 to 14.06 and lifts μ = r₂/r₁ from 1.029 to
1.056. It saturates by b ≈ 25.

### 4.1 The corpus is ordered, and the order carries the effect

A Wikipedia corpus is ordered by article. Mean cosine between rows at index gap
`g`, against a random-pair baseline of 0.2279 (`results/density_ordering.json`):

| gap | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 |
|---|---|---|---|---|---|---|---|---|
| cos | 0.598 | 0.530 | 0.449 | 0.367 | 0.304 | 0.267 | 0.246 | 0.236 |

A correlation length of roughly 100 rows, decaying smoothly to baseline.

---

## 5. The adjacency budget is finite

k-NN index gaps on a plain contiguous 200k block
(`results/nn_index_gap.json`):

| k | 1 | 4 | 8 | 16 | **32** | 100 | 500 |
|---|---|---|---|---|---|---|---|
| median \|Δindex\| | 3 | 5 | 9 | 55 | **14,880** | 39,095 | 52,340 |
| fraction \|Δ\| ≤ 128 | 0.862 | 0.769 | 0.661 | 0.519 | 0.369 | 0.176 | 0.045 |

There is a cliff between k = 16 and k = 32. Below it neighbours are index-local;
above it they are scattered across the corpus. **At k = 500 only 22.7 of 500
neighbours are index-local, and that count stops growing.**

So a row's neighbourhood is a two-population mixture: ~23 same-article
neighbours, then the global cloud — and `s(k)` climbs 8.82 → 35.73 across
exactly the k = 16–32 crossover.

### 5.1 The two populations are one cloud, not two manifolds

Measuring the full curve in both regimes (`results/scurves.json`):

| k | 4 | 8 | 14 | 28 | 53 | 100 | 263 | 500 |
|---|---|---|---|---|---|---|---|---|
| no adjacent rows | 27.40 | 30.74 | 33.82 | 36.32 | 37.02 | 37.69 | 36.95 | 35.13 |
| whole articles | 8.82 | 11.46 | 16.08 | 23.40 | 28.88 | 31.29 | 34.82 | 35.73 |

**They converge** (35.13 vs 35.73 at k = 500). Real's large-k dimension is ~36
regardless of how the corpus is sampled; same-article neighbours drop `s(4)`
from 27.4 to 8.8 and leave `s(500)` untouched. The corpus is one ~36-dimensional
cloud carrying a ~9-dimensional local structure that appears only when adjacent
rows are present.

This corrects a natural but wrong reading of the TwoNN values (16 and 26) as two
manifold dimensions. G1 is a k = 1,2 statistic; it reads the finest scale, not
the manifold.

---

## 6. Consequence: i.i.d. models are excluded structurally

For a generative model whose rows are **i.i.d.**, density is not a variable at
all: `n` rows drawn from a pool of 50,000 and from a pool of 600,000 are
identically distributed, so the density response is exactly zero and no parameter
setting changes it. Adjacency is a property of the row *sequence*, which i.i.d.
emission does not have.

Measured against real's ratio span of **+2.397 ± 0.085**
(`results/density_controls.json`):

| family | ratio span | log G1 span |
|---|---|---|
| **real** | **+2.397 ± 0.085** | **−0.494 ± 0.054** |
| i.i.d. isotropic Gaussian | −0.015 | +0.025 |
| i.i.d. Gaussian, real's exact mean + covariance | −0.004 | −0.002 |

A ~28σ separation, and the exact-covariance control is the sharper of the two:
carrying real's first two moments exactly buys nothing.

---

## 7. Consequence: cross-corpus dimension comparisons need matched protocol

The profile is a joint property of the embedding, the sampling density, and the
corpus ordering. Reporting an intrinsic dimension for a corpus without fixing
the latter two does not identify a property of the embedding. Concretely, the
same Cohere/Wikipedia corpus yields ratios from 1.29 to 4.09 — a 3.2× range —
purely by changing how rows are drawn, with the embedding model and the row
count held fixed.

We register the protocol we use (`spec/PROFILE.md` §2, §3b) rather than
proposing it as a standard: a contiguous 600,000-row pool, 10,000 queries drawn
as a uniform holdout *from within that pool*, rungs drawn uniformly from the
remainder, exact k-NN on L2-normalised vectors over a 16-point log grid on
4…500.

The holdout construction is not incidental. Drawing queries from a different
region than the base inflates every neighbour diagnostic — it moved measured G1
from 16.1 to 65.7 (`R23`) — and it recurred three times in this work because it
produces smooth, monotone, entirely plausible numbers. It is now constructed
once in `geometry.exchangeable_split()`.

---

## 8. Reproducibility of the artifact

The measurements above are only useful if the corpus they describe can be
redistributed exactly. Two results support that.

**Reconstruction.** A corpus published at 10⁷ rows, with every materialised
source deleted and only a signed root manifest retained, reconstructs from a
mixture of regeneration, cache and mirror with every shard verifying against its
Merkle root, byte-identical shards, identical index results on a fixed query
set, and a corrupted chunk detected and rejected (`R22`).

**Cross-toolchain regeneration.** Sixteen shards at indices 0 to 10¹² regenerate
byte-identically across Windows/numpy 2.3.5 and Linux glibc 2.39/numpy 2.4.4 —
a 100% success rate (`results/xtoolchain.json`). This holds structurally: the
emitter is pure integer arithmetic over a counter-based bit generator.

The qualifier matters for anyone reproducing this work. A float32 matrix product
is **not** bit-reproducible across platforms — same OpenBLAS build, Windows vs
Linux, identical inputs, different output — because SIMD width and blocking
reorder the inner sum and float32 cannot absorb it (`R48`). Reductions must be
ordered explicitly or carried in float64.

---

## 9. Limits

* **One corpus, one primary encoder.** The registered target is Cohere Embed-V3
  on dense Wikipedia. §2.1 shows four other encoders share the phenomenon and
  §2.2 shows the magnitude tracks training rather than width, but the constants
  (~23 index-local neighbours, ~100-row correlation length) are Wikipedia's.
* **Article structure is inferred, not annotated.** The ~23 figure is read off a
  k-NN index-gap cliff, not from article boundaries in the source data. We did
  not have the article metadata.
* **The block-to-block uncertainties came from four blocks, and the
  registered falsifier has since fired in part.** `spec/PROFILE.md` §5
  registered that further blocks falling outside the ±2 sd bands would show
  the quoted variance is an underestimate from n = 4. Four held-out blocks
  at fresh offsets (`results/rc2_heldout.json`, §11) confirm this for some
  statistics: hubness skew moved from 1.696 to a fresh-block band of
  [1.711, 1.748], and the ratio-trend band from [0.254, 0.649] to
  [0.455, 0.658] — the corpus's own block-to-block drift is comparable to
  several admission windows. The intrinsic-dimension and contrast bands
  held. Bands in any future registration should come from 8–10 blocks.
* **No generative model reproducing the full profile is offered — and the
  best one is now a registered, held-out negative rather than an open
  question** (§11). The frozen family matches the fixed-density
  neighbourhood geometry on held-out data (intrinsic dimension and distance
  contrast in band; hubness, PCA retention and effective rank within 1–3%)
  and fails precisely the density-response criteria this paper attributes
  to corpus assembly. The summary statistic remains satisfiable by geometry
  that is not real's; the *density response* was not satisfiable by
  anything this search found.

---

## 10. The permutation control

The claim is that the profile is produced by index-adjacency structure in the
corpus rather than by the embedding. The direct test is to destroy the adjacency
and leave every embedding vector untouched: shuffle the row order and re-measure
under the identical protocol (`results/permutation.json`).

| corpus | b | ratio | G1 | s(4) | s(500) |
|---|---|---|---|---|---|
| ordered | 1 | 1.282 | 26.09 | 27.40 | 35.13 |
| **ordered** | **100** | **4.050** | **15.85** | **8.82** | 35.73 |
| permuted | 1 | 1.333 | 26.00 | 27.09 | 36.12 |
| **permuted** | **100** | **1.281** | **26.48** | **27.97** | 35.82 |

| corpus | §3b ratio span | §3b log G1 span |
|---|---|---|
| registered target | +2.397 ± 0.085 | −0.494 ± 0.054 |
| ordered | +2.524 | −0.473 |
| **permuted** | **+0.012** | **+0.004** |

**The ramp disappears.** At b = 100 — whole articles present — the ordered corpus
gives a ratio of 4.050 and the permuted corpus 1.281, which is the ordered
corpus's *no-adjacent-neighbour* value. Both registered §3b spans collapse to
zero: +2.524 → +0.012, and −0.473 → +0.004.

Not one embedding vector changed. Only their order did.

This is the cleanest available confirmation that the profile is a property of
corpus assembly. It also shows the permuted corpus behaves exactly like the
i.i.d. controls of §6 — spans at zero — which is what the structural argument
there predicts, since shuffling makes the row sequence carry no information.

### Further falsifiers
* An **unordered** corpus — one whose row order carries no semantic relation,
  such as a shuffled web crawl — should show no ramp at any density.
* Conversely, a corpus with *stronger* document-level clumping than Wikipedia
  should show a *larger* ramp at matched density.

---

## 11. The constructive test: a generator search, frozen and judged held-out

If the profile is created by corpus assembly, a generator that *builds in*
the assembly — contiguous articles, segments, an ordered row sequence —
should reproduce what i.i.d. emission structurally cannot. We ran that
search to a registered conclusion: a five-phase campaign of 116 full-panel
arms (`RC1_PLAN.md`, `R62`–`R66`; ~200+ configuration evaluations across
the wider arc, all disclosed in `spec/RC2_FREEZE.md` §4), ending in a
frozen, bit-exact, random-access generator
(`openvector_bench.segment_corpus`) evaluated **once** against four
held-out real blocks at offsets no round had touched
(`results/RC2_VERDICT.md`).

Three mechanisms were found, each moving a statistic nothing else moved:
the within-segment level-variance **decay with an unstructured per-row
ball** is the intrinsic-dimension lever (4.4 → 16.3 against real's ~17);
**keyed sharing of direction sets across neighbourhoods** is the hubness
lever; and **per-level arrangement frames** — giving each coarse
organisational scale its own subspace instead of one shared low-rank frame
— is what lets the ratio *trend* enter its band, seed-robustly. The last
is the interesting one: a single shared frame is a hard ceiling on
coarse-scale dimension, and every density-response failure of the
single-frame family pointed at it coherently.

The held-out verdict is the paper's thesis read back from the generative
side. The frozen family lands the **fixed-density neighbourhood geometry**
on data it never saw — TwoNN dimension 16.31 against a held-out band
[15.0, 19.1], distance contrast 1.377 in [1.362, 1.397], hubness, PCA
retention and effective rank within 1–3% of their bands — and is excluded
by exactly the **density-response** criteria of §3–§6: the five-pool
ladder's spans and levels, and the four-rung trend against the held-out
band. The static snapshot of the cloud is constructible; how the geometry
moves as sampling thins is what no configuration reached, and the
campaign's error bars say why: the spans' generation-seed variance is 4×
their admission window — a property of the family, not a tuning gap.

Two incidental findings deserve record. First, an early port of the frozen
family accidentally ran a controlled experiment: changing *only* the
article-length law and the cluster-assignment rule — no vector-construction
parameter — moved `s(14)` from 16.6 to 38.3 and hubness skew from 1.77 to
2.43 (`RC2_FREEZE.md` §6). The "bookkeeping" of corpus layout carries as
much of the geometry as the embedding construction, which is this paper's
claim in miniature. Second, the held-out blocks moved some of real's own
targets (§9), so part of the residual mismatch is real-vs-real drift, not
generator-vs-real error.

The search's discipline is part of the result: the configuration was frozen
with its byte hash, expected outcome and full search budget declared before
the held-out data was touched, and the verdict — exclusion — is reported
under the freeze's own pre-stated rule. The profile's density response
remains unreproduced by any known deterministic generator, now as a
registered negative with quantified misses rather than an absence of
attempts.

A second campaign (RC-3, 60 arms, `results/R68`–`R74`) revised that
statement upward under bands that respect real's measured heterogeneity —
ten fresh blocks showed the corpus's own density response varies 2.4×
block-to-block, with weakly-articulated regions (g1 ≈ 20, span ≈ 1)
alongside strongly-articulated ones. One added mechanism (a power-law
amplitude profile over the shared direction pool) and one relocated break
rate produced a configuration that, frozen and evaluated once on four
further untouched blocks, passes **eight of ten** registered criteria —
including the mandatory intrinsic-dimension / contrast / hubness trio,
in band held-out for the first time, and the ratio trend and both §3b
spans. The two residuals are precise: dims90 (417 vs real's razor-stable
352–365) and the G1-vs-n exponent (−0.11 vs −0.17). The constructive
statement now reads: sequence-structured generation reproduces both the
fixed-density geometry and the leading density-response summaries; what
still resists is the exact PCA tail shape and the rate at which dimension
falls with sample size (`results/RC3_VERDICT.md`).
