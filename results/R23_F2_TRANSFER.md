# F2 transfer: the dimension ramp is not Cohere-specific, but it is not universal either

**Exploratory, not a registered round.** Train/validation only, RC-2 seal
untouched, no admission claim. Measured 2026-08-08/09 on Atlas (CPU, 4 threads).
Driver [`f2_three_arm.py`](../harness/rc1/f2_three_arm.py), LeBSE repair
[`lebse_arm.py`](../harness/rc1/lebse_arm.py), record
[`f2_three_arm.json`](f2_three_arm.json).

## Why

`NORMAL_FORMS.md` **F2** is a registered falsification criterion that had never
been tested: *"the selected descriptor predicts within known datasets but fails
on unseen embedding models or modalities — this would make it a benchmarking
heuristic rather than a general theory."*

`R21B_SCALE_DEPENDENCE.md` characterised the target as a rising `s(r)` curve and
six generator families have failed to reproduce it. Before designing a seventh
it is worth knowing whether the ramp is a property of embedding geometry or of
one model. Two independent reviews converged on this as the cheapest experiment
that could kill the encoder-generator route, and it is diagnostic for the
hand-designed search either way.

## Design

Four corpora over **identical passages** at **identical rungs**, so every
difference is the encoder and nothing else. 60,000 Wikipedia passages sampled
600-per-blob across ~100 parquet blobs; rungs n = 12,500 / 25,000 / 50,000;
10,000 held-out queries; k grid 4…500.

| arm | dim | isolates |
|---|---|---|
| cohere (parquet `emb` column) | 1024 | the reference, free |
| LaBSE | 768 | different architecture, objective, training |
| LeBSE v1 | 768 | **same** arch + tokenizer as LaBSE, different training |
| BGE-M3 | 1024 | the registered dim, different family (XLM-R, 24 layers) |

**Headline statistic is the k-matched ratio `s(500)/s(4)` and its n-trend, not
beta.** Beta divides by each corpus's own log-radius span and the corpora occupy
disjoint bands with spans differing up to 6x; that inflates |beta| for
narrow-band corpora and makes cross-corpus comparison unsound. Beta is reported
alongside for continuity only.

## Two bugs found during the run, both recorded because they bit hard

1. **Non-exchangeable base/query split.** Rows arrive blob-by-blob and each
   parquet blob is a contiguous, topically-clustered slice of Wikipedia. Taking
   the query set as the last `NQ` rows drew base and queries from *disjoint
   blobs*. Measured effect: Cohere G1 **65.7** and a falling ratio 0.93, against
   16.1 and a rising 3.34 after permuting. The same defect was present in the
   original `scale_probe.py` and contributed to its discredited numbers. Fixed
   by a fixed-seed permutation before splitting.
2. **LeBSE would not load** — `ModuleNotFoundError: sentence_transformers.base`.
   The published model was saved with sentence-transformers 5.6.0, whose
   `modules.json` names classes under `sentence_transformers.base.modules.*`;
   Atlas has 5.3.0, where they live at `sentence_transformers.models.*`. Weights
   were fine. Repaired by rewriting the four `type` fields on a copy. v2 still
   failed to load after patching, so **v1** was used — which is arguably the
   better arm, since v2 is contrastively fine-tuned
   (`MultipleNegativesRankingLoss`) and would confound domain with objective.

## Results

| arm | dim | ratio @12.5k / 25k / 50k | ratio trend | G1 @50k | G1 exponent | ‖mean‖ |
|---|---|---|---|---|---|---|
| **cohere** | 1024 | 2.28 / 3.34 / 3.73 | **+1.045** | 16.8 | +0.006 | 0.476 |
| **bge_m3** | 1024 | 1.48 / 1.75 / 2.30 | **+0.592** | 21.9 | −0.092 | 0.533 |
| **lebse_v1** | 768 | 0.98 / 1.10 / 1.35 | **+0.267** | 37.9 | −0.111 | 0.462 |
| **labse** | 768 | 1.14 / 1.27 / 1.24 | **+0.072** | 27.8 | −0.106 | 0.458 |

Synthetic reference, measured through the same statistic on the 600k pool
(`scale_probe4.json`): every control flat near 1.2 or below, with |trend| ≤ 0.13
— `bitmap_L90` +0.019, `bitmap_L60` −0.033, `null_gaussian` +0.047,
`null_lowrank` +0.034, `strat_as_built` +0.126.

## Reading

**The ramp is not Cohere-specific.** BGE-M3 reproduces it clearly: ratio
climbing 1.48 → 2.30 with trend **+0.592**, far outside the flat band every
synthetic family occupies. The registered falsification rule — *if no arm
produces a rising ratio strengthening with n, the ramp is Cohere-specific* —
fires the other way. **The property the family search has been chasing for 22
rounds is real and reproducible in a second, independent model.**

**But it is not a generic property of encoders on text.** LaBSE is essentially
flat at **+0.072**, indistinguishable from the bit-cascade and Whitney controls.
"Encode text and you get a rising profile" is false.

**Training data alone moves the profile, within a fixed architecture.** This is
what the LeBSE arm was for, and it is the sharpest result in the table. LaBSE
and LeBSE-v1 are the *same* BERT-base architecture, the *same* 768 dimensions
and the *same* tokenizer; only the training corpus differs. Their trends are
**+0.072 and +0.267** — LeBSE-v1 sits clearly above the synthetic control band
(|trend| ≤ 0.13) while LaBSE sits inside it. Roughly 40% of the LaBSE→BGE-M3 gap
is recovered by changing training data alone.

**So the ramp is graded, not binary, and no single factor explains it.** The
ordering is cohere (+1.045) > bge_m3 (+0.592) > lebse_v1 (+0.267) > labse
(+0.072). An earlier reading of this table — before LeBSE ran — proposed that
the split was dimensional, since both ramping arms were 1024-d. **LeBSE-v1
refutes that as a sufficient explanation:** it is 768-d and still exceeds every
control. Dimension is not necessary. What can be said is that the two strongest
arms are 1024-d and the two weakest are 768-d, while training moves each arm
substantially within its dimension — so dimension and training both contribute
and this design cannot separate their sizes.

**Intrinsic dimension runs opposite to the ramp.** G1 at n=50k is 16.8 (cohere),
21.9 (bge_m3), 27.8 (labse), 37.9 (lebse_v1) — the arms with the *strongest*
ramp have the *lowest* G1. Worth noting because a generator must hit both, and
these two targets may not be independently tunable.

## Limits — three, and the first is serious

1. **The profile is protocol-dependent, and that is a problem for the target
   itself.** Same corpus, same estimator, two sampling schemes:

   | protocol | G1 @25k | G1 exponent | ratio @25k | ratio trend |
   |---|---|---|---|---|
   | 600k contiguous pool (registered) | 25.97 | **−0.168** | 1.29 | +0.511 |
   | 60k spread across ~100 blobs (here) | 16.14 | **+0.006** | 3.34 | +1.045 |

   The arms are internally comparable because they share passages and protocol,
   so nothing above is invalidated. But the absolute values are not comparable
   to the registered anchors, and **the falling-G1 ladder that R19/R20 spent
   three rounds targeting does not reproduce under a diverse draw.** The
   registered protocol takes its pool from the contiguous *head* of a
   topically-ordered corpus; `geometry.py` warns about exactly this hazard for
   the query holdout, but the pool itself is still `cap` contiguous rows. A
   uniform draw from the full 41M rows is the defensible choice and is one run.
2. **No anisotropy controls here.** `‖mean‖` is 0.46–0.53 for every arm, so all
   are strongly anisotropic and it does not separate them — but the exact-
   covariance Gaussian null and the whitened-real re-measurement (the two
   controls that actually close the "it's just the cone" objection) have not
   been run.
3. **Scale and scope.** 60k passages and three rungs, not the registered ladder;
   LeBSE **v1** rather than the current v2; and this says nothing about whether
   an encoder could *serve* as the generator — that route is separately blocked
   on a 1,746x cost inversion that makes regeneration slower than fetching.

## What this changes for the generator search

The target is real and model-general enough to be worth matching, which was not
established before. It is also **graded** — four encoders span trends from
+0.072 to +1.045 — which means the ramp is a continuous property that varies
with both training and architecture rather than a switch that is on for one
model. A generator therefore has a family of targets to aim at, and the
registered Cohere anchor is the extreme end of the observed range, not a typical
value.

The cheapest way to separate dimension from training, now that training is known
to matter: measure two dimensional variants of one model family (e.g. `bge-m3`
against a 768-d sibling trained on the same data), which holds training fixed
while moving dimension — the mirror of the LaBSE/LeBSE contrast that held
architecture fixed while moving training.

Nothing here is an admission claim, and `s(r)` remains unregistered in `spec/`
— usable as a fitting signal, not yet as a published claim.
