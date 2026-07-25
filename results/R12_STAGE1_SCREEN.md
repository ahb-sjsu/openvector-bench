# Round 12 — stage-1 SCREENING smoke: mechanism responses, first read

**2026-07-24, local workstation. Screening, disclosed per campaign practice — NOT
calibration evidence.** Single seed, single subsample draw, two-point ladder
(n ∈ {25k, 50k}), reduced pool (90k; grid thinning factors therefore differ from
the §5 convention), and the **committed fit_v9 params as base** (`fit_v10_result.json`
is pod scratch and is not committed), so *absolute* ratios are not comparable to the
round-11 fit_v10 baselines — only the **relative mechanism responses (vs the
architecture-removed control)** are the readings here. Driver:
[`harness/rc1/r12_stage1.py`](../harness/rc1/r12_stage1.py) (committed defaults are
the full grids/ladder for the freeze-candidate sweep); raw cells:
[`r12_stage1_screen.json`](r12_stage1_screen.json); scoring instrument: the committed
5-draw real reference ([`r11v2_real_ref.json`](r11v2_real_ref.json)), identical
subsample operator.

Operating point: `cloud_mass = dup_mass = 0` (the round-12 architecture removal),
mechanisms per setting. Family: `hier_r12_corpus` (byte-identical to round 10 at
default knobs; regression-tested).

## Mechanism responses (vs the shared control, mean over k where flat)

| setting | G1 vs ctrl | S_k vs ctrl (k10/k30/k100) | G3 vs real | G5 vs real |
|---|---:|---|---:|---:|
| control (arch off) | 1.00 | 1.00 | 0.71 | 1.21 |
| `grad_decay=0.4` | **0.66–0.70** | 0.63 / 0.59 / 0.70–1.42 | 0.74 | 1.30–1.36 |
| `grad_span=10` | **1.95 (wrong way)** | 1.75 / 1.14–1.33 / 0.59–0.72 | 0.47 | 1.66–1.71 |
| both | 1.26–1.33 | 1.28 / 0.98–1.09 / 0.59–0.67 | 0.48 | 1.67–1.75 |
| `occ_mix=1, occ_tail=1.3` | 1.03 | **0.91–1.06 (inert)** | 0.73 | 1.21 |
| + `dens_span=0.6` | 1.16–1.20 | **2.77–2.87 / 2.22–2.45 / 1.63** | 0.32 | 1.35–1.38 |

Control G1 vs real: 2.28 (25k) → 2.80 (50k) — the arch-removed baseline reproduces
the known upward G1 drift (~+0.30/decade in the ratio) and sits above the S_k band
(1.3–1.7× real), consistent with ROUND11_PREFREEZE at a different base.

## Findings

- **F1 — `grad_decay` is a real, correctly-signed G1 dial** (0.66× control at 0.4;
  monotone direction as designed) — the anisotropic axis profile moves TwoNN down
  without near-duplicate owners. **But (a) it does not cure the n-drift** (relative
  drift across the octave ≈ control's), and **(b) it is not count-quiet at this
  setting** (S_k −35–45% at k ≤ 30 — well beyond plausible draw noise). P-A as
  drafted ("without moving S_k beyond draw noise") is at risk at strong settings;
  the admissible region, if any, is at smaller `grad_decay`.
- **F2 — `grad_span` (patch-wide radial density field) is falsified as an
  ID-pinning mechanism as implemented**: it moves G1 the *wrong way* (×1.95
  control; 4.4–5.5× real) — a patch-wide scale mixture behaves like transverse
  noise (readings toward ambient), not like the short-range μ ladder round 9
  diagnosed. It also degrades G3 (0.47× real) and G5. The prereg's gradient
  mechanism should freeze `grad_decay` as its core knob; a μ-ladder mechanism, if
  reintroduced, must put graded mass at *sub-patch* scales rather than spreading
  the patch itself.
- **F3 — renewal occupancy alone is inert at ladder scale** (S_k 0.91–1.06×,
  G1 1.03× control): the toy-scale ID leak (0.77×, `tests/test_generator_search.py`)
  does **not** persist at n ≥ 25k in 1024-d, and neither does any count response.
  Occupancy re-weighting without density contrast is not a dial.
- **F4 — `dens_span` is the count dial, and it is strong**: S_k 2.8× control at
  0.6 (overshooting real by 2.2–4.4×), with a moderate G1 leak (+16–20%) and a
  **severe G3 interaction** (0.32 vs control's 0.71 — density contrast concentrates
  variance and the post-recolour normalization re-couples it). The admissible
  region is at substantially smaller `dens_span`; the G3 interaction must be in
  the stage-2 decoupling check.
- **F5 — no screened setting matches real's S_k growth** (Δslope +0.09 to
  +0.38/decade at k10/k30 where the level is near band) — but a two-point,
  one-draw ladder cannot support slope conclusions; this is what the full 4-n,
  multi-draw sweep is for.

## Status

Screening only; nothing here freezes PREREG_ROUND12 or amends its bands. Read
against H12: both mechanism *directions* exist (F1, F4) — the decoupling premise
survives screening — but neither mechanism is quiet at the screened strengths
(F1b, F4), so the stage-2 decoupling check will bind at *calibrated small*
settings, and the H12 count-tail claim rests on `dens_span` (density contrast),
not on occupancy re-weighting per se (F3). The full stage-1 sweep (committed
grids, 4-n ladder, ≥2 draws, fit_v10 base from pod scratch) runs on NRP per the
prereg's compute rule.
