# RC-3 Phase A: the family is seed-deterministic, and the rank-level hypothesis dies at its premise

**Exploratory, not a registered round.** Measured 2026-08-13 on Atlas GPU 1
(package generator, 8-worker generation, ~77 °C). Four generation seeds
(41/89/137/271) of the frozen configuration against the R68 ten-block
bands; record `results/r69_phasea.json`. Executes `RC3_PLAN.md` Phase A.

## Seed robustness: the panel is essentially deterministic

| statistic | R68 band | 4 seeds | verdict |
|---|---|---|---|
| g1 * | [14.44, 21.03] | 16.27–16.44 | IN, robust |
| g5 * | [1.362, 1.407] | 1.375–1.376 | IN, robust |
| g6 * | [1.702, 1.789] | 1.764–1.774 | IN, robust |
| g3 | [153.6, 196.5] | 154.5–156.1 | IN (low edge), robust |
| §3 trend | [0.390, 0.648] | **0.414–0.438 — 4/4 IN** | IN, robust |
| gspan | [−0.630, −0.261] | −0.244…−0.262 | straddles the edge |
| g4 | [351.3, 362.7] | **448–449** | **out, robust (+24%)** |
| rspan | [1.086, 2.938] | **4.58–4.78** | **out, robust** |
| §3 G1 exp | [−0.236, −0.112] | **−0.085…−0.097** | **out, robust** |
| g8 | [0.731, 0.743] | 0.722–0.724 | out, robust (−0.008) |

Two corrections to the RC-2 reading: the frozen seed 1009's trend (0.377,
out by 0.013) was seed-misfortune — the family's trend is in band — and
the generation-seed spread of every statistic is tiny (rspan ±0.10 against
the harness family's ±0.64), so the corrected article law also removed
most of the family's seed variance. The robust residue is exactly four
numbers: **g4, rspan, g1exp, g8**.

## The rank anatomy: no deficit exists

Local/global eff_rank under ONE implementation (25k base, 256 queries,
k = 100 neighbourhoods) on both sides:

| corpus | local | global |
|---|---|---|
| generator, 4 seeds | 38.1–38.4 | 151.0–152.6 |
| real, block 3M | 38.0 | 125.4 |
| real, block 18M | 39.5 | 180.8 |

**Real's local eff_rank is ~38–40 and the generator already matches it**;
global sits inside real's own 125–181 block spread. The `R64` figure of
"local 75 vs real 168" does not survive re-measurement under a shared
implementation — it was a cross-implementation comparison, exactly the
class of error the campaign's discipline exists to catch. `RC3_PLAN.md`
§2's hypothesis is **refuted at its premise**: there is no rank-level
deficit for Phase B to fix, and no residual miss is attributable to one.

## Phase B, re-aimed

The plan's Phase B (rank sweep) is void. The robust residue re-aims it:

1. **g4 — spectrum tail shape.** eff_rank (g3) is in band while dims90 is
   24% high and real's dims90 is its most stable statistic (357 ± 3 across
   ten blocks). The generator's PCA tail decays too slowly. Untried lever:
   an amplitude profile on the shared direction pool (power-law decay
   across pool slots) — shapes the tail without touching the mechanisms.
2. **rspan / g1exp — density response magnitude.** The sparse end
   overshoots (§3b ratio at 50k: 6.0 vs [3.2, 4.0]) while G1-vs-n falls
   too slowly. Levers with known signs at the old family, unmeasured at
   the corrected one: seg_break, path_mix, w_loc, d_glob.

Phase B sweep: pool-spectrum exponent × the density levers, harness
generator on NRP (signs transfer; winners verified with the package on
Atlas), judged only against R68 bands.
