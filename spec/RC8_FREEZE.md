# RC-8 freeze declaration: the eight-block re-verdict of F8

**Status: FROZEN as of 2026-08-14, before any held-out evaluation.** The
first round run under `RC7_VERDICT`'s binding rule: held-out draws are
registered at ≥ 8 blocks before the freeze. Written under the same
binding rules as the prior freeze documents.

## 1. What this round is, and is not

`RC7_VERDICT` excluded the frozen F8 at 5/10 under the narrowest
four-block draw in the project's history, with the generator's own
statistics inside seed noise of their in-sample values. The diagnosis —
verdict variance in the sample of a heterogeneous corpus — is itself
testable: **the same frozen artifact, evaluated once against an
eight-block draw, should score near its in-sample robust 8/10.** This
round runs that test. It is a new one-shot with a new seed against new
blocks; it does not retract RC-7 (which stands as registered), and no
parameter of the artifact has moved since `spec/RC7_FREEZE.md`.

## 2. The frozen artifact

Unchanged from RC-7: `openvector_bench.segment_corpus` at its committed
defaults (F8). **Generation seed: 4001** — never used. Byte identity:
`sha256(segment_corpus(defaults, 6000, 1024, 4001))` =
`115682bdb4339ca528a115dd17ebf5cc886fe172b71d21be300171b417f66db0`.

## 3. The evaluation, declared before it runs

* **Real side**: EIGHT 600k blocks at offsets **2M / 9M / 12M / 16M /
  20M / 24M / 30M / 36M** — all untouched (post-RC7 ledger). Bands:
  mean ± 2 sd across the eight. Ten clean slots remain after this draw.
* **Generator side**: ONE evaluation at seed 4001, registered protocol,
  hash gate, ANN panel reported (expected np95 ≈ 2–3, the declared
  deficit).
* **Verdict rule**: as always — mandatory g1/g5/g6, full panel, verdict
  either way.

## 4. Expected outcome, stated in advance

Generator values within seed noise of `R88` (the family is
seed-deterministic). Eight-block bands should approximate the 14-block
tuning bands in width. Expected: **8/10** — g1, g5, g6, g3, g8, trend,
g1exp, rspan IN; g4 out (structural); gspan out (the registered dup
cost) unless the draw includes weak-response regions, in which case
9/10. Risks: a draw skewed as RC-7's was (probability much reduced at
n = 8 but not zero); g1exp's thin margin.

## 5. Budget

One evaluation. Prior disclosures: `RC2`/`RC3`/`RC7` freeze documents.
Seed 4001 and the eight offsets above were touched by nothing.
