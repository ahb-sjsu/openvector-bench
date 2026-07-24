# Pre-registration — Round 11: mechanism-designed battery-A corpora (DRAFT for review)

**Status: DRAFT ⚪ — not frozen.** Drafted 2026-07-24 for the user's review;
freezing (and any §-numbering into the RC-1 family) is the author's call.
Round-10 verdict governs the premise: battery-A G1 (~2.6×) and G6 (~1.7×)
misses are a *generator-capability* failure, not a fitness failure — no
optimizer pass over the existing generator family can reach the target
tail (the Θ(k) donor ceiling and the soft-gradient ~2.2k cap, measured in
turboquant-pro `docs/RESULTS_strata_phase23_gates.md` fixture work, bound
it structurally). Round 11 therefore changes the GENERATOR, not the
search.

## Hypothesis

H11: battery-A hub-tail gates (G1, G6) are reachable by **construction**
using planted local-center mechanisms whose count response is
near-deterministic, leaving the fitted components (spectrum, cloud-mass,
G3/G4/G5 structure) to the round-10 nonparametric machinery unchanged.

## Generator change (the only change)

Add a `local_centers` primitive to the corpus generator: `m` off-center
unit shells (radius r, ambient placement per existing geometry), each
with `p` planted rows at its local center, plus the existing background.
Measured response (STRATA fixtures, 2026-07-23): planted count ≈
n_shell·(slots taken), count_max and S_k monotone in (m, p, n_shell) —
G6's count-tail becomes a *dial*, not a search target. Centrality
signature stays population-typical when a central band is occupied
(origin-shell trick) — G1's mechanism constraint respected.

## Protocol (inherits RC-1 PREREG v2 §5 verbatim)

- Pool + subsample fitness (round-10 fix): fit AT the pool, evaluate
  gates on grid-subsampled ladders — never generate-at-n.
- Formal grid admission: 12 cells, ≥6/8 gates in ≥10/12, equivalence
  bands [0.85,1.15]/[0.80,1.20], 5-subsample CIs, mandatory G1/G5/G6
  every cell, |Δslope| ≤ 0.05/decade. Sealed 25% untouched.
- Calibration allowed BEFORE freeze: one sweep mapping (m, p, n_shell) →
  (S_k, count_max, RH) on the pool, published with the prereg; after
  freeze, parameters are locked and only the admission run speaks.

## Predictions (to be frozen by the author)

- P-A: with the calibrated dial, G6 lands in band in ≥10/12 cells
  (mechanism claim: count tail is constructed, not emergent).
- P-B: G1 lands in band WITHOUT degrading G3 (1.00×24/24 in round 9) —
  the local-center mechanism is orthogonal to the recolouring.
- Failure clause: if the dial's pool→subsample transfer breaks (ladders
  thin the planted counts out of band), that is the sampling-operator
  lesson recurring at mechanism level — reported as such, and the fix is
  subsample-aware calibration, not band adjustment.

## Assets

Fixture constructions + measured responses: turboquant-pro
`tests/test_anatomy.py` (confusion-matrix fixtures), `strata.py`
instrumentation for verification, adversarial-hubness benchmarks
(arXiv:2604.05480 / 2602.22427) as candidate external stress batteries
(exploratory, non-gating). Compute: NRP swarm pods per
`feedback_nrp_for_cpu_search` (cpu=1/2Gi, self-contained via target
ConfigMap), not Atlas CPUs.
