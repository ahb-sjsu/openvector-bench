# The registered gates, measured at last: two of three mandatory pass, and the family is too low-rank

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/gates_probe.py`; records
`results/gates.json`, `gates2.json`. Follows `R36`.

## Why this was overdue

Rounds 29–36 optimised `PROFILE.md` §3b and never once evaluated
`PREREG_RC1`'s eight registered gates on the family. That is the `R27` failure
mode by construction — match the scored statistic through a mechanism the
unscored ones would reject — and it went unchecked for eight rounds.

Protocol as registered: 200,000 base rows, 10,000 held-out queries from the same
region, k = 10.

## Result

| gate | real | composed fd22 | log-ratio |
|---|---|---|---|
| **g1 id_twonn** * | 17.228 | 17.603 | **+0.02** |
| **g6 hubness_skew** * | 1.696 | 1.597 | **−0.06** |
| **g5 relative_contrast** * | 1.369 | 2.522 | **+0.61** |
| g2 id_ballgrowth | 5.495 | 4.759 | −0.14 |
| g3 eff_rank | 182.295 | 71.359 | −0.94 |
| g4 dims90 | 359 | 90 | −1.38 |
| g7 local_id_iqr | 12.180 | 4.814 | −0.93 |
| g8 pca_retention | 0.730 | 0.993 | +0.31 |

Two of the three mandatory gates land — g1 within 2%, g6 within 6% — which is
not nothing given they were never targeted. **g5 relative contrast fails at 1.8x
real**, and it is mandatory.

The dominant defect is elsewhere and is structural: **the corpus is far too
low-rank.** Real needs 359 dimensions for 90% of its variance and has effective
rank 182; the family needed 90 and had 71.

## The diagnosis: intrinsic dimension is not ambient dimension

Real has intrinsic dimension ~36 (`R33`) yet spreads over 359+ PCA dimensions.
Those are only compatible if real is a low-dimensional manifold embedded
**nonlinearly** in a high-dimensional space.

Every construction in this family placed points in a *fixed* linear subspace, so
its intrinsic and ambient dimensions coincide by definition. The §3b work could
not have surfaced this: the profile is a neighbourhood statistic and is blind to
how the neighbourhoods are oriented relative to each other. g3, g4 and g8 see
exactly that, and g5 follows — a low-rank corpus has inflated distance contrast.

## The fix, and how far it goes

Giving each super-cluster and each article its **own** orientation, drawn from a
shared direction pool, so that a union of randomly-oriented low-dimensional
patches spans the ambient space while each neighbourhood stays low-dimensional:

| gate | real | linear | per-cluster orientation |
|---|---|---|---|
| g4 dims90 | 359 | 90 (−1.38) | **440 (+0.20)** |
| g8 pca_retention | 0.730 | 0.993 (+0.31) | **0.834 (+0.13)** |
| g3 eff_rank | 182.3 | 71.4 (−0.94) | 75.7 (−0.88) |
| g5 relative_contrast * | 1.369 | 2.522 (+0.61) | 2.653 (+0.66) |
| g7 local_id_iqr | 12.18 | 4.81 (−0.93) | 3.86 (−1.15) |
| g1 id_twonn * | 17.228 | +0.02 | +0.04 |
| g6 hubness_skew * | 1.696 | −0.06 | −0.07 |

**It fixes the spectral tail and not the bulk.** `dims90` moves 90 → 440 against
a target of 359, and `pca_retention` more than halves its error, while g1 and g6
are undisturbed. But `eff_rank` barely moves, 71 → 76 against 182.

The two are measuring different things and the split is informative. Variance
remains concentrated in the global `d_glob` = 90 subspace, with the per-cluster
orientations adding a long, weak tail — enough to push the 90% threshold out to
440 dimensions, not enough to spread the eigenvalue *mass*. Real distributes its
mass evenly across ~182 effective directions.

g7 also moves the wrong way: real's local intrinsic dimension varies far more
across the corpus (IQR 12.2) than any arm produces (3.9–4.8). The family is too
homogeneous — every article has the same `fil_dim`, every super-cluster the same
`d_loc`, and `size_spread` has been 0 throughout.

## Status

The §3b progress of `R34`–`R36` survives this check: the mandatory neighbourhood
gates g1 and g6 are matched, so the ramp was not bought by breaking them. That
was the specific risk and it did not materialise.

Three defects are now named, with two of them sharing a cause:

1. **g5 relative contrast, mandatory**, 1.8x high — expected to follow the rank
   deficit, untested.
2. **g3 eff_rank**, 2.4x low — variance concentrated in the global subspace.
3. **g7 local_id_iqr**, 3x low — the family is dimensionally homogeneous where
   real is not.

## What is not established

* That fixing eff_rank fixes g5. The link is plausible (low rank inflates
  contrast) and unmeasured.
* Whether spreading the variance can be done without disturbing the §3b profile.
  Earlier sweeps showed `d_glob` moves the s-curve, so these may be in tension —
  the same over-constraint that closed the cascade family in `R33`.
* The per-cluster-orientation arms were measured on gates only. Their §3b spans
  and s(k) curves have not been re-checked, so `R36`'s ramp result does not yet
  carry over to this variant.
