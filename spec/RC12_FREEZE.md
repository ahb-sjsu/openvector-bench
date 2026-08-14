# RC-12 freeze declaration: the echo-cell one-shot — the final eight-block draw

**Status: FROZEN as of 2026-08-14, before any held-out evaluation.**
Operator-authorized use of the last full eight-block draw. Written under
the binding rules of the prior freeze documents; the ≥8-block rule
(`RC7_VERDICT`) applies.

## 1. The frozen artifact

* **Family**: `openvector_bench.segment_corpus` with the R1 parameters
  over the committed defaults: `p_dup 0, p_echo 0.11, echo_k 3,
  echo_win 100000, echo_alpha 0.96, pool_alpha 0.23, seg_break 0.138`
  (all other parameters the F8 defaults). This is the RC-11 echo
  mechanism — small window-local near-parallel groups — at the RC-12
  re-centred operating point (`R96`–`R99`: robust 9/10 vs tuning bands
  at 3 of 4 seeds, the first ever).
* **Generation seed: 5001** — never used. **Byte identity**:
  `sha256(segment_corpus(params, 6000, 1024, 5001))` =
  `60dfb49f6e4456b43e3fe4e93e386c804d2cd8d55bd6d242795d046bd9f06109`.

## 2. The evaluation, declared before it runs

* **Real side**: EIGHT 600k blocks at offsets **4M / 11M / 14M / 19M /
  22M / 26M / 31M / 38M** (27M and 33M remain as the corpus's final
  reserve). Bands: mean ± 2 sd across the eight.
* **Generator side**: ONE evaluation at seed 5001, registered protocol,
  hash gate, ANN panel reported (expected np95 ≈ 10–15, a real
  improvement over 2 and short of real's ~50 — declared as such).
* **Verdict rule**: mandatory g1/g5/g6, full panel, verdict either way.

## 3. Expected outcome, stated in advance (`R99`)

**Seven to eight of ten.** Expected IN: g1, g6, g3, g8, **g1exp
(−0.195…−0.206)** and **gspan (−0.41…−0.43)** — the two structural
density residuals held-out in band for the first time in the project's
history, the declared point of this round. Expected out: g4
(structural) and **rspan** (0.93–1.14 vs real's fresh floor ~1.35 — the
echo mechanism's one structural cost, present at any effective dose).
Coin-flips: g5 (±0.002 of the eight-block edge) and trend (mean 0.588
vs fresh bands ending near 0.60). An 8/10 with the density residuals in
supersedes every prior verdict; a 7/10 still certifies the density
response held-out.

## 4. Budget

RC-11: 32 arms; RC-12: 16 arms + 14 package verification runs
(`R97`–`R99`). Prior disclosures in the earlier freeze documents.
Consumed offsets before this round: thirty; seed 5001 and the eight
offsets above were touched by nothing.
