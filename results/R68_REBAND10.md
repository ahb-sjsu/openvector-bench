# R68 / RC-3 Phase 0: ten-block bands — real is more heterogeneous than any prior band admitted

**Registered as RC-3's targets before any RC-3 generator arm runs.**
Measured 2026-08-13 on Atlas GPU 1. Ten contiguous 600k blocks: the four
RC-2 held-out offsets (5M/15M/25M/39M) plus six fresh (3M/10M/18M/21M/28M/
32M). Record `results/reband10.json` (per-block panels + mean ± 2 sd
bands). Driver `harness/rc1/rc2_real.py` protocol, unchanged.

## Real's block-to-block spread, n = 10

| statistic | 4-block held-out band | **10-block band** | sd 4 → 10 |
|---|---|---|---|
| g1 | [15.04, 19.08] | **[14.44, 21.03]** | 1.01 → 1.65 |
| g5 | [1.362, 1.397] | [1.362, 1.407] | 0.009 → 0.011 |
| g6 | [1.711, 1.748] | **[1.702, 1.789]** | 0.009 → 0.022 |
| g3 | [159.6, 200.7] | [153.6, 196.5] | 10.3 → 10.7 |
| g4 | [352.1, 363.9] | [351.3, 362.7] | 2.9 → 2.8 |
| g8 | [0.731, 0.741] | [0.731, 0.743] | 0.003 → 0.003 |
| §3 trend | [0.455, 0.658] | [0.390, 0.648] | 0.051 → 0.064 |
| §3 G1 exp | [−0.243, −0.127] | [−0.236, −0.112] | 0.029 → 0.031 |
| rspan | [1.938, 2.646] | **[1.086, 2.938]** | 0.177 → 0.463 |
| gspan | [−0.590, −0.396] | **[−0.630, −0.261]** | 0.049 → 0.092 |

Blocks 21M and 32M are the finding: g1 ≈ 20.1–20.3 with rspan 1.04–1.42 —
regions of the corpus that look weakly articulated (high fine-scale
dimension, weak density response), presumably list/stub-heavy Wikipedia
ranges. Real's density response varies **2.4×** across blocks. g4 and g8
are real's most stable statistics (sd 2.8 rows and 0.003 respectively at
n = 10) — misses on those are meaningful; narrow misses on rspan-like
statistics never were.

## The frozen generator against the ten-block bands

Post-hoc observation — the RC-2 verdict stands as registered under its
pre-declared four-block bands; this is what the same evaluation looks like
under bands that respect real's measured heterogeneity:

| criterion | 10-block band | frozen | verdict |
|---|---|---|---|
| g1 * | [14.44, 21.03] | 16.31 | IN |
| g5 * | [1.362, 1.407] | 1.377 | IN |
| g6 * | [1.702, 1.789] | 1.773 | **IN** (was out) |
| g3 | [153.6, 196.5] | 155.0 | **IN** (was out) |
| g4 | [351.3, 362.7] | 448 | out (+23%) |
| g8 | [0.731, 0.743] | 0.723 | out (−0.008) |
| §3 trend | [0.390, 0.648] | 0.377 | out (−0.013) |
| §3 G1 exp | [−0.236, −0.112] | −0.090 | out (+0.022) |
| rspan | [1.086, 2.938] | 4.386 | out (+1.45) |
| gspan | [−0.630, −0.261] | −0.271 | **IN** (was out) |

**The mandatory trio is jointly in band for the first time in the
campaign's history**, and the residual misses collapse onto the rank-level
cluster `RC3_PLAN.md` §2 hypothesizes about: g4 large and robust, rspan
large, g1exp/trend/g8 small. RC-3's Phase B is aimed at exactly that
cluster, judged against these bands.

## Consumed offsets ledger

0; 1,067,268; 3M; 5M; 7,228,966; 10M; 15M; 18M; 21M; 25M; 28M; 32M;
34,414,820; 39M (each +600k rows). Everything else in [0, 41M) remains
untouched for the RC-3 one-shot.
