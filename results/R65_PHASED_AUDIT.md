# Phase D audit: the neighbourhood criteria hold, the density-response criteria fail beyond seed noise

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-13 on NRP A10s (12 pods: 2 operating points × 3 generation
seeds × 2 measurement halves). Driver `harness/rc1/phased.py`; record
`results/r65.json`. Executes `RC1_PLAN.md` Phase D — the gate to RC-2.

This is the family's first exposure to the §3 four-rung ladder, the full §3b
five-pool ladder (absolute per-density values), and g8. Protocol seeds fixed;
generation seed varies, so spreads below are generation variance.

## Gates: stable across seeds, three of eight in or near band

| gate | real | OP1 (3 seeds) | OP2 (3 seeds) |
|---|---|---|---|
| g1 * | 17.23 | 15.60–16.07 | 16.14–16.47 |
| g5 * | 1.369 | 1.378–1.384 | 1.399–1.409 |
| g6 * | 1.696 | 1.824–1.848 | 1.793–1.807 |
| g3 | 182.3 | 96–115 | 97–102 |
| g4 | 359 | 717–723 | **438–441** |
| **g8** | **0.730** | 0.611–0.614 | **0.715–0.717** |

**g8, measured for the first time ever, is essentially matched at OP2** —
0.716 vs 0.730 (2%), with tiny seed variance. The smaller direction pool
improves PCA retention. OP1's is 16% low. The mandatory trio sits at 0.90–0.96x
(g1), 1.01–1.03x (g5), and 1.06–1.09x (g6) — close and, importantly, **stable**:
gate spreads across seeds are under 3%.

## §3 four-rung ladder: fails decisively, first time measured

| statistic | band | all six arms |
|---|---|---|
| trend | [+0.254, +0.649] | **+0.81 to +1.11 — all out, 1.5–2.2x high** |
| G1 exponent | [−0.227, −0.112] | −0.125 to −0.167 — **all IN** |
| rung ratio 25k | [1.175, 1.571] | all IN |
| rung ratios 50k/100k/200k | — | **all out (high)** |

The generator's k-matched ratio grows far too fast with rung size: right at
25k, then escaping the bands above. The G1 exponent — the *slope* of dimension
with n — is in band in every arm; the ratio *trend* is not. This criterion had
never been run on this family, and it fails structurally, not marginally.

## §3b five-pool ladder: the absolute levels fail; the spans do not survive seeds

**Per-density values (the part of §3b beyond the two spans): nearly all out.**
The ratio is in band only at the endpoints (50k and sometimes 600k), out at
every middle pool in every arm. The G1 values fail in 29 of 30 cells — the
generator's rung-G1 runs ~14–23 across pools where real runs 16.27 → 26.66;
the *span* can be right while both endpoints sit ~15–20% low.

**And the R63 spans-in-band result does not survive generation-seed variance:**

| OP1 seed | rspan (band [+2.227, +2.567]) | gspan (band [−0.602, −0.386]) |
|---|---|---|
| 41 | +2.355 **IN** | −0.434 **IN** |
| 137 | +2.013 out | −0.383 out |
| 271 | +2.200 out | −0.405 IN |

Seed spread on the ratio span (±0.17) is comparable to the full band width
(0.34). **R63's joint-in-band hit was partly seed fortune** — reachable, not
robust. OP2: rspan in at 2 of 3 seeds, gspan out at all three. This is
precisely the adjudication the audit was designed to force, and it is the same
verdict the arc's history demanded: a single-seed point estimate near a band
edge is not a result.

## Coherence of the failures

The misses cohere into one statement: **everything measuring the density
response at multiple operating points fails in the same direction.** The §3
trend is too steep, the §3b middle-pool ratios too high, and the §3b G1 levels
too low and too compressed — while every *fixed-density, fine-scale* criterion
(g1, g5, g6, g8, r25k, G1 exponent) holds. The family reproduces real's
neighbourhood geometry and does not reproduce how that geometry moves across
sampling densities, beyond the two-point span it was tuned toward.

This is plausibly the same deficit as the rank *level* problem (local eff_rank
~75 vs 168, `R64`): the generator has too little independent structure for its
dimension estimates to climb as sampling thins.

Incidentally the single-block s(k) rms reached 3.57–4.05 — the best ever —
which underlines the lesson rather than softening the verdict: the convenience
statistic kept improving while the registered criteria failed.

## Phase D verdict

**Not freezable on the evidence.** Per `RC1_PLAN` Phase F, the fork is now
explicit: (a) the documented-exclusion close — freeze the best configuration
and execute RC-2 as a *verdict*, expecting exclusion on §3/§3b, making the
negative registered and held-out rather than in-sample; or (b) one more
mechanism cycle (the queued hyperbolic arrangement, which bears on exactly the
density-response/mid-curve deficit) before the seal. The choice spends or
defers the one-shot and belongs to the operator, not the audit.

Also still open before any freeze: the Atlas-side re-banding was deferred (box
at load 18); it affects only the unregistered s(k) curve targets, not the
registered criteria above.

## Budget

12 arms; 76 across Phases A–D.
