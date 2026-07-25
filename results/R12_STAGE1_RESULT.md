# Round 12 — stage-1 mechanism anatomy sweeps: full-scale result

**2026-07-25, Atlas (GPU kNN, CPU threads capped 16), 6.6 h.** Full prereg
instruments: fit_v10 base (fetched from pod scratch, committed alongside as
[`fit_v10_result.json`](fit_v10_result.json)), architecture removed
(`cloud_mass = dup_mass = 0`), 4-n ladder (25k–200k), 2 subsample draws, 14
settings, scored per cell against the committed 5-draw real reference
([`r11v2_real_ref.json`](r11v2_real_ref.json)), identical subsample operator.
Raw: [`r12_stage1.json`](r12_stage1.json) (336 cells). Driver at `30e7618`.
Compute-route note: prereg's assets line says NRP swarm; run on Atlas instead
(where the r11v2 stage instruments ran and the fit_v10 artifact lives) —
logistics, not protocol.

## Control (fit_v10, architecture removed)

G1 vs real 2.22 → 3.70 across the ladder (**+0.24/decade drift**, the known
wall); S_k 1.25–1.73× real; G3 0.85 (flat, at band edge); Δslope_sk k10 +0.04
(the un-planted fit_v10 baseline nearly matches real's k10 count growth —
consistent with ROUND11_PREFREEZE finding at the k10 small-k margin).

## Sweep G — gradient mechanism (G1 dial)

| setting | G1 vs ctrl | G1 vs real @25k→200k | S_k vs ctrl | G3 vs real |
|---|---:|---|---|---:|
| `grad_decay=0.2` | 0.89–0.93 | 1.97 → 3.43 | 0.79–0.98 | 0.85 |
| `grad_decay=0.4` | 0.67–0.74 | 1.49 → 2.74 | 0.47–0.99 | 0.87 |
| `grad_decay=0.6` | 0.50–0.58 | **1.12** → 2.15 | 0.37–1.11 | 0.88 |
| `grad_span=6` | 1.60–1.73 | 3.56 → 6.40 | 0.63–2.35 | 0.62 |
| `grad_span=15` | 2.14–2.19 | 4.74 → 8.09 | 0.50–2.87 | 0.54 |

- **`grad_decay` is a clean monotone G1 dial** — at 0.6 the reading is nearly
  in band at the 25k end (1.12×) with G3 *improved* (0.88) and G5 drifting up
  moderately.
- **The n-drift is untouched**: every `grad_decay` setting drifts at the
  control's ~+0.24/decade. Anisotropy moves the *level*, not the *flatness*.
- **Not count-quiet at strength**: S_k falls to 0.37–0.47× control at
  0.4–0.6 in the k ≤ 30 large-n cells. At 0.2 it is marginal (0.79–0.98).
- **`grad_span` (patch-wide radial field) is falsified at scale**, decisively:
  G1 moves the wrong way (2.2× control at span 15), count maxima explode (up
  to 10× real), G3 collapses. Same verdict as the screening, now with the
  right base and ladder. The radial-field variant of the gradient mechanism
  is dead; `grad_decay` carries the mechanism.

## Sweep O — renewal occupancy (G6 dial)

| setting | S_k vs ctrl | S_k vs real | G1 vs ctrl | G3 vs real | Δslope_sk (k10/k30/k100) |
|---|---|---|---:|---:|---|
| `occ_tail=1.3` | 0.91–1.09 | 1.11–1.81 | 1.04 | 0.87 | +0.03/+0.13/+0.10 |
| `occ_tail=1.8` | 0.84–1.02 | 1.05–1.70 | 1.01–1.02 | 0.85 | +0.07/+0.15/+0.09 |
| `occ_tail=2.5` | 0.86–1.17 | 1.09–2.00 | 1.00–1.02 | 0.85 | −0.03/+0.09/+0.06 |
| + `dens_span=0.3` | **1.21–1.96** | 1.79–3.20 | **1.02–1.04** | 0.70 | **−0.15/−0.00/+0.08** |
| + `dens_span=0.6` | 1.67–3.49 | 1.98–6.97 | 1.10–1.11 | 0.53 | +0.06/+0.30/+0.34 |
| `occ 1.3, dens 0.6` | 1.52–4.19 | 1.87–7.24 | 1.19–1.20 | 0.36 | +0.17/+0.39/+0.42 |

- **Occupancy re-weighting alone is inert and quiet** (confirms screening at
  scale): iid Pareto weights do not move counts because equalized-scale
  clusters carry no density contrast.
- **`dens_span` is the count dial and its admissible region is real**: at
  0.3 the S_k movement is 1.2–2.0× control with the **ID leak within
  2–4%** (nearly ID-quiet — the H12 decoupling premise holds here), and —
  notably — **Δslope at k30 is 0.00**: the renewal law's level re-expresses
  itself across the ladder at that scale, exactly the subsample-covariance
  the mechanism was designed for. k10 overshoots negative (−0.15), k100 mild
  positive.
- **The cost is G3** (0.85 → 0.70 at dens 0.3; 0.36–0.53 at 0.6): density
  contrast concentrates variance and the post-recolour normalization
  re-couples it. At dens ≈ 0.3 this is plausibly recoverable by re-fitting
  the colouring (a fitted, not structural, parameter); at 0.6 it is not.

## Verdicts against the H12 predictions (draft; nothing frozen)

- **P-B (renewal) — supported in a bounded region.** `occ_tail ≈ 1.8–2.5,
  dens_span ≈ 0.2–0.4` gives a count dial with n-stable level (k30 Δslope
  ≈ 0), thinning maxima, and ≤4% G1 leak. The G3 interaction must enter the
  stage-2 decoupling check and the joint fit must re-tune the colouring.
- **P-A (gradient) — at risk as drafted.** `grad_decay` reaches the G1 band
  at the 25k end but **no setting is n-flat**: the +0.24/decade drift is
  invariant across the entire sweep. If P-A is frozen as "G1 in band across
  the ladder," it fails, and the registered clause fires: *ID pinning in
  this geometry family is inherently [short-range-structure]-driven; aim the
  next round at the ID mechanism alone.*
- **The binding open problem is unchanged and now precisely isolated: G1
  n-flatness.** Neither anisotropy (level dial) nor renewal density (count
  dial) touches the drift. Real's n-flat TwoNN needs neighbour mass at
  graded *sub-patch* scales. A per-row radial law cannot make *pairs*;
  pairs require correlated placement. The natural round-13 candidate,
  consistent with both the renewal principle (scale-free, no fixed owners)
  and round 9's μ-ladder diagnosis, is a **self-similar within-patch point
  process** (multiplicative cascade / cluster-in-cluster), which supplies
  pair distances at every fractional scale and is subsample-covariant by
  construction.

## Status

Stage-1 map complete under the prereg's instruments (§ pre-freeze program,
item 1). Stage 2 (decoupling check at band settings) is well-posed for the
renewal mechanism at `dens_span ≈ 0.3`; for the gradient mechanism the
author's freeze decision should weigh P-A's drift exposure — freezing H12
as drafted converts the drift finding into a registered P-A failure with a
clean redirect. Bands untouched; sealed rows untouched; nothing frozen.
