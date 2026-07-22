# The Bond Metric — a measure–metric–scale decomposition of embedding geometry

*Working conjecture + operational programme, 2026-07-22. Status: conjecture with first
empirical support; not yet a registered spec (nothing here gates RC-1/RC-2).*

## The conjecture

High-dimensional embedding geometry factors into (at least) three distinct degrees of
freedom that standard summary statistics conflate:

1. **Measure layer** — where probability mass sits: sampling density over the manifold,
   *and separately* the query marginal's mass over the corpus (they need not agree).
2. **Metric layer** — the scale structure: neighbour-distance quantiles, the across-query
   d10 window, ball-growth behaviour through intermediate scales.
3. **Spectral layer** — the global covariance shape: effective rank, dims90, PCA capture.

**Apparent trade-offs between embedding statistics arise when a generator (or a model's
representation) binds several layers to one mechanism — not because the statistics are
intrinsically incompatible.** Corollary: a statistic's *value* underdetermines its
*anatomy*; two corpora can share a gate reading produced by different layers.

## Evidence so far (all from the generator-search campaign, results/ this repo)

- **Round 5:** Zipf codebook hierarchy = one mechanism for angular hubs *and* the global
  spectrum → clean two-ended G6 × G3 Pareto frontier, nothing in the middle. Round 6
  split the mechanisms (placement vs Mahalanobis recolouring) → the "trade-off" vanished;
  first five-gate joint match. *Same statistics, unbound.*
- **Hub anatomy (`diag_hubs.json`):** real corpus vs round-6 winner, same-order battery-B
  G6, opposite anatomy. Real: base→base skew ≈1.5, max reverse-count 78, density-driven
  (rank-corr(N₁₀, −d10) = +0.67), hubs' d10 only 8% under population. Round-6 winner:
  skew 7.0, max count **369**, extreme-centrality metric-layer hubs 34% closer than
  population. **The G6 gate cannot distinguish these; the decomposition can.**
- **Round 7 diagnosis:** real's battery-B hubness (6.8) lives in the **query marginal**
  (measure layer, query side); its corpus is metrically homogeneous (d10 window ≈1.17 —
  which *is* G2 ≈ 15). Six corpus-side hub mechanisms failed because they attacked the
  wrong layer; a Zipf query model moved G6 0.19×→2.20× with the metric layer untouched.
- **Amplification:** in high local dimension the measure layer is exponentially sensitive
  to the metric layer (count contrast ~ s^-d_local), so tiny metric perturbations produce
  large measure signatures — why binding the layers is both easy to do and expensive.

## Operational programme ("Fuzzing the Bond Metric")

Replace the scalar fitness with a **coverage signature** — the structural-fuzzing move,
applied to corpus space:

C = (d_M-quantile band, N_k-quantile band, local density, local ID, ball-growth slope,
angular basin size, spectral band)

A generated corpus is *retained* when it enters a previously empty cell or expands a
cell's boundary. The fuzzer then discovers separations by construction:

- same Mahalanobis centrality, different hubness;
- same hubness, different effective rank;
- same centrality and hubness, different ball growth;
- same exact geometry, hubs destroyed (or created) by quantization;
- hubs stable at one k, gone at another;
- hub configurations that break a specific ANN implementation.

**Differential system testing.** Each retained corpus is a test vector across: exact kNN
vs HNSW / DiskANN / FAISS / cuVS; fp32 vs TurboQuant-Pro operating points; cosine vs
Euclidean; graph build orders; sharding strategies. Oracles: (a) hub-rank divergence,
`hub_rank_exact ≉ hub_rank_approx`; (b) aggregate recall fine but **anti-hub queries fail
catastrophically** (the tail the mean hides — the same blindness cosine-acceptance has in
turboquant-pro). The round-7 P2 falsifier (gate value must come from the right layer) is
the first registered use of the decomposition.

## Candidate papers

1. *The Bond Metric: Breaking Apparent Trade-offs in High-Dimensional Embedding Geometry*
   — the decomposition + the rounds 5–7 falsification chain as evidence.
2. *Fuzzing the Bond Metric* — the coverage signature + differential ANN testing harness.

Relation to existing work to position against: hubness-as-centrality literature
(Radovanović et al.), query/corpus distribution shift in IR, and this repo's registered
gates (the decomposition explains *why* eight scalar gates underdetermine anatomy).
