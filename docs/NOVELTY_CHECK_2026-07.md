# Literature / novelty check — five-angle sweep (2026-07-24)

**Method.** Five independent search agents, one per angle (intrinsic-dimension estimation ·
ANN benchmarking/OOD · synthetic geometry-matched generation · hubness/LID/relative-contrast
difficulty measures · two-sample NN-distance theory), ~60 targeted searches + full-text fetches
of the load-bearing sources, coverage through 2026. Verification: the load-bearing *positive*
claims below were confirmed by full-text fetch (marked ✔); the *negative* (novelty) claims rest
on convergent absence across all five independent sweeps. One coverage hole is flagged at the end.

## Verdicts

### V1 — The query-coupling finding (queries from a different realization mis-measure ID/difficulty): **NOVEL, with a mandatory mechanism statement**

- No paper, survey, or tutorial states or tests a within-sample vs cross-sample asymmetry for
  TwoNN/MLE-class ID estimators. The field's own 2025 eight-estimator survey (arXiv:2509.15517,
  §2.7/§4.1.5 ✔) evaluates every estimator with one dataset as both query and reference.
- He–Kumar–Chang (ICML 2012, relative contrast — the founding difficulty-measure paper) assumes
  ✔ "xi, q ∈ R^d are i.i.d samples from an unknown distribution p(x)": the cross-realization
  regime is *outside the founding model*, not a rejected case.
- Aumüller–Ceccarello (EDML19 ✔ / Inf. Systems 2021): queries are always same-sample splits;
  their Q1 robustness result (random splits behave consistently) is the *complementary* finding —
  within-realization splits are stable, which is exactly what makes the cross-realization
  instability a result.
- **Mandatory mechanism statement (three agents converged on this):** the ambient-dimension
  readout is a finite-sample, off-the-empirical-cloud phenomenon. For a *fixed shared support*,
  NN-radii theory (Houle LID framework; arXiv:2605.14343, 2026) predicts the intrinsic readout
  even for near-support queries — so the effect requires the query to lie off the corpus
  realization's support (re-drawn manifold/embedding per realization, or transverse noise), and
  it vanishes asymptotically on a genuinely shared continuous manifold. The paper must define
  "independent realization" as re-drawn manifold/embedding (which is what our generators do),
  not re-drawn points on a fixed manifold. Positioned this way the claim is safe; positioned as
  a property of manifolds it is refutable.
- Partial precedents to cite and distinguish (they supply the mechanism in fragments, never the
  statement): Facco et al. 2017 noise→ambient drift + decimation mitigation · multiscale-SVD
  noisy-manifold crossover (Little/Maggioni; s41598-019-53549-9) · adversarial/OOD LID reads
  high (Ma et al. ICLR 2018; Kamkari et al. ICML 2024) · LID as query-relative quantity
  (Amsaleg et al. KDD 2015).

### V2 — Geometry-matched synthetic corpus generation: **GAP CONFIRMED (twice, independently)**

- Nobody procedurally generates synthetic embedding corpora matched to multiple measured
  geometric diagnostics (ID + effective rank + hubness + relative contrast jointly), at any
  scale. The field diagnosed the premise — VIBE ✔ (arXiv:2505.17810): legacy datasets "no longer
  representative"; Milvus/VDBBench: "benchmarks lie" — and universally resolved it by *using
  real embeddings*, which does not scale to trillion-vector regimes. Nobody names
  geometry-matched synthesis as an open problem; the framing is unclaimed.
- Closest non-overlapping cousins: embedding-space GAN/diffusion (augmentation/privacy; never
  validated on geometric diagnostics; never for ANN benchmarks) · skdim `BenchmarkManifolds`
  (Hein–Audibert / Campadelli suites: known-ID manifolds for benchmarking *estimators*, single
  controlled diagnostic) · legacy `random-*` datasets (the disowned baseline).
- **No hubness-aware generator exists.** Hubness is always emergent (Radovanović JMLR 2010
  onward), measured but never dialed. A generator with a hubness knob is novel on its own; the
  SIGMOD 2026 hubness-lens paper (10.1145/3802120 — hubness as "the fundamental cause of
  performance instability" in graph ANNS; anti-hub queries are the latency tail) is the
  ready-made motivation citation.

### V3 — OOD-query prior art (must distinguish, not claim): **WELL-DEVELOPED, ADJACENT**

Cross-*modal* query/base mismatch is a named benchmark category since 2021: NeurIPS'21/'23
Big-ANN OOD tracks (arXiv:2205.03763, 2409.17424), OOD-DiskANN (2211.12850: ≥10× latency at
fixed recall; 1% sample queries at build recovers 40%), RoarGraph (VLDB 2024, 2408.08933 —
closest geometric characterization: OOD queries 2.1–11.3× farther from their NNs), VIBE OOD
datasets. All of it is engineering-performance framing on *genuinely different distributions*;
none of it treats the query set as an estimator whose sampling scheme can invalidate ID/difficulty
inference. Cite RoarGraph + Aumüller–Ceccarello as nearest prior art for V1 and draw the line
explicitly.

### V4 — Real-embedding geometry defies i.i.d. concentration (supporting citation)

arXiv:2410.05752 / DASFAA 2025: random vectors reach RC → 1 by ~512–768 dims, but real text
embeddings hold RC ≈ 1.75–2.05 up to 12,288 dims — their synthetic baseline is plain Gaussian
with uncontrolled ID. Direct motivation for geometry-matched generation and for reporting RC as
a matched diagnostic.

## Coverage caveats (honest accounting)

- Angle 3 (generation) was rate-limit truncated: copula-based generators, GenAI-bench-style
  work, and 2025–26 preprint sweeps were not probed. Angle 2's independent sweep partially
  covers this hole (its Q3 also found nothing), so the gap claim is *moderately strong ×2*, not
  exhaustive. A camera-ready pass should run the copula query.
- Negative claims are absence-of-evidence across ~60 queries by five independent agents;
  positive load-bearing claims were full-text verified (marked ✔).

## One-line dispositions for the paper

- Finding #1 (query coupling): claim as novel; cite V1's four partial precedents; include the
  mechanism statement verbatim in the limitations; distinguish V3's OOD line in related work.
- Generator: claim the open-problem framing (V2) and the hubness knob as first; use VIBE +
  VDBBench + SIGMOD-2026 hubness lens as the motivation triad; V4 as the realism evidence.
