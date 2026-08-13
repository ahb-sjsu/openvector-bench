# Phase A: g1 lands at 17.52 — the ninth held-fixed parameter was the cause

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-13 on NRP A10s (16 arms, two indexed jobs, ~2 min each).
Driver `harness/rc1/phasea.py`; record `results/r62.json`. Executes
`RC1_PLAN.md` Phase A. Predictions were stated in the plan and the driver
header **before** the run; they are adjudicated against here, including the
misses.

## The diagnosis under test

`R60`/`R61` measured g1 at 4.31–4.87, invariant to `d_glob`, `fil_dim`, `brk`
(including zero) and `w_loc`. The RC1_PLAN §3.1 diagnosis: in a pure dyadic
path, adjacent rows differ at level 0 and gap-2 rows at levels 0+1, so the
two-NN ratio is pinned at `mu ~ sqrt(1 + decay)`. The path level-variance decay
had been **0.72 since R49 — never swept**. Predicted TwoNN ≈ 3.7 at decay 0.72
(measured 4.3–4.9 ✓) and ≈ 17 at decay 0.125.

Kill-criterion, pre-registered: decay 0.125 leaving g1 < 8 falsifies it.

## Sweep 1 — mechanism confirmed; quantitative model degrades at low decay

Pure path column (config P_B: brk 0.030, w_loc 0.6, branch 64, d_glob 30):

| decay | predicted g1 | measured g1 | g6 | autocorr gap-1 | ratio span |
|---|---|---|---|---|---|
| 0.72 | 3.7 | 4.44 | 1.681 | 0.723 | **+2.420** |
| 0.50 | 4.9 | 6.12 | 2.495 | 0.660 | +0.189 |
| 0.30 | 7.6 | 11.38 | 3.230 | 0.605 | −0.335 |
| 0.125 | 17.0 | **51.34** | 3.601 | 0.564 | −0.393 |

**The kill-criterion is nowhere near triggered** — decay moves g1 from 4.4 to
51.3, monotone. The mechanism is confirmed: `decay` is the g1 lever that four
swept levers were not. The quantitative shell model is good at moderate decay
and **degrades badly at low decay** (predicted 17, measured 51): once the
inter-shell separation is comparable to the within-shell noise width, `mu → 1`
faster than the arithmetic says and the MLE runs away.

Two costs of the pure-path route, both disqualifying: g6 blows up (3.2–3.6
against 1.696), and the ratio span collapses.

## Sweep 1 — the R42 transfer prediction half-failed

(decay 0.72, mix 0.4) was predicted to give g1 ≈ 17 with NN-gap ≈ 3 on R42's
direct evidence. Measured: **g1 25.64, NN-gap 1**. The segment context
amplifies the ball relative to R42's pre-segment family, and the gap only
unsticks with *both* levers flat: (0.50, 0.4) → gap 2, (0.30, 0.4) → gap 5,
(0.125, 0.4) → gap 8, bracketing real's 3 — but all with g1 ≥ 33.

The mixture's clean wins: **g6 stays healthy under it at every decay**
(1.79–1.96 where pure path gave up to 3.6), and the autocorrelation stays
near real's.

## Sweep 2 — the contour lands

Refinement over decay ∈ {0.40–0.72} × mix ∈ {0.45–0.6}:

| decay | mix | **g1** | NN-gap | g5 | g6 | autocorr (1,2,4,8,16) |
|---|---|---|---|---|---|---|
| **real** | | **17.23** | **3** | **1.369** | **1.696** | 0.598, 0.530, 0.449, 0.367, 0.304 |
| **0.50** | **0.6** | **17.52** | 1 | 1.535 | 1.930 | 0.611, 0.540, 0.475, 0.401, 0.310 |
| 0.72 | 0.5 | 19.12 | 1 | 1.567 | 1.759 | 0.630, 0.562, 0.491, 0.408, 0.312 |
| 0.60 | 0.6 | 14.92 | 1 | 1.548 | 1.825 | 0.628, 0.554, 0.484, 0.404, 0.311 |
| 0.60 | 0.5 | 21.29 | 1 | 1.549 | 1.828 | — |

**g1 = 17.52 against 17.23 — within 2%** — at (decay 0.50, mix 0.6), with g6
at 1.930 and the autocorrelation close to real's, simultaneously. After three
rounds of invariance across four levers, the gate is reached by the parameter
none of them touched.

## Two open items, recorded rather than chased

**1. The NN-gap tension.** Real has g1 17.23 *and* k=1 NN median index gap 3.
In this parameterization the two trade: every arm with gap ≥ 2 has g1 ≥ 25;
every g1 ≈ 17 arm has gap 1. The g1 ≈ 17 arms match real's two-NN *ratio*
distribution while still having the adjacent row as the nearest neighbour —
the right distances via a different anatomy. Gap is not a registered
criterion; it is a fidelity indicator, and this family currently cannot have
both. Noted as the honest residual of Phase A.

**2. The spans reshuffle completely at healthy g1.** The broken-g1 baseline
had ratio span +2.420 (in band); every g1-healthy arm sits at +0.19 to +0.84,
and the log G1 span ranges −0.83 to +0.63 across the grid, crossing zero.
`R61`'s "spans never jointly reachable" is confirmed **stale** — it described
the broken-g1 family — but the fresh landscape is not obviously friendlier:
the in-band ratio span of R61 was, in part, an artifact of the quantized-shell
mechanism. Phase B now re-adjudicates §3b on genuinely new terrain, which is
exactly what the plan sequenced it for.

## Phase A verdict

**Complete.** g1 is fixed (17.52 vs 17.23), the mechanism is understood and
confirmed against a pre-registered kill-criterion, g6 survives the fix, and
the autocorrelation holds. Carried forward: (decay 0.50, mix 0.6) as the
Phase B operating point; the NN-gap tension and the reshuffled spans as the
open items Phase B and the Phase D audit must confront.

## Budget

16 arms this round (8 + 8), all pre-registered as Phase A in `RC1_PLAN.md`.
