# The registered gates at R58's best point: g5 matched, g1 3.5x low

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12 on NRP A10s. Driver `harness/rc1/gate_check.py`; record
`results/r59.json`. Follows `R58`.

## Why this came before more tuning

`R56`-`R58` tracked only `s(k)` and an inline hubness skew, and `R57` had already
shown a summary can look right while the curve underneath is wrong. Tuning `rms`
further without checking the gates would have repeated that.

The `g1` reported in those rounds was also wrong twice over — `log(2)/mean(log mu)`
where the registered Facco MLE is `n / sum(log mu)` with `mu` trimmed to
`(1, q90]`. It carried a spurious 0.693 factor and no trimming, and was flagged
as non-comparable. This measures the registered estimators exactly.

## Result

| gate | real | br64 dg30 | br64 dg38 | br64 dg45 |
|---|---|---|---|---|
| **g1** id_twonn * | **17.23** | **4.87** | 4.87 | 4.87 |
| **g5** rel_contrast * | **1.369** | **1.354** | 1.359 | 1.352 |
| **g6** hubness * | **1.696** | **1.932** | 1.953 | 1.944 |
| g3 eff_rank | 182.3 | 122.1 | 128.8 | 141.3 |
| g4 dims90 | 359 | 717 | 715 | 717 |
| s(k) rms | — | **5.30** | 5.71 | 6.51 |
| §3b ratio span | +2.397 ± 0.085 | +1.192 | +0.800 | +0.708 |
| §3b log G1 span | −0.494 ± 0.054 | −1.296 | −1.271 | −1.269 |

**`g5` is matched** — 1.354 against 1.369, inside 1.1%. That gate was 1.95x out
through the whole of `R40`-`R43` and was the binding mandatory failure for four
rounds. `g6` at 1.932 against 1.696 is 14% high, the closest it has been while
the profile is also good.

**`g1` is 4.87 against 17.23**, a factor of 3.5, and the `rms` of 5.30 gave no
hint of it. That is exactly the `R57` failure mode, caught here only because the
gates were measured rather than inferred from the curve.

## g1 belongs to the article, not the arrangement

`g1` is **identical to three significant figures across all three `d_glob`
values** while `g3` moves 122 → 141 and the rms moves 5.30 → 6.51. So `g1` is
fixed entirely by the within-article structure — segmentation plus the path — and
the arrangement does not touch it. That is consistent with `g1` being a k = 1,2
statistic.

The reading that follows: the segmentation that filled the k = 14 dip (`R56`) did
so by making nearest neighbours too close. A break resets the shared centre, and
rows *within* a segment then sit closer together than real's do, which drives the
two-NN ratio toward 1 and the MLE toward a low dimension.

That is a mechanism-level tension between two things `R56`-`R58` treated as
independent wins: **the dip and `g1` are both set by the within-segment
geometry**, and the settings that fill the dip depress `g1`.

## The §3b spans are also out

`ratio span` +1.192 against +2.397 ± 0.085, and `log G1 span` −1.296 against
−0.494 ± 0.054 — the latter 2.6x too negative. Both outside their registered
bands, in opposite directions.

Note that the arm with the best `rms` (dg 30) also has the best `ratio span` of
the three (+1.192 against +0.800 and +0.708), so those two do at least move
together here, unlike the ratio in `R57`.

## What is established

* `g5` is reachable and essentially exact (1.354 vs 1.369) at the best-rms point.
* `g6` is 1.932 vs 1.696, its closest while the profile is also good.
* `g1` is 4.87 vs 17.23 and is invariant to the arrangement, so it is a
  within-article property.
* The dip fix and `g1` are in tension: both are set by within-segment geometry.
* `rms` alone does not see the gates — 5.30 with `g1` 3.5x out.

## What is not

* `g1`, `g3`, `g4`, and both §3b spans.
* `g8` pca_retention, not measured: it needs a second full k-NN in PCA space and
  would exceed the ~60 s pod window `R57` established.
* Whether `g1` can be raised without reopening the dip. Nothing was tried; the
  obvious candidate is raising the within-segment spread at fixed break rate,
  which `R55` showed collapses `d50_same` when done through gating but has not
  been tried through the segment path itself.
