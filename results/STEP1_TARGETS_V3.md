# Round-9 step 1 — the v3 real targets under the uniform battery-A protocol

**Run:** 2026-07-22→23, Atlas GPU-1, 4.5 h, driver
[`harness/rc1/step1_targets_v3.py`](../harness/rc1/step1_targets_v3.py)
(committed at launch). Full PREREG_RC1 v2 grid — n ∈ {25k, 50k, 100k, 200k}
× k ∈ {10, 30, 100} × 5 subsamples × both batteries × {real + 3 registered
nulls}, non-sealed pool 449,780 rows, explicit seal filter, **uniform**
battery-A holdout for every corpus (the registered fix of
`RC1_ROUND2_CANDIDATE.md` finding 3). Targets:
[`rc1_targets_v3.json`](rc1_targets_v3.json) — the reference set all
round-9 candidate scoring reads, published before any candidate number.

## Real targets at k=10 (subsample means)

| n | A: G1 | A: G6 | B: G1 | B: G6 | G3 |
|---|---:|---:|---:|---:|---:|
| 25k | 26.9 | 1.60 | 59.4 | 12.36 | 179.1 |
| 50k | 22.5 | 1.51 | 60.6 | 14.25 | 179.4 |
| 100k | 19.7 | 1.58 | 59.7 | 17.75 | 179.6 |
| 200k | **18.1** | 1.79 | 62.1 | **20.42** | 180.0 |

## Three findings

**1. Finding 3 confirmed, quantitatively: battery-A hubness was ~6× a
row-ordering leak.** Under first-rows holdout (round-2 targets) real's
battery-A G6 read 9.4–11.4; under uniform holdout it reads **1.5–1.8**.
The old A-side hubness target was almost entirely Wikipedia's topical
ordering smuggling a concentrated query marginal into the
corpus-to-corpus battery. The candidate's round-2 battery-A G6 "failures"
(2.1–4.8 vs 9.4–11.4) were failures to reproduce a protocol artifact.

**2. NEW: real's battery-A intrinsic dimension FALLS with n (26.9 → 18.1)
— the corpus's own short-range ladder, visible.** With uniform corpus-like
queries, densifying the sample brings each query's nearest neighbours into
the graded near-duplicate ladder, driving the two-NN reading *down*. This
is a third independent arrival at the round-9 paraphrase-cloud mechanism
(after the codebook-probe diagnosis and the round-9 probes) — and it
sharpens the round-9 target into a genuinely two-sided constraint: the
candidate must reproduce a **falling A-side G1 (27→18)** and a **flat
B-side G1 (~60)** simultaneously, from one corpus. Uniform-sparse patches
can do neither; a graded ladder plausibly does both (corpus queries fall
into the ladder; the real held-out query set sits at its own
characteristic offset from it).

**3. B-side dynamics confirmed at higher precision.** G1 ≈ 59–62,
n-flat (the round-2 observation stands); G6 grows 12.4 → 20.4
(≈ +0.22/decade, exactly the exponent the round-2 map identified); G3
flat at ≈ 179.5.

## Consequence for round 9

The step-2 screen and step-3 gating (`ROUND9_PREDICTION.md`) now target
the v3 numbers. P1's n-flatness clause applies to battery B as registered;
the A-side falling-G1 profile becomes an additional reported (not yet
registered) discriminator — if the paraphrase-cloud family reproduces it
without tuning for it, that is strong mechanism evidence and will be
reported as such.
