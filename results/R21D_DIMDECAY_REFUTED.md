# The cascade's per-level dimension decay is refuted, structurally

**Exploratory, not a registered round.** Train/validation only, seal untouched,
no admission claim. Measured 2026-08-08 on Atlas (CPU, 20 threads). Driver
`calib_dimdecay.py`, record `/home/claude/ovb_scale/calib_dimdecay.json`.

## What was tested

`R21C_FILAMENT_CALIBRATION.md` excluded the filament family because one
characteristic scale saturates, and concluded the target needs structure at
every scale with dimension DECREASING toward finer scales — a hierarchy with a
per-level dimension decay. That is `bitmap_gen`'s `dim_decay`, which had never
functioned, for two separately-diagnosed reasons whose union left one regime
untested: **moderate amplitude decay with a zero noise floor.**

Registered prediction: if the level at the separating depth dominates, then
`s_lo ~ m0 * exp(-dd * l*)` with `l* ~ log_B n`, so

    dlog(s_lo)/dlog(n) = -dim_decay / ln B = -1.443 * dim_decay   (B = 2)

Registered falsifier: dead if `s_lo`'s n-exponent stays >= 0, **or** if it is
negative but flat in `dim_decay` (truncation again, which looks superficially
like success).

## Result: the falsifier fired on its second clause

| dim_decay | exp(s_lo) measured | predicted | exp(G1) |
|---|---|---|---|
| 0.00 | −0.088 | −0.000 | −0.011 |
| 0.10 | −0.068 | −0.144 | −0.015 |
| 0.20 | −0.047 | −0.289 | −0.018 |
| 0.35 | −0.029 | −0.505 | −0.019 |

*(real: s_lo −0.268, G1 −0.168)*

The exponent is negative but **flat in the knob, and anti-correlated with it** —
raising `dim_decay` makes it *less* negative where the prediction says it should
become sharply more negative. G1 barely drifts at all (−0.015 against −0.168).

## The structural reason, and it is the useful part

Amplitude decay collapses the corpus:

| scale_decay | G1 | radius band | mu_ok |
|---|---|---|---|
| 1.00 | 78.4 | 1.232 .. 1.331 | 1.00 |
| 1.15 | 6.4 | 0.215 .. 0.619 | 1.00 |
| 1.30 | 3.4 | 0.043 .. 0.297 | 0.99 |
| 1.60 | 2.2 | 0.003 .. 0.085 | 0.85 |
| 2.00 | 2.8 | 0.000 .. 0.022 | **0.18** |

**In a cascade the neighbour distance IS the tail energy.** Amplitude decay is
precisely what makes level `l*` dominate the local dimension, and it is the same
quantity that sets how far apart neighbours are. Two rows sharing a long prefix
differ only in levels below `l*`, whose summed energy the decay has already
driven to nothing — so they become near-duplicates. G1 falls to ~3 and the
corpus is a pile of duplicate clusters, not a spread geometry.

The two regimes are exhaustive and both fail:

* **`scale_decay` = 1** — sane radii, but every level contributes equally, so a
  neighbour difference spans the whole tail, `dim_decay` is swamped and the
  drift is finite-depth truncation (`R21_BITMAP_PROBE`).
* **`scale_decay` > 1** — level `l*` dominates as designed, but distances
  collapse and the geometry degenerates.

There is no middle setting, because the mechanism that produces level dominance
is the mechanism that destroys the distance scale. This closes the hierarchical
cascade direction, not just this parameterization.

Caveat: the explanation above is post-hoc. The measurements are solid; the
mechanism story would need its own test before being relied on.

## Instrumentation note

The per-cell estimator domain check — the precondition `R20_CONVERGENCE.md`
named as missing — flagged `usable_mu_frac` = 0.18 at `scale_decay` 2.0, so
those cells are known-unreliable rather than being read as data. This is the
first round in the campaign where the domain check ran *before* conclusions were
drawn from a cell.

## Predictive track record, recorded deliberately

Three quantitative models of this family have now been advanced and all three
were wrong: the tail-sum model (predicted dd=0.12 would give dimension ~19
against dd=0's ~231; measured ~23 for both), the truncation model (right in
form, wrong by a constant factor ~1.6), and `-1.443*dd` above. The family's
qualitative failures have been diagnosable after the fact every time and
predictable in advance none of the time. Any further work on cascades should
treat analytic predictions about them as hypotheses to test cheaply, never as
grounds for designing an expensive round.
