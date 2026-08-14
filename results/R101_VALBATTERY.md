# R101: the original battery on validation rows - battery B is the unseen wall, and it has a licensed door

**Validation-stage, spends nothing sealed.** The full PREREG section-5
battery (8 gates, batteries A+B, (n,k) grid, 5 subsamples, sealed rows
excluded per blake2b%4==3) on S1 vs real. Records `results/r101_cells.json`,
`r101_scores.json`. Verdict: **not admitted (9/24 cells)** - and the
composition redraws the project's map:

* **Battery A (corpus-side, the domain of all 17 modern campaigns) is
  nearly clean under the REGISTERED bands**: g1/g3/g5/g8 12/12, and
  **g4 12/12** - the original +-20% band admits our 1.18 ratio; the
  block-band protocol was stricter than the registered rule on the one
  gate we recorded as structural. Residuals: G2 ball-growth hot at small
  n (3/12, 1.14-1.54), G6-deconvolved noisy (1/12 - the amended
  estimator sees through the raw skew the panel matched), G7 9/12.
* **Battery B (real queries vs the synthetic corpus) fails
  catastrophically and structurally**: g1 x5.6-6.3, g2 x5.5-7.4, g7
  x2-4.4, g8 0.07-0.18. Real query vectors are out-of-distribution for
  any cloud built on random frames - they land far from every synthetic
  subspace, neighbourhoods degenerate. No internal-geometry campaign
  could see or touch this.
* **The licensed door**: section 7's train split exists to fit
  distributional parameters. A train-fitted ROTATION aligning the
  generator's variance-ranked directions to real's principal frame is a
  pure orthogonal map - every battery-A statistic is exactly invariant -
  while making real queries in-distribution. RC-13: alignment + G2
  small-n + the G6-deconvolution study, iterated on validation rows,
  then the battery re-run; the seal stays closed until it passes.

Seal status: **not opened; opening today would fail admission.** The
two-stage seal reading stands (section-5 admission separable from the
section-6 ANN battery, which waits on scatter regardless).
