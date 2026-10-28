# The round-14 hub-skew slope is partly a file-ordered split

**Exploratory, not a registered round.** No admission claim, seal
untouched. Measured 2026-10-28 on Atlas. Driver and records live in turboquant-pro, branch
`research/hubness-density-ratio` (commit d95daa1): `benchmarks/hubness_campaign_check.py`,
`benchmarks/results/hcc_results.json`. Nothing in this repo has been changed except this file.

## The finding in one paragraph

Real's attractiveness skew was recorded as rising with n at about +0.5 per decade at k = 10
(`PREREG_ROUND14.md` amendment of 2026-08-07, paper Table `tab:invariance` and the paragraph after
it). All three measurements behind that figure come from `harness/rc1/r14_real_targets.py`, and
that script puts its corpus and its queries in different files of the dataset. Shuffling the
same rows before the split removes about half of the rise. What remains is not distinguishable
from zero.

## How the split happens

`load_pool` walks `part_000.npy` to `part_040.npy` in order, takes an equal sample from each and
stops once it has `1.6 * n_max` rows. `main` then takes `pool[:n_max]` as the corpus and
`pool[n_max:]` as the query pool. Because the pool is concatenated in file order, recomputed on
Atlas from the script's own seed and the sealed-row rule:

| measurement | record | corpus rows from | query rows from |
|---|---|---|---|
| narrow ladder, constant ρ (+0.543) | `r14_real_invariant_targets.json` | parts 0–17 | parts 17–27 |
| fixed n_q (+0.474) | `r14_real_fixednq.json` | parts 0–17 | parts 17–27 |
| wide ladder (+0.511) | `r14_real_targets_wide.json` | parts 0–17 | parts 17–27 |

The docstring's intent ("across parts rather than from the head, because the corpus's row order is
topically clustered") is met for the pool as a whole, but not for the corpus/query division inside
it. Queries and corpus are drawn from different stretches of the dataset, which is a query/corpus
distribution shift. The turboquant-pro density-ratio pilot (same date) measured that such a shift
inflates hubness strongly: real queries against held-out corpus rows gave deconvolved skew 6.36
against 2.51 at a matched cell. The shift here is far milder, but it is the same direction.

The three measurements agree to within 0.07, and that agreement was read as confirmation. They
share this split, so the agreement says the slope is reproducible under one sampling operator. It
does not separate corpus structure from the operator. This is the pattern the round-12 review
names: something calibrated under one sampling operator, read as a corpus property.

## The test

`r14_real_targets.py` rerun verbatim at k = 10, ρ = 4, n ∈ {12,500, 25,000, 50,000}, seeds 0–5
(arm "ordered"), and again with the identical 80,000 rows permuted before the split (arm
"shuffled"). Nothing else differs. Seeds 0–2 of the ordered arm reproduce the values in
`r14_real_invariant_targets.json` exactly.

| n | ordered (r14 protocol) | shuffled |
|---|---|---|
| 12,500 | 2.24 ± 0.12 | 2.12 ± 0.11 |
| 25,000 | 2.40 ± 0.04 | 2.23 ± 0.10 |
| 50,000 | 2.53 ± 0.02 | 2.28 ± 0.03 |
| slope per decade (per-seed OLS) | **+0.48 ± 0.17** | **+0.26 ± 0.20** |

## Two further cautions about the recorded slope

1. **The top cell's SE is understated in every ladder.** At n = n_max the corpus is the whole base
   pool, so every seed shares one corpus and only the queries vary. That is why the top cells read
   ± 0.013 (narrow) and ± 0.015 (wide) while lower cells read ± 0.2. The top cell carries the most
   weight in the slope and has the least honest error bar.
2. **The bottom cells sit where the instrument is unstable.** The campaign's own instrument finding
   (2026-08-07) is that attractiveness skew destabilises below n ≈ 12,500 at ρ = 4. The wide ladder
   starts at 6,250, so its lever arm is bought in that region.

Even taking the recorded cells at face value, the narrow-ladder slope with per-seed residuals is
+0.54 ± 0.32 (t = 1.7) at k = 10 and +0.37 ± 0.33 (t = 1.1) at k = 30.

## What stands and what does not

**Stands.** The invariance result: only the Poisson deconvolution returns the same slope under
both budget protocols. That comparison holds the split fixed across the two protocols, so the
split cannot manufacture it. The rule that any cross-n comparison must hold ρ constant or use a
ρ-invariant statistic also stands.

**Does not stand.** The claim that real's hub structure rises with n at +0.51 ± 0.07 per decade as
a corpus property. Under a split that keeps queries and corpus exchangeable, the rise is
+0.26 ± 0.20, not distinguishable from zero on six seeds and three cells. An independent
measurement on `part_000` alone with held-out rows as queries (turboquant-pro pilot, ρ = 2.5,
n 12,500–200,000, k 5–80) found the skew flat at 2.0–2.2 (slope −0.10 ± 0.13 at k = 10).

**Not resolved.** The shuffled arm at n = 50,000 (2.28) still sits about 2.5 SE above the
single-part pilot (2.00 ± 0.11). The likely difference is drawing from about 28 parts against one,
which has not been tested.

## Places that cite the figure (for the author to decide on)

- `results/PREREG_ROUND14.md`, the 2026-08-07 amendment and the "Confirmation over a wider ladder"
  table, which set the P-14B target at +0.51/decade with ± 0.15 tolerance.
- `paper/bond_metric/main.tex`, Table `tab:invariance` (the invariance comparison itself is
  unaffected) and the following paragraph, which states that the real corpus's skew rises with n.
- `results/R15_CODEBOOK_GATE.md` line 87 and `results/R17_STAGE0_RESULT.md` (the "+0.51 real"
  comparison, 3.6 SEM from the round-8 family), which compare candidates against the figure.

## Suggested next measurement (not run)

The decisive version is a registered rerun of `r14_real_targets.py` with the pool permuted before
the split, at least 10 seeds, n from 12,500 to 100,000, and a pool larger than `n_max` so the top
cell's seeds draw distinct corpora. A one-line change to `main` (permute `pool` with a fixed seed
before slicing) gives the protocol. Whether that becomes the round-14 target is the author's call.
