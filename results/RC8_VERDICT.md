# RC-8: seven of ten under the eight-block rule — the lottery split into dice and truth

**Registered round.** Freeze: `spec/RC8_FREEZE.md` (F8 unchanged, seed
4001, identity `115682bd…`, eight blocks registered before evaluation).
Records: `results/rc8_heldout.json` (2M/9M/12M/16M/20M/24M/30M/36M),
`results/rc8_generator.json`. Measured 2026-08-14; hash verified in-run.

## The verdict table

| criterion | 8-block band | frozen F8 | verdict |
|---|---|---|---|
| g1 * | [15.31, 18.78] | 15.79 | **IN** |
| g5 * | [1.355, 1.401] | 1.363 | **IN** |
| g6 * | [1.682, 1.811] | 1.754 | **IN** |
| g3 | [154.5, 203.4] | 163.8 | **IN** |
| g8 | [0.728, 0.744] | 0.738 | **IN** |
| §3 trend | [0.492, 0.598] | 0.564 | **IN** |
| rspan | [1.350, 2.868] | 1.481 | **IN** |
| g4 | [352.8, 363.7] | 426 | out (structural) |
| §3 G1 exponent | [−0.216, −0.151] | −0.134 | out |
| gspan | [−0.650, −0.335] | −0.202 | out |

**Seven of ten, mandatory trio IN** — the second-strongest held-out
result of the project, under the strictest verification rule it has had.

## What the eight blocks settled

**RC-7's g5, rspan, and trend misses were dice** — all return to band
under an honest draw, with the generator again inside seed noise of its
in-sample values. The band-lottery diagnosis holds for them, and the
≥8-block rule earned its keep on its first use: this verdict's bands are
consistent with the 14-block tuning bands where RC-7's four-block draw
was not.

**g1exp and gspan are not dice.** Across eight fresh blocks real's
G1-vs-n exponent runs −0.163…−0.205 and its §3b G1 span −0.35…−0.58 —
uniformly steeper and deeper than the family reaches. Two consequences,
both new:

1. **The §3b G1 span is a structural residual**, joining g4: no measured
   configuration (base D12 −0.27…−0.28, F8 −0.19…−0.21) reaches the
   eight-block band's shallow edge (−0.335). The tuning-band edge that
   made it look reachable came from the two weak-response blocks
   (21M/32M) — outliers, not the corpus's typical behaviour.
2. **The near-dup ladder fails its held-out adjudication at p 0.05**:
   its g1exp gain (−0.113 → −0.134) is insufficient against real's true
   steepness, and its gspan cost moves the family *away* from a band it
   already missed. The mechanism remains real and documented (`R82`,
   `R85`); its current dose is net-negative held-out.

## Standing

* **Held-out frontier: RC-3's verdict (8/10) stands** under its
  registered draw; under RC-8's stricter rule the family's ceiling is
  7/10 with three structural residuals (g4, g1exp, gspan) — all now
  measured against eight-block bands, none reachable by any mapped
  lever.
* The residual list is coherent: all three are statements that **real's
  geometry changes with sampling density more strongly than any
  configuration of this family** — the same direction as R80's scatter.
  Whatever architecture solves scatter plausibly moves these too; that
  is the successor's single problem, not four.
* Ten clean block slots remain — one more eight-block draw.

## Budget

One evaluation, as declared. Consumed offsets now thirty.
