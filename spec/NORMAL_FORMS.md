---
registered: 2026-07-22
status: v1 research plan (registered; WP0 in progress)
provenance: authored from the query-coupling anomaly (results/QUERY_COUPLING_ARTIFACT.md);
  moved verbatim from /Vector_Workload_Normal_Forms.txt at registration.
wp0-status: item 1 (battery-A holdout, fitness measure_corpus) and the registered
  battery-A uniform-sampling harness fix (RC1_ROUND2_CANDIDATE.md finding 3) landed
  with this registration; items 2-3 (structural/content seed split, role samplers)
  are realized by the same-instance query-block convention (QUERY_FRAC families,
  rounds 7-9).
---

# Vector Workload Normal Forms

## A Research Plan for a Predictive Theory of Approximate Nearest-Neighbor Search

### Executive summary

This project will investigate whether apparently different vector-search workloads can be reduced to a small set of canonical geometric and query–corpus properties that predict approximate nearest-neighbor search behavior across datasets, embedding models, algorithms, and scale.

The central hypothesis is:

> A vector-search workload is not characterized by its corpus alone. It is a joint query–corpus object, and much of its operational behavior may be determined by a compact set of invariant “order parameters.”

The proposed theory would play a role similar to relational normal forms and database statistics. Raw coordinates, embedding-model identity, arbitrary rotation, and other representational details would be treated as nuisance variables. The research would seek a minimal representation that preserves the properties needed to predict search cost, recall, failure modes, and algorithm choice.

The immediate motivation comes from OpenVector Bench. Its recent experiments indicate that independently regenerating structural state for synthetic queries can move them onto a different manifold and radically alter measured intrinsic dimension. Sharing the correct structural backbone changes the apparent problem. This suggests that the relevant object is the relationship between the query process and the corpus process, not either distribution in isolation.

OpenVector Bench already separates corpus-to-corpus and query-to-corpus batteries and proposes a sealed test of whether fitted geometry predicts previously unseen IVF and graph-search behavior. That provides an unusually strong experimental foundation for the proposed research.

---

# 1. Research objective

The project has three progressively stronger objectives.

## Objective A: Workload characterization

Determine which measurable properties of a query–corpus pair explain ANN difficulty better than conventional corpus-level descriptors.

This would establish that query–corpus coupling must be treated as a first-class benchmark object.

## Objective B: Predictive normal forms

Identify a compact descriptor of a vector workload that predicts:

* recall–cost curves;
* required search breadth;
* IVF probe counts;
* graph traversal effort;
* reranking depth;
* index occupancy and imbalance;
* tail latency;
* sensitivity to scale.

Two workloads with matching descriptors should exhibit predictably similar behavior, even when they come from different embedding models or content domains.

## Objective C: Universality classes

Determine whether workloads fall into a small number of operational equivalence classes.

A successful theory would permit statements such as:

> These text, image, and code embedding workloads are different in raw coordinates but belong to the same graph-search universality class.

This is the most fundamental target. It should be treated as a hypothesis to test, not an assumption.

---

# 2. Scientific foundation

Several parts of the proposed theory already have independent support, but they have not yet been unified.

Local intrinsic dimensionality has been shown to distinguish easy and difficult nearest-neighbor queries and to affect ANN implementation performance. Relative contrast was proposed as a more general difficulty measure incorporating dimension, sparsity, and database size. Hubness is a theoretically and empirically established high-dimensional phenomenon in which some points occur unusually often in nearest-neighbor sets.

More recent work shows that geometry alone may not be sufficient for every algorithm. Steiner-hardness incorporates the structure of the ANN graph and reportedly correlates with graph-search effort better than LID on the evaluated workloads. Recent work also constructs query workloads with controlled empirical hardness, reinforcing the principle that the query distribution is part of the benchmark rather than a passive sample.

Vector-database research is also moving toward explicit query planning, plan selection, and adaptive execution rather than treating the ANN index as a fixed black box. This strengthens the analogy with relational query optimization.

The open scientific gap is therefore not whether individual hardness variables matter. It is:

> Is there a small, transferable and causally meaningful set of variables that is jointly sufficient to predict vector-query behavior?

---

# 3. Formal research framework

## 3.1 Define the workload as the primary object

Represent a vector workload as:

[
W =
\left(
P_X,,
P_Q,,
d,,
k,,
N,,
\mathcal F,,
R
\right)
]

where:

* (P_X) is the corpus distribution;
* (P_Q) is the query distribution;
* (d) is the distance or similarity function;
* (k) is the retrieval depth;
* (N) is corpus size;
* (\mathcal F) represents filters or other structured constraints;
* (R) represents relevance semantics when they differ from geometric nearest neighbors.

For purely geometric ANN, (\mathcal F) and (R) may be omitted. They should remain in the general definition because operational vector databases increasingly execute hybrid and semantically evaluated queries.

An ANN system is represented as:

[
S=(A,\theta,H)
]

where:

* (A) is the algorithm or index family;
* (\theta) is its configuration;
* (H) is the hardware and execution environment.

The observed result is:

[
Y(W,S)
]

where (Y) may contain recall, latency, throughput, distance computations, bytes read, energy, rerank depth, or failure probability.

The research goal is to find a descriptor:

[
\Phi(W)
]

such that:

[
Y(W,S) \approx F_S!\left(\Phi(W),N,k\right)
]

for workloads and systems not used to fit (F_S).

---

## 3.2 Define several strengths of equivalence

A single definition of “same workload” will be too restrictive. The project should define a hierarchy.

### Exact metric equivalence

Two workloads are equivalent if a joint isometry preserves all corpus–corpus and query–corpus distances.

Examples include a common orthogonal rotation under Euclidean or cosine geometry.

This equivalence is mathematically exact but too narrow to classify real workloads.

### Exact neighborhood equivalence

Two workloads are equivalent if they preserve exact top-(k) identities, rankings, or distance ratios for the registered query set.

This ignores irrelevant coordinate differences but remains tied to particular finite samples.

### Statistical neighborhood equivalence

Two workloads are equivalent if distributions of local geometric quantities agree within registered tolerances.

Candidate quantities include margins, local dimensionality, density, hub exposure, neighborhood overlap, clusterability, and query support distance.

### Algorithm-relative equivalence

For an algorithm family (\mathcal A):

[
W_1 \equiv_{\mathcal A} W_2
]

when normalized performance curves agree across configurations and scale.

This allows the possibility that two workloads are equivalent for IVF but not for HNSW.

### Cross-algorithm operational equivalence

This strongest empirical equivalence requires agreement across several distinct ANN families. It is the most appropriate basis for a workload universality class.

---

# 4. Candidate vector workload normal form

The initial candidate normal form should be:

[
\mathcal N(W)=
\left(
\mathcal M,,
\rho_X,,
\rho_Q,,
\Lambda,,
\mathcal T,,
\eta,,
d,,
k,,
N
\right)
]

where:

* (\mathcal M): shared support, manifold, or system of local charts;
* (\rho_X): corpus density over that support;
* (\rho_Q): query density over that support;
* (\Lambda): local spectral and anisotropy fields;
* (\mathcal T): topology and connectivity between local regions;
* (\eta): residual noise, duplication, and quantization structure;
* (d,k,N): metric, retrieval depth, and scale.

This representation separates three frequently conflated questions:

1. Where can corpus and query vectors exist?
2. How are corpus vectors distributed over that support?
3. How are queries distributed relative to it?

The recent OpenVector result is naturally interpreted as a failure to preserve (\mathcal M): the corpus and independently seeded queries had similar generating recipes but different structural realizations.

The project should not assume that this proposed decomposition is identifiable. One research task is to determine which components can be uniquely estimated and which are only identifiable through operational equivalence.

---

# 5. Research questions and hypotheses

## RQ1: Is ANN difficulty a joint query–corpus property?

### Hypothesis H1

Models using joint query–corpus descriptors will predict per-query and aggregate ANN cost substantially better than models using corpus-only statistics.

A minimum success criterion should be a meaningful out-of-workload error reduction, not merely an improvement on randomly held-out queries from the same workload.

---

## RQ2: Does a compact sufficient descriptor exist?

### Hypothesis H2

A descriptor containing approximately 10–30 calibrated variables will predict most of the variation in recall–cost curves across unseen workloads.

Candidate variables include:

* calibrated local intrinsic dimension;
* local spectral participation ratios;
* nearest-neighbor margin distributions;
* local relative contrast;
* query distance to corpus support;
* neighborhood density and density gradient;
* hub and anti-hub exposure;
* local clusterability;
* inter-region connectivity;
* query–corpus cluster-frequency divergence;
* neighborhood retention under compression;
* graph-native hardness measures.

The final descriptor must be selected empirically. This list is a candidate library, not a conclusion.

---

## RQ3: Are normal forms algorithm independent?

### Hypothesis H3

Some variables will be broadly algorithm independent, while others will be algorithm-relative.

For example, local margins may affect nearly every ANN family, whereas graph connectivity can have special predictive value for graph indexes. The Steiner-hardness results provide a concrete reason to expect algorithm-relative descriptors.

---

## RQ4: Can workload behavior be reproduced causally?

### Hypothesis H4

Synthetic workloads that match the proposed normal form will reproduce ANN behavior not used during fitting.

This is stronger than showing statistical correlation. The generator must create the mechanisms, and the resulting behavior must follow.

---

## RQ5: Do universality classes exist?

### Hypothesis H5

Workloads from different embedding models or modalities will cluster into a smaller number of operational classes than their raw representations suggest.

Within a class:

* algorithm rankings should transfer;
* tuning parameters should transfer after scale normalization;
* recall–cost curve shapes should be predictable;
* failure modes should be similar.

---

## RQ6: Are there stable scaling laws?

### Hypothesis H6

Conditional on the normal form, key quantities will follow stable functions of (N), such as:

[
C_A(N)\sim N^{\alpha_A(\Phi)}
]

or:

[
H_k(N)\sim N^{\beta(\Phi)}
]

where (C_A) is an algorithmic cost and (H_k) is hubness at neighborhood scale (k).

The functions may not be pure power laws. Power laws should be tested against logarithmic, piecewise, saturating, and transition models.

---

# 6. Work packages

## WP0 — Protocol repair and preregistration

Before investigating fundamental theory, remove known measurement ambiguities.

### Tasks

1. Correct Battery A so held-out queries are never present in the searched base.
2. Separate structural randomness from row-level content randomness.
3. Implement explicit `role="corpus"` and `role="query"` samplers.
4. Make generation row-addressable and independent of requested corpus size, shard boundaries, and process count.
5. Add invariance tests for rotations, row order, sharding, and deterministic regeneration.
6. Register the theory-study metrics separately from RC-1 so that exploratory additions do not alter OpenVector’s existing admission criteria.
7. Preserve the RC-2 seal; do not use its outcomes to choose the normal-form descriptor.

The current OpenVector preregistration already requires held-out Battery-A queries, separate query-to-corpus evaluation, a multi-(n), multi-(k) grid, equivalence intervals, and a sealed predictive test. These should remain intact.

### Deliverable

A versioned “Vector Workload Theory Protocol v1” containing definitions, exclusions, data splits, statistical tests, and stopping rules.

---

## WP1 — Formal invariances and identifiability

### Tasks

1. Prove exact invariance under joint isometries.
2. Characterize which transformations preserve rankings but not margins.
3. Distinguish corpus-only transformations from joint query–corpus transformations.
4. Define algorithm-relative pseudometrics between workloads.
5. Study non-identifiability: construct geometrically different workloads with identical selected diagnostics.
6. Determine whether proposed descriptors are invariant under nuisance transformations.
7. Define a canonical representation where possible, such as ordered spectra and canonical density summaries.

### Key experiment

Construct pairs of workloads that share:

* covariance but not local neighborhoods;
* local dimension but not hubness;
* hubness but not query support;
* margins but not graph topology.

If an allegedly sufficient descriptor cannot distinguish workloads with different ANN behavior, reject or expand it.

### Deliverable

A formal definitions paper establishing the hierarchy of equivalence and the limits of canonicalization.

---

## WP2 — Build a vector workload atlas

Create an empirical matrix spanning workload type, embedding model, query process, scale, and ANN algorithm.

### Workload families

The atlas should contain at least:

* several text retrieval workloads;
* multilingual text;
* image embeddings;
* cross-modal image–text retrieval;
* code retrieval;
* recommendation-like vectors;
* deliberately shifted or out-of-domain queries;
* controlled synthetic workloads;
* filtered or hybrid workloads in a later extension.

Each real corpus should have at least two query processes where feasible:

* corpus-like held-out queries;
* task-native queries;
* controlled shifted queries.

### Scale grid

Use nested samples where possible:

[
N \in
{10^5, 3\times10^5,10^6,3\times10^6,10^7,\ldots}
]

Continue until computational limits are reached. Large synthetic tiers can extend the scaling study, but real and synthetic evidence must remain clearly distinguished.

### Algorithms

Include at least one representative of each major physical access-path family:

* brute-force exact search;
* graph ANN;
* IVF or partition-based ANN;
* compressed IVF/PQ;
* disk-oriented ANN;
* hashing or projection-based search where practical.

ANN-Benchmarks and Big ANN Benchmarks demonstrate the value of common interfaces and controlled billion-scale comparisons, but the proposed atlas adds query–corpus characterization and nested distribution control.

### Measurements

For every workload, query and scale:

* exact neighbor distances and margins;
* LID and alternative dimension estimators;
* local spectral profiles;
* hubness and anti-hubness;
* local density and density gradients;
* cluster and chart membership;
* query support-distance estimates;
* graph connectivity measures;
* IVF occupancy;
* per-query ANN effort;
* recall–latency and recall–work curves;
* tail latency and failure rates;
* reranking depth.

### Deliverable

An open “Vector Workload Atlas” with raw measurements, standardized workload manifests, and reproducible exact-neighbor computation.

---

## WP3 — Mechanistic generator and causal interventions

Build a generator specifically for scientific intervention rather than only benchmark fitting.

### Proposed decomposition

[
x_i =
\operatorname{Normalize}
\left[
c_{z_i}
+
U_{z_i} a_i
+
Vb_i
+
\epsilon_i
\right]
]

where:

* (z_i) selects a local region;
* (c_z) is a center;
* (U_z) is a local subspace;
* (a_i) gives local coordinates;
* (Vb_i) supplies shared global variation;
* (\epsilon_i) represents residual structure.

Corpus and query roles share structural objects but use separate distributions:

[
z_x\sim \pi_X,\qquad z_q\sim \pi_Q
]

[
a_x\sim P_X(a\mid z),\qquad
a_q\sim P_Q(a\mid z)
]

### Independent intervention knobs

The generator should independently vary:

* local dimension;
* global effective rank;
* angular anisotropy;
* local density gradients;
* cluster-size distribution;
* chart overlap;
* inter-chart connectivity;
* curvature;
* query–corpus cluster shift;
* query boundary mass;
* duplication and near-duplication;
* hubness-generating mechanisms;
* metadata/vector correlation.

### Experimental design

Use factorial and fractional-factorial designs rather than one-dimensional sweeps alone.

For each intervention:

1. vary the target mechanism;
2. hold other measured descriptors within tolerance;
3. measure ANN behavior;
4. test whether the predicted operational consequence appears;
5. repeat across algorithm families.

This is the main causal test. If hubness can only be increased by also changing local dimension and margins, then hubness may not be an independently meaningful normal-form coordinate.

### Deliverable

A row-addressable “geometric workload laboratory” capable of generating matched controls and counterfactual workload pairs.

---

## WP4 — Discover minimal sufficient descriptors

### Baseline models

Compare four model classes:

1. **Scale-only:** (N,d,k)
2. **Corpus-only:** traditional global and local corpus metrics
3. **Joint geometric:** corpus plus query–corpus descriptors
4. **Joint plus algorithm structure:** graph or partition-specific descriptors

### Prediction targets

Predict:

* per-query distance evaluations;
* per-query nodes visited;
* IVF cells needed for target recall;
* reranking depth;
* probability of recall failure;
* aggregate recall–cost curves;
* p50, p95 and p99 latency;
* best algorithm and configuration under a resource constraint.

### Model classes

Use:

* regularized generalized linear models;
* hierarchical Bayesian models;
* gradient-boosted models as nonlinear references;
* monotonic models where theory implies monotonicity;
* symbolic regression for interpretable scaling laws;
* conformal or probabilistic prediction for uncertainty.

Highly expressive models should not be treated as proof of a compact theory. The primary result must come from sparse or interpretable predictors.

### Feature-selection criterion

A descriptor remains in the proposed normal form only if it:

1. improves out-of-workload prediction;
2. survives leave-one-model-family-out validation;
3. remains stable under nuisance transformations;
4. participates in a successful causal intervention;
5. is estimable without exhaustive ANN execution, unless explicitly labeled algorithm-relative.

### Validation splits

Do not randomly split individual queries alone. Use progressively harder splits:

* held-out queries within a workload;
* held-out corpus;
* held-out embedding model;
* held-out modality;
* held-out algorithm family;
* held-out scale range.

The main claim should be based on held-out workloads and embedding families.

### Deliverable

A preregistered candidate descriptor (\Phi^*) with uncertainty estimates and a documented list of rejected variables.

---

## WP5 — Normal-form matching experiments

This work package directly tests whether matched descriptors imply matched behavior.

### Pair construction

Create workload pairs using three methods:

1. pairs of naturally occurring real workloads;
2. real-to-synthetic matched pairs;
3. synthetic counterfactual pairs.

### Matching procedure

Match workloads on increasingly rich descriptor sets:

* global spectrum only;
* spectrum plus local dimension;
* plus margins and density;
* plus hubness;
* plus query–corpus shift;
* plus topology or algorithm-relative hardness.

At each stage, test whether operational agreement improves.

### Primary endpoint

For each algorithm, compare normalized recall–work curves using functional equivalence tests.

For example:

[
\sup_r
\left|
\log C_{W_1}(r)-\log C_{W_2}(r)
\right|
<\epsilon
]

over a preregistered recall interval.

### Transfer tests

Use the configuration tuned on (W_1) directly on (W_2).

Measure:

* regret relative to workload-specific tuning;
* preservation of algorithm ranking;
* preservation of tail behavior;
* transfer of scaling exponent.

Low transfer regret is stronger evidence of equivalence than correlation between summary metrics.

### Deliverable

An empirical answer to whether normal-form equivalence is operationally meaningful.

---

## WP6 — Scaling laws and phase transitions

### Questions

1. Which descriptors change with (N)?
2. Which remain stable properties of the generating process?
3. Does hubness grow smoothly or exhibit threshold behavior?
4. Do algorithm rankings change at predictable boundaries?
5. Does query–corpus shift become more or less important as the corpus densifies?
6. Are there regime transitions where graph, IVF or brute-force execution becomes preferable?

### Method

Fit several competing scaling models:

* power law;
* logarithmic;
* saturating;
* piecewise linear in log space;
* change-point models;
* finite-size scaling models.

Do not label a pattern a phase transition merely because a curve bends. Require:

* reproducibility across seeds;
* stable estimated transition location;
* a mechanistic explanation;
* cross-workload collapse after normal-form rescaling.

### OpenVector integration

OpenVector’s nested tiers are particularly valuable here because they are intended to hold the distribution fixed while varying (N). The family specification defines exact nested membership through content-addressed row ordering, addressing a major confound in ordinary cross-dataset scaling comparisons.

### Deliverable

A scaling-law paper and a set of falsifiable predictions for larger tiers.

---

## WP7 — Vector-query optimizer prototype

If a predictive normal form emerges, implement it as a database-style statistics and cost-model system.

### Components

#### Workload statistics catalog

Maintain estimated distributions of:

* query hardness;
* local dimension;
* margins;
* hub exposure;
* density;
* query–corpus shift;
* filter–vector correlation;
* index occupancy.

#### Per-query estimator

Estimate a query state:

[
s(q,X)=
\left(
\widehat d_{\text{local}},
\widehat{\Delta}*k,
\widehat\rho,
\widehat h,
\widehat\delta*{\text{support}}
\right)
]

using a small pilot search, routing index, or learned estimator.

#### Plan space

Choose among:

* exact scan;
* graph search breadth;
* IVF probe count;
* compressed search plus reranking;
* disk versus memory tier;
* pre-filter versus post-filter;
* candidate and rerank depth.

#### Cost model

Predict latency, work, and recall uncertainty for each plan.

#### Adaptive execution

Permit the plan to widen when the observed search trajectory disagrees with the estimate.

### Evaluation

Compare against:

* static default parameters;
* globally tuned parameters;
* per-workload tuning;
* oracle per-query choice;
* existing learning-based planners where applicable.

The target is not merely lower mean latency. It should reduce tuning regret and tail recall failures under workload shift.

### Deliverable

A working prototype demonstrating whether the proposed theory has systems value.

---

# 7. Statistical methodology

## Preregistration

Register before final evaluation:

* primary hypotheses;
* descriptor candidates;
* fitting and test workloads;
* equivalence tolerances;
* curve-comparison methods;
* multiple-testing corrections;
* stopping criteria;
* treatment of failed or unavailable system runs.

## Uncertainty

Use hierarchical resampling reflecting the true levels of variation:

* embedding model;
* corpus;
* query;
* generator seed;
* index construction seed;
* machine run.

Do not describe overlapping subsamples as independent replications.

## Equivalence rather than failure to reject

The primary question is whether behaviors are sufficiently close, not whether a difference fails to reach significance.

Use two one-sided equivalence tests or Bayesian regions of practical equivalence for scalar and functional outcomes.

## Leakage control

The most serious risk is selecting descriptors because they predict the same algorithm measurements later presented as validation.

Maintain three layers:

1. exploratory development;
2. registered model-selection workloads;
3. sealed operational validation.

OpenVector’s RC-2 must remain a separate sealed evaluation rather than becoming another feature-selection loop.

---

# 8. Falsification criteria

The theory should be considered falsified or substantially weakened under any of the following outcomes.

## F1: Corpus-only sufficiency

Joint query–corpus descriptors do not improve prediction on held-out workloads.

This would reject the central “search socket” hypothesis.

## F2: Descriptor non-transfer

The selected descriptor predicts within known datasets but fails on unseen embedding models or modalities.

This would make it a benchmarking heuristic rather than a general theory.

## F3: Algorithm fragmentation

Each algorithm requires a nearly unrelated hardness model.

The result might still support algorithm-relative normal forms, but not a universal workload normal form.

## F4: Intervention failure

Changing a proposed coordinate while holding others fixed does not cause the predicted operational change.

This would suggest that the coordinate is correlational or improperly defined.

## F5: Non-identifiability

Many workloads with identical proposed normal forms exhibit materially different ANN behavior.

The descriptor would be insufficient.

## F6: Scale failure

Models fitted below (10^7) fail systematically at larger (N), with no stable scaling correction.

This would sharply limit trillion-scale claims.

## F7: Semantics failure

Geometric equivalence predicts exact-neighbor recall but not application relevance.

The result would remain an ANN systems theory, not a general retrieval theory.

---

# 9. Decision ladder for interpreting results

## Level 1 — Measurement result

Query–corpus coupling explains the earlier anomaly, but no compact transferable predictor is found.

**Contribution:** correction to synthetic ANN benchmarking.

## Level 2 — Benchmark result

A generator matches OpenVector RC-1 and predicts sealed RC-2 behavior for one real workload.

**Contribution:** strong vector-search benchmark and synthetic workload methodology.

## Level 3 — Empirical workload theory

A compact descriptor predicts ANN behavior across multiple corpora and algorithms.

**Contribution:** major systems and benchmarking result.

## Level 4 — Normal-form theory

Matched descriptors support configuration transfer and causal counterfactual reproduction across embedding families.

**Contribution:** a general theory of vector workloads.

## Level 5 — Universality and scaling theory

A small number of workload classes and scaling laws predict algorithmic regimes across modalities and large changes in (N).

**Contribution:** potentially foundational result for vector-search science.

Claims should advance through this ladder only when the corresponding evidence is obtained.

---

# 10. Proposed schedule

## Months 0–3

* repair measurement protocol;
* complete preregistration;
* define workload and equivalence formally;
* implement invariance and determinism tests;
* begin initial workload atlas.

## Months 3–6

* collect multi-model, multi-query workload matrix;
* run exact-neighbor measurements;
* benchmark initial ANN families;
* build descriptor extraction library.

## Months 6–10

* implement mechanistic generator;
* run causal intervention experiments;
* calibrate local dimension and hubness estimators;
* fit first joint difficulty models.

## Months 10–14

* freeze candidate descriptor;
* run leave-one-workload and leave-one-model-family-out tests;
* conduct matched-pair normal-form experiments;
* test parameter and algorithm-ranking transfer.

## Months 14–18

* conduct nested scaling experiments;
* estimate scaling laws and possible regime transitions;
* perform external replication on at least one independently prepared workload.

## Months 18–24

* run final sealed evaluations;
* integrate successful findings into OpenVector;
* construct vector-query optimizer prototype;
* release atlas, generator, theory specification and reproducibility package.

---

# 11. Required team and infrastructure

A minimal team would include:

* one ANN/vector-search systems researcher;
* one geometry, statistics or manifold-learning researcher;
* one database query-optimization researcher;
* one research engineer responsible for deterministic generators and benchmarking;
* access to domain collaborators for real query workloads.

Infrastructure should support:

* exact nearest-neighbor computation at research-scale tiers;
* repeated index construction;
* controlled CPU and GPU experiments;
* large local or distributed storage;
* immutable experiment manifests;
* reproducible containerized builds;
* result provenance and hardware telemetry.

Hardware variation should initially be controlled rather than modeled. Cross-hardware generalization can become a later study once the geometric theory is stable.

---

# 12. Core deliverables

1. **Vector Workload Theory Specification**
   Formal definitions, equivalence relations and preregistered tests.

2. **Vector Workload Atlas**
   A multi-domain collection of query–corpus measurements and ANN behavior.

3. **Normal-Form Descriptor Library**
   Reproducible estimators for joint workload characteristics.

4. **Mechanistic Workload Generator**
   Row-addressable, role-conditioned and intervention-capable.

5. **Normal-Form Matching Benchmark**
   Tests whether matched geometry transfers operational behavior.

6. **Scaling-Law Study**
   Controlled nested-(N) analysis.

7. **Vector Query Optimizer Prototype**
   A practical demonstration that normal-form statistics support plan selection.

8. **OpenVector Integration**
   RC-1/RC-2-compatible generator and query process, if the evidence supports promotion.

---

# 13. The decisive experiment

The most informative single experiment is a cross-workload configuration-transfer test.

1. Select two real workloads from different embedding families.
2. Estimate their candidate normal-form descriptors.
3. Construct a synthetic workload matched to the first.
4. Tune HNSW, IVF and a disk-oriented ANN index only on the synthetic workload.
5. Apply those configurations unchanged to the real workload.
6. Repeat for the second workload.
7. Compare regret against workload-specific tuning.
8. Repeat after deliberately mismatching one coordinate at a time.

The fundamental hypothesis receives strong support only when:

* matched workloads transfer configurations with low regret;
* mismatching a supposedly important coordinate predictably breaks transfer;
* the effect repeats across algorithms and embedding families;
* the behavior was not part of the descriptor-fitting objective.

That experiment converts “the metrics look similar” into a direct operational test of whether the proposed normal form preserves what a vector-search system needs to know.

---

# Conclusion

The proposed research should not begin by declaring that vector workloads possess normal forms. It should begin by defining what equivalence would mean and constructing experiments capable of disproving it.

The strongest plausible outcome is a compact theory in which:

[
\text{ANN behavior}
\approx
F\left(
\text{shared support},
\text{corpus density},
\text{query density},
\text{local geometry},
\text{topology},
N,
\text{algorithm}
\right)
]

If this approximation generalizes across models, modalities, algorithms and scale, the result would be much more than a synthetic benchmark. It would establish the beginnings of a database-style science of vector workloads: canonical workload descriptions, sufficient statistics, cost models, plan selection and experimentally validated universality classes.
