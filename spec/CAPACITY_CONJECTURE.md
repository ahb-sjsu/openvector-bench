# The Hub-Profile Capacity Conjecture (DRAFT — for the author's review)

**Status: CONJECTURE ⚪, drafted 2026-07-24.** Companion to
`spec/BOND_METRIC.md` (which holds the proved pieces cited below) and
`results/PREREG_ROUND11.md` (whose generator is the achievability side).
Nothing here is claimed as proved unless cited to an existing theorem.

## Setup

An *observation* is O = (metric d, depth k, query measure ν, sampling
operator S) applied to a corpus X = {x₁…x_n} ⊂ ℝ^D. The observable is the
reverse-count vector N_k(X; O) ∈ ℤ^n_{≥0} with Σᵢ N_k(xᵢ) = nk
(corpus→corpus battery), summarized by the sorted normalized profile
p(X; O) ∈ Δ. Define the **realizable region**

  R(n, k, D) = { p : ∃ X ⊂ ℝ^D with p(X; O) = p }.

R is the capacity region of the observation channel: which hub profiles
can ANY geometry produce.

## Known constraints (the converse fragments, already established)

- **Hypersimplex outer bound**: each query contributes k distinct
  incidences, so N_k lies in the hypersimplex Δ(n,k) scaled by n (the
  simplex-address lemma, BOND_METRIC.md).
- **Spectral bound**: ‖M‖₂ ≤ 1/√(n−1) (deterministic, proved).
- **Θ(k) donor ceiling**: the count deliverable to a point-like cluster
  by ambient mass is Θ(k) in any D (measured 2026-07-23; proof sketch:
  the k-NN ball volume argument makes donor count ≈ k).
- **Low-D cap**: for small D, count_max ≤ c(D)·k (kissing-number-type;
  measured: rings top out ≈ 2k).
- **Concentration requirement**: soft (gradient) mechanisms produce
  super-2.2k tails only under distance concentration (measured cap).

## The conjectures

**C1 (dimension-indexed capacity).** R(n,k,D) is nested increasing in D,
and there exists D*(n,k) above which R equals the full
conservation-and-ceiling-compatible region: every profile satisfying the
hypersimplex, spectral, and per-row N_k ≤ n−1 constraints is realizable.

**C2 (finite mechanism basis).** The extreme profiles of R are generated
by finitely many mechanism families — center-planting (counts ~n),
local-center shells (counts ~n_shell, tunable), and
concentration-gradients (soft tails) — and every realizable profile is
approximated by a mixture from this catalog. (The round-11 generator is
the constructive half; its calibration sweep is an explicit map into R.)

**C3 (observation non-commutativity).** Sampling and generation do not
commute: S(R(n,k,D)) ⊊ R(n′,k,D) for subsample size n′ < n, with a
quantifiable contraction of the tail coordinates ("ladders thin") — the
round-9 sampling-operator lesson as a theorem. A generator admitted at
the pool is admitted on ladders only if its profile lies in the
S-stable interior.

**C4 (quotient rate-distortion).** For a bit-rate R per row, let D(R) be
the minimum achievable min-over-strata anti-hub rank error against a
target observation. Then D(R) is bounded below by the ν-mass of query
pairs whose decision margin falls below the quantization scale at rate
R — distortion measured on the QUOTIENT (rankings), not the signal.
Empirical anchor points: the 27.7× score-precision floor (fidelity
plateaus at 0.70 while coverage reaches 0.93) and the originals-rerank
curve (fidelity = coverage exactly when the rate constraint is lifted on
the short list): turboquant-pro `docs/RESULTS_strata_phase23_gates.md`.

## Falsification program

C1/C2: the round-11 calibration sweep either fills the predicted region
or exhibits a hole no mixture reaches (report the hole — it would be the
more interesting outcome). C3: pool→ladder transfer measurements, already
mandated by the prereg. C4: trace D(R) at 2/3/4-bit operating points on
one admitted corpus. Proof work is separate from, and not replaced by,
these measurements.
