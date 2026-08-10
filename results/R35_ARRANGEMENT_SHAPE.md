# The arrangement's shape is fixable, and what remains is below k=4

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/hier_centres.py`; records
`results/hier_centres.json`, `hier_centres2.json`. Follows `R34`.

## What was broken

`R34` produced the project's first ramp using article-sized groups, and
localised the remaining error to one component: a uniform cloud in a fixed
subspace has a **decreasing** profile at every dimension tried
(`s(500)/s(4)` = 0.87 down to 0.80), where real's cross-article regime
**increases** (1.282). No `arr_dim` fixes a shape problem.

## The structure above the article is not in the row index

Before building contiguous super-blocks, the assumption was checked. Taking one
row per 23-row article from real — 26,087 article representatives — and asking
whether *their* neighbours are article-index-local:

| k | 1 | 4 | 16 | 64 | 200 |
|---|---|---|---|---|---|
| median \|Δ article\| | — | — | 6,637 | 7,004 | 7,179 |
| fraction within 10 articles | — | — | 0.039 | 0.013 | 0.005 |

Essentially uniform over 26,087 articles. **Above the article there is no index
locality at all**, so whatever hierarchy exists lives in embedding space. Super-
cluster assignment must therefore be by hash, not by contiguity — the opposite
of the article level, where contiguity is the whole mechanism (`R30`, `R31`).

This is consistent with `R34`'s gap table, where `frac|Δ|≤1000` was almost
identical to `frac|Δ|≤128`: nothing lives between gap 128 and 1000.

## Hierarchy fixes the direction

A two-level centre cloud — articles assigned to super-clusters by hash, local
offsets in a `d_loc` subspace, super-centres in a wider `d_glob` one — gives
**increasing** profiles where a uniform cloud cannot:

| | s(4) | s(500) | ratio | G1 |
|---|---|---|---|---|
| **real (b=1)** | **27.40** | **35.13** | **1.282** | **26.09** |
| uniform cloud, best `arr_dim` | 36.68 | 29.32 | 0.799 | 54.26 |
| p200 dl64 dg110 w0.4 | **26.43** | **35.06** | **1.326** | 44.80 |
| p200 dl64 dg110 w0.7 | 26.25 | 38.32 | 1.460 | 44.90 |
| p200 dl52 dg110 w0.4 | 23.40 | 36.33 | 1.553 | 38.73 |

`s(4)` within 3.5%, `s(500)` within 0.2%, ratio within 3.4%. **The shape problem
is solved**: the arrangement now has real's cross-article profile across the
whole registered k grid.

## What remains is below k = 4

**G1 measures 44.80 against 26.09** — 72% high — while every point on the k grid
from 4 to 500 matches. G1 is TwoNN, a k = 1,2 statistic, so the residual error
now sits entirely at a scale *finer* than the profile grid resolves.

The diagnostic is that real's G1 and `s(4)` agree closely (26.09 against 27.40)
whereas the synthetic cloud's diverge sharply (44.80 against 26.43). Real is
smooth through k = 1…4; the construction has a dimensional discontinuity there.
That is consistent with real articles having sub-structure — sections, or
adjacent-passage overlap — which a single local offset does not model.

Recording this as the shape of the remaining gap, not as a diagnosis: nothing
here identifies what real does between k = 1 and k = 4.

## The construction is brittle

**Only 12 of 36 arms produced a non-collapsed `s(500)`.** At `per_super` = 600
the profile collapses outright (`s(500)` ≈ 0.4); at 2000 the ratio flips back
below 1. The working region is narrow around `per_super` ≈ 200, and the
parameter is not one `R34`'s measurements constrain — 200 articles per
super-cluster was found by sweeping, not measured from real.

That is a genuine weakness. The article scale of ~23 came from a measured k-NN
gap cliff; the super-cluster scale has no such anchor, and a swept parameter in
a narrow working region is exactly the kind of result that has failed to
transfer before in this project (`R28`, `R30`).

## Status

The arrangement is no longer the blocker. What is now known:

* above-article structure is in embedding space, not row order — measured,
* two-level hash-assigned hierarchy reproduces real's cross-article profile on
  k = 4…500,
* the residual is confined to k < 4 and shows as a G1 discrepancy,
* the super-cluster scale is swept, not measured, and the working region is
  narrow.

## What is not established

* **Nothing has been composed.** These are centre clouds measured alone. Whether
  the full corpus — articles of 23 rows around these centres — reproduces the
  §3b spans or the b=100 regime is untested, and `R34`'s ratio overshoot
  (7.8 against 4.05) is unaddressed.
* Whether the super-cluster scale can be measured from real rather than swept.
  The article scale was readable from a gap cliff; the equivalent for
  super-clusters would need a clustering analysis in embedding space.
* Bit-exactness and random access, untouched since `R32`.
