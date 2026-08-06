# Pre-registration — Round 13: a hubness codebook, measured before it is built (DRAFT v1)

**Status: DRAFT ⚪ — not frozen.** Drafted 2026-08-06 following the round-12
close ([`GEN_ROUND12_STAGE2.md`](GEN_ROUND12_STAGE2.md), `2c3a15d` + the
frac-arm addendum `cc432d6`): the cascade is not present at ladder scale and
its absence is structural on both declared axes — `smin` cannot buy the
octaves (1.90 → 1.94 over a 50× sweep) and the sibling-crowding reading is
refuted by its own registered test (octaves *fall* with frac, 1.935 →
1.847). Whether this document is round 13 or an amendment to the r12
architecture line is the author's naming call. Freezing is the author's
call. Bands are those of RC-1 §5, untouched here and not adjustable by
anything downstream of this draft.

The design in §2 is the author's proposal, recorded here as registered
predictions with the one structural constraint (§3) that the campaign's own
negatives impose on it.

## 1. Premise (what four rounds of negatives license)

Three findings constrain any further generator work, and this draft is
built to respect all three rather than rediscover them.

- **Round 7 — hubness is not a corpus property.** Real base-to-base
  reverse-neighbour skew is only ≈ 1.5, while battery-B G6 reads 6.8. The
  gate's number lives in the **query marginal**, not in the corpus alone.
  A point is a hub with respect to a (corpus, query measure, metric, k)
  tuple. Every family that carried hubness as a corpus-side knob has
  either overshot the anatomy or broken a companion gate.
- **Rounds 9 and 11 — the sampling operator is part of the object.**
  Fit-at-n does not survive grid subsampling; planted absolute counts do
  not either. Read off the committed real reference
  ([`r11v2_real_ref.json`](r11v2_real_ref.json)): real holds its count-skew
  **level** (S_k ≈ 1.5–1.8, n-stable) while its absolute count maxima
  **fall** with n (42 → 9.4 at k10). Real hub mass is a population law
  that re-expresses at every sampling scale. Fixed owners can only
  overshoot or vanish.
- **Round 12 — verify presence before building on a mechanism.** The
  cascade's unit-scale evidence (n = 3000, dim = 64) did not transfer to
  the ladder, and the presence gate — added one round earlier — is what
  stopped a failure clause from firing on a mechanism that was never
  there. Gate first is now standing practice, and this draft applies it to
  itself.

## 2. The proposal (author's)

Represent each region of the space by a small set of measurable **hubness
states**, and separate the description into three layers so that the
generator's control surface and its measured response are never the same
quantity:

1. **Corpus geometry code** — local density, radius spectrum across
   several k, anisotropy (angular versus radial contribution to neighbour
   attraction), local intrinsic dimension.
2. **Query exposure code** — how much query mass interrogates the region.
3. **Retrieval response code** — the resulting N_k, reverse-neighbour
   rank, distance-to-neighbour profile, and persistence across seeds,
   metrics, and dimensional projections.

Layers 1 and 2 are **set**. Layer 3 is **measured**. Codewords are
constructed from latent geometric and query-side properties and never
assigned from observed N_k — assigning from the response is circular
calibration, and it is the failure this separation exists to prevent.
The intended benefit is independent control: hubs and anti-hubs stop being
accidents of one global Zipf exponent or covariance parameter.

This turns generator search into an intervention study. The registered
question is no longer "does this parameter reproduce the statistic" but
"does setting this state produce the intended phenotype, and does the same
state produce it again under a different sampling operator".

## 3. Binding design constraint — codewords are a field, not a labelling

**A codeword names a region of the space, not a set of rows.** Codes are
intensities of a measure over the space (density, radius spectrum, query
mass, anisotropy, local ID as functions of position); points are drawn
from that field. No construction in this round may attach a code to an
enumerated point set.

This is not a stylistic preference. A codebook assigned to points — including
"the top and bottom deciles of the pool", the natural reading of the
two-ended sweep — is a fixed-owner construction under a new name. Decile
membership is defined by rank in the full pool; subsample n = 25k from a
420k pool and the surviving members thin by the sampling factor while their
codes do not re-express. That is round 11 exactly, and it would be
rediscovered at cost. A field thinned by a constant factor keeps its shape,
which is the covariance property real data has and every planted
construction so far has lacked.

Corollary for the two-ended sweep: vary the **field** over the high- and
low-intensity tails, not the identity of the decile members.

## 4. Registered predictions

- **P-13A (quantization gate — runs first, on real data only).** Estimate
  the layer-1 and layer-2 codes on the real Cohere Embed-V3 corpus
  (`/archive/tqp_real/wiki1024`, train/val only, seal untouched) and fit a
  codebook of K states **on latent features alone**. Prediction: real
  retrieval phenotype concentrates — a codebook with **K ≤ 12** predicts
  held-out layer-3 response (N_k at k ∈ {10, 30, 100}, reverse-rank
  quantile) with cross-validated mutual information at least **2× that of
  the best single latent feature**, and state assignment is stable across
  seeds at **≥ 0.7 adjusted Rand index**. Mechanism claim: hubness
  phenotype is low-dimensional in the latent code, which is the premise
  every later stage rests on.
- **P-13B (anti-hub taxonomy is real and the battery is blind to it).**
  Among real points with N_k = 0 at k = 10, the five proposed categories —
  legitimate high-dimensional anti-hubs, low-density outliers, boundary
  points, metric-misaligned points, and points the query marginal never
  visits — are separable by latent code at **≥ 0.6 balanced accuracy** on
  held-out points and their proportions are stable across seeds. Second
  half, the instrument claim: **G6 cannot distinguish them** — corpora
  matched on G6 and on base-to-base skew to within draw noise differ in
  category proportions by **≥ 2×** in at least one category. If both halves
  hold, the lower tail is an unmeasured axis of the battery and the
  discriminator is a contribution independent of any generator.
- **P-13C (orthogonal control).** With field-valued codewords and the
  central 80% of the corpus field held fixed, independently varying the
  high- and low-intensity tail fields moves **G6 across at least a 3×
  range** while G2, G3, and the base-to-base skew guard all stay in band at
  every ladder cell, on ≥ 3 fresh seeds. Prediction is registered as
  *orthogonality*: hub and anti-hub control are separate mechanisms.

## 5. Failure clauses

- **P-13A fails** (phenotype does not quantize, or states are seed-unstable)
  → the codebook premise is wrong for real embedding geometry: retrieval
  phenotype is continuous and high-dimensional, and no generator should be
  built on a state abstraction. Report the measured dimensionality of the
  phenotype space as the finding. **No layer-3 control work proceeds.**
- **P-13B first half fails** → the anti-hub categories are not separable by
  latent code; report which collapse into which, since a smaller true
  taxonomy is still an instrument result. **Second half fails** (G6 does
  track the categories) → the battery is not blind after all, which is good
  news for the battery and removes the independent instrument contribution;
  record it and do not claim the gap.
- **P-13C fails** → hub and anti-hub control are still driven by one
  geometric mechanism. That is the round-5 G6×G3 frontier recurring one
  layer deeper, and it is primary evidence for the capacity conjecture.
  Report the measured interaction surface. **No refit-and-retry inside the
  round.**
- Bands are not adjusted under any clause. No stage runs on a failed gate.

## 6. Ordering (each stage gates the next)

1. **Stage 0 — measurement only, real data.** Build the layer-1/2
   estimators and the layer-3 readout; run P-13A. Nothing is generated.
   This is the round-12 lesson applied prospectively: if real phenotype
   does not quantize, the round costs a day of compute instead of a
   campaign round. It also yields, free, the number of states and their
   occupancies — the targets any generator would have to reproduce.
2. **Stage 1 — anti-hub discriminator, real data plus existing corpora.**
   Run P-13B against the committed candidate corpora already on hand. No
   new generator family is required, so this stage can produce a result
   even if stage 2 never runs.
3. **Stage 2 — field-valued control, two-ended sweep.** Only if P-13A
   passes. Run P-13C on grid-subsampled ladders under the standing
   instruments (≥ 2 draws per (setting, n), 5 for any freeze candidate).

## 7. Relation to the standing round-13 cascade proposal

The multiplicative-cascade proposal recorded at the close of round 12 and
this codebook are complementary rather than competing. A self-similar
measure is subsample-covariant by construction, which is exactly what §3
requires of a layer-1 field; the codebook supplies the control surface and
the measurement discipline the cascade proposal does not have. Stage 0
serves both, since verifying a cascade's *realized* field is the same
measurement as estimating layer-1 codes. If the cascade is built, its field
must clear the same presence gate that the r12 cascade failed.

## 8. Assets and compute

Real reference and scoring instruments: [`r11v2_real_ref.json`](r11v2_real_ref.json)
(5-draw), `rc1_round2_cells.json`, `spectrum_target_wiki1024.json`. Prior
evidence chain: rounds 7–12 result files in this directory. Anatomy
falsifier (`bb_skew`) is in force as a guard throughout, per round 8.

Compute per standing rules ([`../spec/NRP_OPS.md`](../spec/NRP_OPS.md)):
stage 0 and stage 1 are CPU-bound and belong on NRP, not Atlas. Workers
that fit the enforcement-exempt envelope (cpu ≤ 1, mem ≤ 2Gi) should use
`openvector_bench.memguard` to hold the page-cache footprint inside it;
anything above the envelope must ride a retry loop through the transient
>2Gi clamp. Fan-out uses `openvector_bench.nrp_pool.PoolRunner` so a stuck
volume idles one slot rather than a wave.
