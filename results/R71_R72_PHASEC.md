# RC-3 Phase C: the triangle threads at α ≈ 0.22, brk ≈ 0.126 — and α × lp puts g4 in band

**Exploratory, not a registered round.** Measured 2026-08-13 on NRP A10s
(two indexed jobs: 14/16 arms `R71` — two lost to a driver seed-collision
bug, grid unaffected — and 16/16 arms `R72`). Drivers
`harness/rc1/phasec.py`, `phasec2.py`; raw `results/r71.txt`, `r72.txt`.
Harness generator against the R68 ten-block bands; package fidelity
offsets (g3 +30, rspan +1.0, g1exp ~+0.02) mean band-edge calls belong to
the package verification (`R73`).

## The pocket: trend, g1exp and rspan co-hold for the first time

| arm | trend [0.390, 0.648] | g1exp [−0.236, −0.112] | rspan | g8 | in-band |
|---|---|---|---|---|---|
| C5 α0.24 brk0.128 | **+0.428** | **−0.117** | **+1.43** | 0.745 (−0.002 out) | 8/10 |
| C1 α0.20 brk0.122 | **+0.417** | −0.111 (0.001 out) | **+1.88** | **0.738** | 8/10 |
| D12 α0.22 brk0.126 | +0.372 | **−0.113** | **+1.53** | **0.742** | 8/10 |

The RC1-era conflict — trend vs the density criteria — is resolved by the
α + brk composition: pool_alpha soaks up the rspan overshoot that brk had
to fix alone, freeing brk to sit where g1exp needs it without killing the
trend. Seed checks (`R72` D0–D3, D13): g1exp and rspan hold at 3/3 seeds;
trend holds at 2/3 (s271 +0.352); g8 is seed-stable to ±0.001; harness g3
and g6 are seed-noisy (the package family is far quieter, `R69`).

## The composition: g4 enters its band

| arm | g4 [351.3, 362.7] | g8 [0.731, 0.743] | trend |
|---|---|---|---|
| D9 α0 lp9.5 | 380 | 0.748 | +0.286 |
| D6 α0.12 lp9.5 | 372 | 0.754 | +0.335 |
| **D5 α0.18 lp9.5** | **361 IN** | 0.762 | +0.316 |
| D4 α0.24 lp9.5 | 345 | 0.777 | +0.405 |
| D7 α0.18 lp9.0 | 297 | 0.797 | +0.480 |

**g4 is fixable** — the two concentration levers compose smoothly through
its band. The cost is g8: both levers raise it, and at lp 9.5 even α = 0
sits 0.005 high. In the (α, lp) plane the g4 and g8 bands do not overlap;
whether a third lever (dg, w_loc) separates them is the remaining
question, and D14 (dg36: g3 163.6 IN harness-scale, g4 369, g8 0.757)
suggests dg helps g3/g4 but not g8.

## Hand-off

Four candidates to package verification (`R73`): C5 and C1 (pocket-first,
g4 conceded), D5 (g4-first, trend/g8 conceded), D12 (centre). The
scorecard that counts is the package one.

## Budget

30 arms these two rounds; RC-3 total 50.
