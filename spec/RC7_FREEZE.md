# RC-7 freeze declaration: the geometric-only bar, re-registered

**Status: FROZEN as of 2026-08-14, before any held-out evaluation.**
Written under the same binding rules as `spec/RC2_FREEZE.md` and
`spec/RC3_FREEZE.md`. Prior identities and verdicts are unchanged.

## 1. The bar, and why it is re-registered

`RC7_PLAN.md` Phase D registered a joint bar: robust geometry **and** the
ANN scatter panel. Scatter is unmet and its status is *measured*, not
pending: additive components cannot scatter partitions at
geometry-compatible amplitudes (`RC6_VERDICT`, three forms), and the
continuum's crowding-vs-geometry trade is mapped (`R86`). Holding the
geometric result hostage to an unsolved architecture problem would leave
two confirmed mechanisms (the near-dup ladder, the continuum sheet)
unregistered indefinitely. **This freeze therefore re-registers a
geometric-only bar — declared here, before evaluation, with the ANN
panel still measured and reported (expected np95 ≈ 2–3) so the scatter
deficit is on the verdict's face, not hidden.** The sealed ANN
prediction test and the tier gate are untouched; nothing here ships a
benchmark.

## 2. The frozen artifact

* **Family**: `openvector_bench.segment_corpus`, defaults as committed —
  the RC-3 frozen D12 plus exactly two mechanisms found by RC-6/RC-7:
  `p_dup 0.05` (near-duplicate ladder, `alpha_dup 0.95`, window =
  arr_window) and `w_cont 0.25` (continuum sheet, lat 2, bw 0.5, 3
  octaves, 24 frequencies, frozen cosine table). Bit-exact,
  random-access, chunk-invariant; all tests pass. Prior identities
  recover exactly (RC-3 `e8423665…` at p_dup 0/w_cont 0; RC-2
  `80d94f61…` additionally at seg_break 0.116/pool_alpha 0).
* **Generation seed: 3001** — never used anywhere (campaign: 41, 89,
  137, 271, 1009, 2027; protocol: 2, 5, 7, 31, 61).
* **Byte identity**: `sha256(segment_corpus(defaults, 6000, 1024, 3001))`
  = `fa6342a0193a23ba99a91f17c2a9b9b9224d3a25dee5a5907878b312330144b4`.

## 3. The evaluation, declared before it runs

* **Real side**: four 600k blocks at offsets **6,000,000 / 17,000,000 /
  29,000,000 / 40,000,000** — untouched by any prior round (ledger:
  `RC3_VERDICT` plus none since). Verdict bands: their mean ± 2 sd.
* **Generator side**: ONE evaluation at seed 3001, registered protocol,
  hash verified in-run, ANN panel included for the record. Same
  bug-vs-retune rule as RC-2 §2.
* **Verdict rule**: mandatory g1/g5/g6 against the fresh bands; full
  panel criterion by criterion; verdict reported either way.

## 4. Expected outcome, stated in advance (`R88`)

Nine of ten: g1, g5, g6, g3, g8, trend, g1exp, rspan IN, **gspan IN
under a typical fresh band** (every fresh gspan band drawn to date has
been wider than the tuning band — RC-3's was [−0.625, −0.187] against
F8's −0.19…−0.21), g4 out (~426 vs ~352–365, structural). Stated risks:
a narrow fresh gspan draw puts gspan out (→ 8/10); g1exp's margin is
0.009–0.019 against fresh-band drift. np95 ≈ 2–3, reported as the known,
measured scatter deficit.

## 5. Search budget

RC-6: 64 arms; RC-7: 44 (32 harness + 12 package incl. R85 extensions);
R80: 5 index builds. Cumulative disclosures: `RC2_FREEZE` §4,
`RC3_FREEZE` §4. Consumed real offsets: eighteen (ledger in
`RC3_VERDICT`); the four above and seed 3001 were touched by nothing.
