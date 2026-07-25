# Pre-registration — Round 12: concentration architecture, not knobs (DRAFT v2 for review)

**Status: DRAFT ⚪ — not frozen.** Drafted 2026-07-24 following the round-11
v2 pre-freeze result ([`ROUND11_PREFREEZE.md`](ROUND11_PREFREEZE.md),
`6e5642c`): joint-constraint infeasibility at the fit_v10 family level —
17 operating points across all five hub-mass knobs, no un-planted baseline
at/below the G6 band on the ladders, and the two levers that move counts
each break a mandatory companion (clouds ↔ G1, hierarchy ↔ G5 + Δslope).
PREREG_ROUND11 v2 remains DRAFT and unsatisfiable as drafted (its
operating-point precondition has no solution in the family); whether this
document supersedes it or is renamed an r11-v3 amendment is the author's
naming call. Freezing is the author's call. Bands are those of RC-1 §5,
untouched here and not adjustable by anything downstream of this draft.

## Amendment history

- **v1 → v2 (2026-07-25).** The v1-permitted stage-1 mechanism anatomy
  sweeps ran before any freeze ([`R12_STAGE1_RESULT.md`](R12_STAGE1_RESULT.md),
  `42bb3a2`; fit_v10 base, full ladder, 336 cells) and decided part of v1's
  predictive content — freezing v1 afterwards would register predictions
  against data already in hand (the r11 v1→v2 situation, resolved the same
  way: amend the draft, bands untouched). Measured: (a) `grad_decay` is a
  clean monotone G1 **level** dial (1.12× real at the 25k end at 0.6, G3
  unharmed) — no longer a prediction; (b) the G1 **n-drift (+0.24/decade) is
  invariant** across the entire gradient sweep — v1's P-A, read per-cell,
  is already refuted: anisotropy cannot pin flatness; (c) the patch-wide
  radial field (`grad_span`) is falsified outright (G1 wrong way, count
  maxima to 10× real); (d) renewal occupancy alone is inert; occupancy ×
  density contrast at `occ_tail 1.8–2.5, dens_span ≈ 0.3` is the admissible
  G6 region — S_k 1.2–2.0× control with G1 leak ≤ 4% and **k30 Δslope
  0.00**, at a G3 cost (0.85 → 0.70). v2 therefore (1) replaces the
  gradient mechanism's flatness role with a **self-similar within-patch
  point process** (the cascade: correlated pairs at graded sub-patch
  scales — per-row radial laws cannot make pairs), keeping `grad_decay` as
  the measured level dial; (2) freezes P-B's operating region to the
  measured admissible region with the surviving unknowns (all-k Δslope,
  G3 recovery under colouring re-fit) as the prediction; (3) re-states the
  decoupling check accordingly. Bands untouched. Nothing in v1 was frozen,
  so this is an amendment of a draft, not a deviation.

## v2 predictions (supersede v1's P-A/P-B; to be frozen by the author)

- **P-A′ (cascade flatness):** a within-patch self-similar point process
  (cluster-in-cluster cascade over ≥ 3 scale octaves, scale-free pair
  distances, no fixed owners) brings the G1 ladder drift from the measured
  +0.24/decade to **|drift| ≤ 0.05/decade** with the level in band via
  `grad_decay`, while count statistics stay within draw noise of the
  cascade-off control at every ladder cell. Mechanism claim: on a
  scale-free pair-distance distribution the TwoNN μ-statistics are
  subsample-invariant — n-flatness as a symmetry, not a tuning target
  (the same renewal principle that carried P-B, applied at sub-patch
  scale).
- **P-B′ (renewal region):** within `occ_tail ∈ [1.8, 2.5], dens_span ∈
  [0.2, 0.4]` there exists a setting with S_k level in band after a
  colouring re-fit, **|Δslope| ≤ 0.05/decade at every k** (k10's measured
  −0.15 at dens 0.3 is the live risk), G1 leak within band, and G3
  recovered to ≥ 0.85 by the re-fit alone (no structural change).
- **Failure clauses (unchanged in spirit, retargeted):** P-A′ fails → ID
  n-flatness in this geometry family requires explicit near-duplicate
  owners; that is the round-9 suspect confirmed at mechanism level and
  primary capacity-conjecture evidence — report, do not tune. P-B′ fails
  on Δslope → the renewal law does not extend below k30; report the k
  profile as the finding. Joint failure after singles pass → the
  interaction is the object. Bands are not adjusted under any clause.

## Premise (what the negatives localize)

Round 9: the sampling operator is part of the object — fit-at-n does not
survive grid subsampling. Round 11 v1: planted absolute counts do not
survive it either (fixed owners keep their counts while the reference
thins). Round 11 v2 stage 1: *every* fit_v10 concentration knob fails —
the k10 large-n count tail (S_k ratio 1.46–1.74 at n ≥ 100k) is invariant
to cloud mass, ownership equalization, and leaf-size Zipf, and only
branch-hierarchy flattening moves it, by rotating the (n, k) profile
through the band (Δslope up to 0.64/decade against a 0.05 limit).

The common cause, read off the real reference (5 draws, committed as
[`r11v2_real_ref.json`](r11v2_real_ref.json)): the real corpus holds its
count-skew **level** (S_k ≈ 1.5–1.8 per k, n-stable) while its absolute
count maxima **fall** as n grows (42 → 9.4 at k10, n25k → n200k). Real hub
mass is a population law that re-expresses itself at every sampling scale.
fit_v10 carries hub mass in **fixed owners** — near-duplicate cloud ladders
and Zipf branch heads — and fixed owners can only overshoot (their counts
are n-invariant) or vanish (when thinned). The G1/G6 trade-off curve
measured across the 17 candidates (cloud mass buys G1 2.25→1.96 at the
price of count tail; no in-band settlement) is the signature of one
mechanism doing two jobs.

## Hypothesis

H12: battery-A G1 and G6 are jointly reachable only by **decoupling the
two jobs**: (a) an intrinsic-dimension mechanism that pins G1 without
near-duplicate owners, and (b) a count-tail mechanism whose hub mass is
carried by a **subsample-covariant population law** (self-similar under
the grid's sampling operator) rather than by enumerable rows. The STRATA
mechanism catalog's local-center/gradient distinction (turboquant-pro
fixture work, `docs/RESULTS_strata_phase23_gates.md`) supplies the two
candidate mechanisms:

- **G1 by gradients**: within-patch anisotropic scale gradients (the
  "soft gradient" family, measured cap ~2.2k on count response — i.e.
  count-quiet by construction) tuned to set TwoNN ID, replacing the cloud
  ladder as the ID-pinning mechanism.
- **G6 by renewal**: heavy-tailed *local density* (patch occupancy drawn
  from a scale-free law applied per-row, not per-planted-row), so any
  subsample redraws the same law and the skew level is n-stable while
  absolute maxima thin with the sample — the real corpus's measured
  covariance, by construction rather than by calibration.

`local_centers` stays shelved as a validated primitive: reintroducible
only if an un-planted baseline ever sits at/below band (v2 retention-floor
and calibration criteria then apply verbatim; proposed floor: expected ≥ 8
surviving planted rows per draw at n = 25k, i.e. m·p ≥ 135 under the
current pool arithmetic).

## Generator change

Replace fit_v10's concentration architecture (cloud near-duplicate ladder
+ Zipf branch-head ownership) with the two decoupled mechanisms above.
Everything else — spectrum machinery, G3/G4/G5 structure, the round-10
nonparametric fit — inherits unchanged. This is an architecture change at
the fitted-family level, exactly where the r11v2 redirect clause points;
it is not a new overlay on fit_v10.

## Pre-freeze program (ordered; each stage gates the next)

1. **Mechanism anatomy sweeps (both mechanisms, independently).** Map
   gradient parameters → (G1, G5, G3) and occupancy-law parameters →
   (S_k, count_max, Δslope) on grid-subsampled ladders under the v2
   instruments: ≥ 2 draws per (setting, n), 5 for freeze candidates,
   between-draw S_k-ratio spread ≤ band width at every n, |Δslope| ≤
   0.05/decade at every k, pool values diagnostic only. The committed
   stage-2/3 drivers (`r11v2_stage2.py`/`r11v2_stage3.py`) and the 5-draw
   real reference are the instruments; G1/anatomy is measured this round,
   not argued from fixtures.
2. **Decoupling check.** Cross-sweep: the G1 mechanism at its band
   setting must be count-quiet (no G6 movement beyond draw noise), and
   the G6 mechanism at its band setting must be ID-quiet. If either
   mechanism moves the other's gate out of band, H12's premise fails at
   that point — reported before any joint fit.
3. **Joint fit + admission** (only if 1–2 pass): round-10 pool+subsample
   fitness with both mechanisms in the family, then the formal 12-cell
   grid admission per RC-1 §5 verbatim (≥6/8 gates in ≥10/12 cells,
   equivalence bands [0.85,1.15]/[0.80,1.20], 5-subsample CIs, mandatory
   G1/G5/G6 every cell, |Δslope| ≤ 0.05/decade, sealed 25% untouched).

## Predictions (to be frozen by the author)

- P-A (decoupling): the gradient mechanism reaches the G1 band
  ([0.85,1.15] on the ratio) with the cloud ladder fully removed, without
  moving S_k beyond draw noise — ID pinning does not require count owners.
- P-B (renewal): the occupancy-law mechanism produces S_k level in band
  with |Δslope| ≤ 0.05/decade across the ladder at every k — the
  n-stable-level / thinning-maxima covariance is constructed, not tuned.
- P-C (joint): with both mechanisms fitted, the admission run lands
  ≥10/12 cells with G3/G5 no worse than the fit_v10 control
  (G5 ≤ 1.19×, G3 ≥ 0.85 under the 5-draw protocol).
- Failure clauses:
  - P-A fails → ID pinning in this geometry family is inherently
    duplicate-driven; report as a mechanism-level finding and aim round 13
    at the ID mechanism alone. No G6 work proceeds on a broken G1 floor.
  - P-B fails (the law does not hold its level under the grid operator) →
    the sampling-operator lesson recurs at architecture level; that is a
    measured hole in the family's reachable region at its third and
    deepest scale, and the capacity conjecture's falsification program
    records it as primary evidence. No refit-and-retry inside the round.
  - P-C fails after P-A/P-B pass → the interaction, not the mechanisms,
    is the object; report the measured interaction surface and stop.
  - Bands are not adjusted under any clause.

## Assets

Evidence chain: [`ROUND11_CALIBRATION.md`](ROUND11_CALIBRATION.md) (v1
dial + transfer failure), [`ROUND11_PREFREEZE.md`](ROUND11_PREFREEZE.md) +
`r11v2_stage1.json`/`r11v2_stage1b.json` (17-point infeasibility +
trade-off curve), [`r11v2_real_ref.json`](r11v2_real_ref.json) (5-draw
real reference, the scoring instrument). Mechanism measurements:
turboquant-pro STRATA fixtures (`tests/test_anatomy.py`,
`docs/RESULTS_strata_phase23_gates.md` — gradient ~2.2k count cap, planted
count ≈ n_shell·slots). Compute: mechanism sweeps on NRP swarm pods
(cpu=1/2Gi, self-contained target ConfigMap) per standing rule; Atlas only
for verification runs needing the committed real-reference protocol.
