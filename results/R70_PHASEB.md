# RC-3 Phase B: the pool-spectrum exponent is the g4/g8/rspan lever, and brk is g1exp's

**Exploratory, not a registered round.** Measured 2026-08-13 on NRP A10s
(16 arms, one indexed job, ~20 s each). Driver `harness/rc1/phaseb.py`;
raw `results/r70.txt`. Executes the re-aimed Phase B of `RC3_PLAN.md`
(rank sweep voided by `R69`). Harness generator; judged against the R68
ten-block bands. Harness-vs-package fidelity gaps at the base point: g3
runs ~30 low (124.7 vs 154.5) and rspan ~1.0 low (3.63 vs 4.59) — signs
and slopes transfer, winners must be verified with the package generator.

## pool_alpha — a new mechanism, and it moves exactly the residue

Power-law amplitude profile over the shared direction pool,
`(1+j)^-alpha`, unit mean square. Nothing else changed:

| arm | g4 | g8 | rspan | trend | g5 | g6 |
|---|---|---|---|---|---|---|
| α = 0 (base) | 445 | 0.720 | +3.63 | +0.41 | 1.386 | 1.789 |
| α = 0.10 | 439 | 0.725 | +3.38 | +0.41 | 1.388 | 1.788 |
| **α = 0.20** | **419** | **0.738 IN** | **+2.79 IN** | **+0.50 IN** | 1.396 IN | 1.781 IN |
| α = 0.35 | 351 | 0.785 | +1.68 | +0.62 | 1.435 out | 1.954 out |
| α = 0.50 | 228 | 0.852 | +1.05 | +0.36 | 1.563 out | 3.126 out |

**B2 (α = 0.20) is 7-of-10 in band** — mandatory trio, g8, trend, rspan,
gspan — the best single arm the campaign has ever produced. The lever's
window is narrow upward: by α = 0.35 the concentrated pool head captures
the hub structure (g6 1.95, g5 1.44, g8 overshoots). g4 crosses its band
near α ≈ 0.3 but nothing else survives there; at α ≈ 0.2–0.26 g4 sits
~400–420 (still +12–16%).

## brk at the corrected operating point: g1exp finally has a lever

| brk | trend | g1exp | rspan |
|---|---|---|---|
| 0.100 | +1.00 | −0.083 | +4.95 |
| 0.116 | +0.41 | −0.107 | +3.63 |
| 0.135 | +0.20 | **−0.141 IN** | +0.71 |
| 0.160 | +0.09 | **−0.182 IN** | +0.21 |

g1exp enters its band ([−0.236, −0.112]) at brk ≳ 0.119; the trend leaves
its ([0.390, 0.648]) at brk ≳ ~0.120. The triangle — trend wants brk low,
g1exp wants it high, α threads g4/g8 — is the Phase C target, with the
mix cross-term as a second g1exp lever (mix 0.75 gives g1exp −0.198 but
g1 11.1; mix 0.45 gives g1 22.5 and g1exp −0.031; the joint pocket is
mix ≈ 0.62–0.68).

Also mapped: w_loc 0.50 tames rspan (1.13) but kills trend (+0.22);
dg 48 lifts g3 to 164 (IN, harness scale) at trend +0.32; the rank
anatomy is flat across every arm except the α ladder (38.8 → 25.3 local
as α concentrates the pool) — consistent with `R69`: rank is not the
family's problem.

## Budget

16 arms; RC-3 total 20 (Phase A 4).
