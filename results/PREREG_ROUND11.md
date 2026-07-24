# Pre-registration — Round 11: mechanism-designed battery-A corpora (DRAFT v2 for review)

**Status: DRAFT ⚪ — not frozen.** Drafted 2026-07-24, amended to v2 the same
day after the pre-freeze calibration sweep
([`ROUND11_CALIBRATION.md`](ROUND11_CALIBRATION.md)) fired the draft's own
failure clause. Freezing (and any §-numbering into the RC-1 family) is the
author's call. Round-10 verdict governs the premise: battery-A G1 (~2.6×) and
G6 (~1.7×) misses are a *generator-capability* failure, not a fitness
failure — no optimizer pass over the existing generator family can reach the
target tail (the Θ(k) donor ceiling and the soft-gradient ~2.2k cap, measured
in turboquant-pro `docs/RESULTS_strata_phase23_gates.md` fixture work, bound
it structurally). Round 11 therefore changes the GENERATOR, not the search.

## Amendment history

- **v1 → v2 (2026-07-24).** The v1-permitted calibration sweep ran before any
  freeze and measured: (a) the dial is real and monotone at the pool
  (count_max ≈ 0.025·n_shell, slot competition as predicted); (b)
  **pool→subsample transfer FAILS** — planted rows thin to 0–1 at n=25k (one
  draw held none), the pool-calibrated ratio statistic swings 56.7×→2.5×→30.4×
  along a single ladder, and between-draw S_k variance reaches 26.9 where the
  dial is strong (real: 0.27); (c) the **un-planted fit_v10 baseline is
  already out of the G6 band high in 12/12 ladder cells**, and the overlay is
  monotone-up, so no dial region can reach band from this operating point.
  v2 therefore (1) replaces pool-only calibration with subsample-aware
  calibration, (2) adds a joint operating-point move as a second generator
  change, (3) adds a G1/anatomy pass to the pre-freeze protocol. Bands are
  untouched, per the failure clause's own terms. Nothing in v1 was frozen, so
  this is an amendment of a draft, not a deviation.

## Hypothesis

H11: battery-A hub-tail gates (G1, G6) are reachable by **construction**
using planted local-center mechanisms whose count response is
near-deterministic, leaving the fitted components (spectrum, cloud-mass,
G3/G4/G5 structure) to the round-10 nonparametric machinery unchanged.

H11 is retained in v2 with one sharpened premise: "reachable by
construction" now explicitly means *from an operating point whose emergent
hub mass sits at or below band* — the calibration showed construction cannot
rescue an operating point that already overshoots.

## Generator changes (v2: two changes, jointly)

1. **Operating-point move (new in v2).** Reduce the emergent cloud/hub mass
   of the fitted generator so the *un-planted* baseline's ladder statistics
   sit at or below the G6 band (measured v1 baseline: S_k ratio 1.19–1.68,
   count_max ratio 1.25–2.14, out high in 12/12 cells). This is the round-10
   target-2 joint constraint (G1-slope/G6-level) taken as a precondition:
   the monotone-up dial can only land in band if the floor it stands on is
   not already above it.
2. **`local_centers` primitive (v1, unchanged).** `m` off-center unit shells
   (radius r, ambient placement per existing geometry), each with `p`
   planted rows at its local center, plus the existing background. Measured
   response (STRATA fixtures 2026-07-23; confirmed at pool scope in the
   calibration sweep): planted count ≈ n_shell·(slots taken), count_max set
   near-deterministically by n_shell alone, S_k monotone in (m, p, n_shell).
   Centrality signature stays population-typical when a central band is
   occupied (origin-shell trick) — G1's mechanism constraint respected at
   fixture level, now to be verified at corpus level (§ pre-freeze protocol).

## Calibration (v2: subsample-aware — replaces v1 pool-only calibration)

The v1 sweep calibrated at the pool and the statistic did not survive the
grid's sampling operator. v2 calibrates against what the gates actually see:

- **Calibrate per ladder n, under the grid's own subsample operator** —
  (m, p, n_shell) → (S_k, count_max, RH) measured on grid-subsampled ladders
  (n ∈ {25k, 50k, 100k, 200k}), never on the pool alone. Pool values may be
  recorded as diagnostics only.
- **Retention in the mass budget.** Expected surviving planted rows per draw
  = (m·p + shell mass)·(n/pool)·(1 − holdout). Dial settings whose expected
  surviving planted-row count at the smallest ladder n falls below a floor
  (proposed: ≥ 8 planted rows expected per draw; author to set at freeze)
  are excluded from the admissible dial region — the v1 sweep showed 0–1
  survivors makes the dial silently stochastic.
- **Ladder stability at calibration time.** An admissible dial setting must
  satisfy the |Δslope| ≤ 0.05/decade criterion on its calibration statistic
  *across the ladder before freeze* — stability is a property the setting
  must demonstrate, not a hope the admission run tests.
- **Variance disclosure.** Calibration reports between-draw spread (≥ 2
  draws per n; 5 for any setting proposed for freeze) alongside means; a
  setting whose between-draw S_k spread exceeds the band width at any n is
  inadmissible.

## Pre-freeze protocol additions (v2)

- **G1/anatomy pass (new).** The v1 sweep mapped only the count family
  (S_k, count_max, RH); G1 (TwoNN ID) and the origin-shell centrality claim
  behind P-B are untested by that data. Before freeze: one anatomy sweep
  measuring G1 and centrality response over the admissible dial region and
  the moved operating point, published alongside the calibration. P-B is to
  be frozen against this data, not the fixture argument alone.
- Both sweeps (subsample-aware calibration, G1/anatomy) are pre-freeze
  calibration in the v1 sense: published with the prereg; after freeze,
  parameters are locked and only the admission run speaks.

## Protocol (inherits RC-1 PREREG v2 §5 verbatim; unchanged)

- Pool + subsample fitness (round-10 fix): fit AT the pool, evaluate
  gates on grid-subsampled ladders — never generate-at-n.
- Formal grid admission: 12 cells, ≥6/8 gates in ≥10/12, equivalence
  bands [0.85,1.15]/[0.80,1.20], 5-subsample CIs, mandatory G1/G5/G6
  every cell, |Δslope| ≤ 0.05/decade. Sealed 25% untouched.
- Bands are NOT adjusted by this amendment (failure-clause discipline).

## Predictions (to be frozen by the author)

- P-A (v2): with the operating point moved to/below band and the dial
  subsample-calibrated per above, G6 lands in band in ≥10/12 cells
  (mechanism claim: count tail is constructed, not emergent — now tested
  from a floor that permits it).
- P-B (v2): G1 lands in band WITHOUT degrading G3 (1.00×24/24 in round 9),
  frozen against the pre-freeze G1/anatomy data — the local-center
  mechanism is orthogonal to the recolouring.
- Failure clauses:
  - If the subsample-calibrated dial *still* fails |Δslope| stability in the
    admission run, the mechanism-level sampling-operator lesson recurs a
    third time and the local-center family is reported as structurally
    non-transferring — retire the primitive, do not adjust bands.
  - If the operating-point move cannot bring the un-planted baseline to
    band without breaking G3/G4/G5, that is a joint-constraint infeasibility
    finding at the fit_v10 family level — reported as such (this would be
    the round-9 "NOT ADMITTED" outcome recurring at the operating-point
    level, and would redirect round 12 at the fitted family, not the dial).

## Assets

Fixture constructions + measured responses: turboquant-pro
`tests/test_anatomy.py` (confusion-matrix fixtures), `strata.py`
instrumentation for verification, adversarial-hubness benchmarks
(arXiv:2604.05480 / 2602.22427) as candidate external stress batteries
(exploratory, non-gating). Calibration evidence:
[`ROUND11_CALIBRATION.md`](ROUND11_CALIBRATION.md) +
[`r11_calibration.json`](r11_calibration.json) (md5
`a21ccaeaac543fb698eff5d759ed06b5`), driver `harness/rc1/r11_calibration.py`
@ `6cd9304`. Compute: NRP swarm pods per `feedback_nrp_for_cpu_search`
(cpu=1/2Gi, self-contained via target ConfigMap), not Atlas CPUs.
