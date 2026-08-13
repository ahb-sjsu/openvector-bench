# RC-3: the one-shot held-out verdict — eight of ten in band, the mandatory trio passes

**Registered round.** Freeze: `spec/RC3_FREEZE.md` (identity `e8423665…`,
seed 2027, expected outcome and 60-arm budget declared first). Records:
`results/rc3_heldout.json` (blocks 8M/13M/23M/37M — untouched by any prior
round), `results/rc3_generator.json`. Measured 2026-08-13 on Atlas GPU 1;
hash verified in-run before the panel.

## The verdict table

| criterion | fresh-block band | frozen D12 | verdict |
|---|---|---|---|
| g1 * (twoNN id) | [15.56, 20.64] | 16.24 | **IN** |
| g5 * (contrast) | [1.320, 1.457] | 1.378 | **IN** |
| g6 * (hub skew) | [1.605, 1.930] | 1.748 | **IN** |
| g3 (eff rank) | [142.0, 212.7] | 149.8 | **IN** |
| g4 (dims90) | [349.9, 365.1] | 417 | out (+15%) |
| g8 (pca ret) | [0.728, 0.744] | 0.742 | **IN** |
| §3 trend | [0.274, 0.681] | 0.387 | **IN** |
| §3 G1 exponent | [−0.204, −0.153] | −0.109 | out (shallow) |
| §3b rspan | [0.525, 3.111] | 1.883 | **IN** |
| §3b gspan | [−0.625, −0.187] | −0.283 | **IN** |

Both misses are the ones `RC3_FREEZE.md` §3 predicted; nothing failed that
was expected to pass. Block 8M is another weakly-articulated region (g1
19.8, rspan 0.88), confirming R68's heterogeneity finding on independent
data — while g4's fresh band stays razor-tight (350–365; it is real's most
stable statistic everywhere we have looked), which makes the generator's
+15% a genuine structural miss, not band luck.

## What this means

* **The mandatory trio g1/g5/g6 passes held-out** — the admission-critical
  criterion no family had ever met on unseen data. Among the measured
  gates the family misses only g4; of the density-response summaries it
  passes trend and both §3b spans, failing only the G1-vs-n exponent.
* **Against RC-2** (same protocol, one campaign earlier): mandatory trio
  failed on g6, 5 of 24 comparisons in band. RC-3: trio in, 8 of 10. The
  distance was covered by two parameters — `pool_alpha 0.22` and
  `seg_break 0.126` — plus honest bands (R68) and the fidelity-corrected
  package family.
* **What remains, precisely**: the PCA tail shape (g4 — under the α
  power-law form, g3/g4/g8 trade along one curve that misses g4 when the
  other two are in) and the G1-vs-n exponent (~−0.11 vs real's ~−0.17).
  The identified untried mechanism for the first is a two-scale pool
  spectral profile; the second likely needs above-article index structure
  (`RC3_PLAN` Phase C, never triggered). Both are recorded for any RC-4,
  not tuned toward here.

## Budget

Disclosed in `spec/RC3_FREEZE.md` §4: 60 RC-3 arms; the fresh blocks and
seed 2027 were touched exactly once — here. Consumed-offset ledger now:
0; 1.07M; 3M; 5M; 7.23M; 8M; 10M; 13M; 15M; 18M; 21M; 23M; 25M; 28M; 32M;
34.41M; 37M; 39M.
