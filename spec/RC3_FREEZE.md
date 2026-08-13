# RC-3 freeze declaration and budget disclosure

**Status: FROZEN as of 2026-08-13, before any held-out evaluation.** Written
under the same binding rules as `spec/RC2_FREEZE.md`; the RC-2 verdict and
identity are unchanged and remain recoverable from this package.

## 1. The frozen artifact

* **Family**: `openvector_bench.segment_gen.segment_corpus`, defaults as
  committed — the RC-2 frozen V1 plus exactly two changes found by the
  RC-3 campaign: `pool_alpha 0.22` (power-law pool amplitude profile, the
  `R70` mechanism) and `seg_break 0.126` (the `R71` pocket). All other
  parameters untouched. Deterministic, bit-exact, chunk-invariant,
  random-access; all tests pass; the RC-2 identity reproduces at its own
  parameters (`80d94f61…`).
* **Generation seed: 2027** — never used anywhere (campaign used 41, 89,
  137, 271, 1009; protocol seeds 2, 5, 7, 31, 61).
* **Byte identity**: `sha256(segment_corpus(defaults, 6000, 1024, 2027))` =
  `e84236658665bc2d1377223877e88c107f0d5851b1e8c62dc3a3d226f4e1a6c5`.

## 2. The evaluation, declared before it runs

* **Real side**: four 600k-row blocks at offsets **8,000,000 / 13,000,000 /
  23,000,000 / 37,000,000** — untouched by any prior round (consumed
  ledger: `results/R68_REBAND10.md`). Primary verdict bands are these four
  blocks' mean ± 2 sd; the R68 ten-block bands (which the candidate WAS
  tuned against, and which are therefore not held out) are reported as
  secondary context only.
* **Generator side**: ONE evaluation at seed 2027, 600k rows, registered
  protocol, hash verified in-run. Same bug-vs-retune rule as RC-2 §2.
* **Verdict rule**: mandatory g1/g5/g6 against the fresh-block bands, the
  full panel reported criterion by criterion, verdict stated either way.

## 3. Expected outcome, stated in advance (`R74`)

Seed-robust at the ten-block bands and therefore expected here, modulo
fresh-block drift: g1, g5, g6, g8, §3 trend, rspan, gspan IN; g3 ~150
(−2 to −3%), g4 ~417 (+15%), g1exp ~−0.104 (shallow by ~0.01) out. The
known risk is fresh-block drift itself — R68 showed four-block bands are
narrow, and g8/gspan sit near edges. The identified-but-untried mechanism
for the g3+g4+g8 joint (they trade along one curve under the α form) is a
two-scale pool spectral profile; it is future work, not this freeze.

## 4. Search budget

RC-3 campaign: 60 arms (Phase A 4, Phase B 16, Phase C 30 across two
sweeps, package verification 4, pre-freeze 6), all recorded in
`results/R69`–`R74`. Prior arcs: as disclosed in `spec/RC2_FREEZE.md` §4.
Consumed real blocks: fourteen offsets (ledger in `R68`), none of them the
four above. The ten-block bands guided tuning; the fresh blocks and seed
2027 were touched by nothing.
