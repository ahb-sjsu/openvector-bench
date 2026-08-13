# Phase B: both §3b spans in band, jointly, for the first time

**Exploratory, not a registered round.** No admission claim, seal untouched —
and see the caveats, which matter more than usual here. Measured 2026-08-13 on
NRP A10s (24 arms, three indexed jobs). Driver `harness/rc1/phaseb.py`; record
`results/r63.json`. Executes `RC1_PLAN.md` Phase B.

## What Phase B was

`R61` concluded the two §3b spans were never jointly reachable — in-band windows
disjoint in `w_loc`, no bridging lever. `RC1_PLAN` §3.2 flagged that verdict as
conditional on the broken g1 mechanism, since the log G1 span *contains* G1 at
both densities. Phase B re-adjudicates on the g1-healthy operating point from
Phase A (decay 0.50, mix 0.6). Its pre-registered kill: spans still disjoint
with healthy g1 → §3b structurally unreachable for the family.

**The kill-criterion is refuted.** Both spans are jointly in band.

## Sweep 1 — the landscape at healthy g1

3×3 grid over brk × w_loc (bands: ratio [+2.227, +2.567], log G1
[−0.602, −0.386]):

| brk | w_loc | ratio span | log G1 span | g1 | g5 | s(14) |
|---|---|---|---|---|---|---|
| 0.030 | 0.6 | +0.191 | −0.046 | 17.52 | 1.535 | 6.9 |
| 0.080 | 0.6 | **+2.531 IN** | −0.235 | 16.43 | 1.461 | 10.3 |
| 0.080 | 0.9 | +3.586 | +0.045 | 16.51 | 1.605 | 12.0 |
| 0.143 | 0.6 | +1.307 | **−0.510 IN** | 15.36 | **1.354** | **16.3** |
| 0.143 | 0.9 | +1.642 | **−0.391 IN** | 14.18 | 1.280 | 20.2 |

`R61`'s disjoint-by-lever structure is gone: the two bands are reachable in
adjacent grid cells. The (0.143, 0.6) arm was already the best cross-criterion
confluence ever measured — g1 0.89x, g5 0.99x, s(14) 1.01x, log G1 span in
band — missing only the ratio span.

## Sweep 2 — one lever per arm around that champion

`d_glob` 18/24 kept the log G1 span in band and nudged the ratio up; `fil_scale`
and `size_spread` moved things the wrong way; and the middle-of-bracket probe
**brk 0.110 overshot the ratio band (+3.502) with log G1 at −0.376, ten
thousandths outside its band**. Both spans therefore cross their bands between
brk 0.110 and 0.143, with interpolation pointing at brk ≈ 0.125.

## Sweep 3 — the crossing, confirmed twice

| arm | ratio span | log G1 span | g1 | g5 | g6 | s(14) |
|---|---|---|---|---|---|---|
| **bands / real** | **[+2.227, +2.567] / +2.397** | **[−0.602, −0.386] / −0.494** | **17.23** | **1.369** | **1.696** | **16.08** |
| **brk 0.125, wl 0.6, dg 24** | **+2.381 IN** | **−0.475 IN** | 15.45 | **1.374** | 2.020 | 14.6 |
| **brk 0.128, wl 0.65** | **+2.290 IN** | **−0.435 IN** | 15.23 | **1.354** | 1.959 | 15.4 |

**Both §3b spans in band, at two independently-parameterised configurations.**
At the champion the ratio span is 0.7% from real's central value and the log G1
span 4% from it, with `g5` at 1.374 against 1.369 — essentially exact — `g1` at
0.90x, and `s(14)` at 0.91x, simultaneously.

For calibration of what this means: §3b is the criterion that excludes i.i.d.
generators *structurally* (`R29`), the one validated by the permutation control
(shuffle the rows, both spans collapse to zero), and the one `R61` declared
unreachable. Every prior "span in band" result (`R46`, `R56`) was exposed as
endpoint cancellation or artifact on inspection. This one arrives with the
neighbourhood gates simultaneously close, which is precisely what those
failures lacked.

## Caveats, stated with the result rather than after it

1. **This is not §3b admission.** The registered criterion also requires the
   five per-density values each within ±2 sd; only the two summary spans were
   measured here. The five-pool ladder is Phase D.
2. **Single-seed arms.** The ratio span is visibly noisy in brk over
   0.115–0.135 (non-monotone: +2.979, +2.131, +1.967 at 0.115/0.122/0.125-dg30),
   so band verdicts near edges need seed/block error bars. The two BOTH-arms sit
   mid-band, which is why they are credible, but Phase D must re-measure with
   variance.
3. **g6 is now the worst mandatory gate**: 1.96–2.02 against 1.696 (~19% high)
   across the whole champion region. g1 sits ~10% low. Both are residuals for
   Phase C/D.
4. Budget: 24 arms this phase, 40 for Phases A+B together, all pre-registered
   in structure by `RC1_PLAN`.

## Phase B verdict

**Complete, and the kill-criterion is refuted** — `R61`'s structural negative
was an artifact of the broken g1 mechanism, exactly as `RC1_PLAN` §3.2
suspected. Champion carried to Phase C/D:
`(brk 0.125, w_loc 0.6, d_glob 24, decay 0.50, mix 0.6, branch 64, fil_dim 48,
nlev 6, d_loc 64, fil_scale 1.0, size_spread 1.2)`.

Remaining, in plan order: Phase C (alignment, for `s(53)`/g3/g4 — and now also
g6), then the Phase D audit where the §3b five-pool ladder, the §3 four-rung
ladder, g8, and error bars all land at this single configuration.
