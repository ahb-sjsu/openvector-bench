# R102: alignment halves the wall, and the mean fixes G2

**Validation-stage.** RC-13 Phase A (`RC13_PLAN.md`): train-fitted
principal-frame rotation + mean restoration, three variants, full
registered battery vs the r101 real cells. Records `results/r102_*`.

* **Battery-A invariance of the rotation: verified exactly** (the rot
  arm's A-cells reproduce r101's raw values digit for digit).
* **Battery B moves massively, does not close**: g1@B x5.6-6.3 -> x2.6
  (rot+mean), g8@B 0.07 -> 0.77 (rot; the mean costs a little here),
  g2@B x7 -> x1.7-2.1, g7@B -> x1.0-2.1, g5@B 12/12.
* **The gift: mean restoration fixes G2@A** (3/12 -> 11/12, 1.08-1.20)
  - the corpus-side ball-growth heat was a missing-mean artifact.
* **P1's registered kill fires on the declared (Q, beta) space**: pure
  A-invariant maps bottom out at g1@B x2.6. The residual is the variance
  PROFILE along the aligned axes (rank-matched, magnitude-unmatched).
  Phase B: partial spectral matching s_i^gamma (train-fitted, linear,
  NOT A-invariant - its A-cost measured against A's known margins), plus
  the G6-deconvolution study (untouched by alignment, 1/12 both
  batteries, the remaining mandatory blocker).

Counts: raw 9/24 -> rot 9/24 -> rot+mean 12/24. Seal: closed.
