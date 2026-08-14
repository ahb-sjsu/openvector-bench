# RC-13: alignment — bringing real queries in-distribution

**Status: plan, 2026-08-15.** From `results/R101_VALBATTERY.md`: battery
B fails structurally because real query vectors are out-of-distribution
for a synthetic cloud built on random frames. The fix is licensed by
PREREG §7 (train = "fit distributional parameters") and is
battery-A-invariant by construction.

## 1. Mechanisms

* **M1 — principal-frame rotation.** Fit real's PCA frame `V_real` on
  TRAIN rows only (blake2b(i)%4 ∈ {0,1}); fit the generator's own frame
  `V_gen` on its base; apply the orthogonal map `Q = V_real·V_genᵀ`
  (variance-rank matched) to every generated row. A pure rotation:
  every battery-A statistic is exactly invariant; battery B sees the
  cloud along real's principal directions.
* **M2 — mean restoration (dose-swept).** Real's cloud has a large mean
  (baseline cosine 0.228); the generator's is centred. Add
  `β · m_real` before normalization, β ∈ {0, 0.5, 1.0}. NOT
  A-invariant — the A-side cost is measured, not assumed.

## 2. Registered predictions and kills

* **P1:** rotation alone moves battery-B g1 from ×5.6–6.3 toward 1 and
  g8@B off the floor; mean restoration closes the rest. **Kill:** if
  g1@B stays > ×2 at all (Q, β), query-realism is beyond
  train-fittable linear maps and battery B needs its own mechanism
  class (recorded, campaign stops).
* **P2 (guard):** rotated-only arms reproduce r101's battery-A cells
  bit-nearly (invariance verified empirically, not assumed); β > 0
  A-costs reported per gate.
* Residuals G2 (small-n heat) and G6-deconvolution are Phase B, after
  the B-battery picture settles.

## 3. Protocol

Validation-stage throughout (sealed rows excluded; spends nothing).
Real cells reused from `results/r101_cells.json`; candidate cells
measured identically; `score_rc1` arithmetic. One sweep (3 candidate
variants × full grid × 5 subsamples); Phase B ≤2 sweeps. The seal stays
closed until the battery passes on validation. Budget so far: 0.
