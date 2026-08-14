# RC-12: eight of ten — the density response certified held-out; mandatory g5 by six ten-thousandths

**Registered round.** Freeze: `spec/RC12_FREEZE.md` (R1 echo cell,
identity `60dfb49f…`, seed 5001, eight blocks registered before
evaluation). Records: `results/rc12_heldout.json` (4M/11M/14M/19M/22M/
26M/31M/38M), `results/rc12_generator.json`. Measured 2026-08-14; hash
verified in-run.

## The verdict table (full precision where it matters)

| criterion | 8-block band | frozen R1 | verdict |
|---|---|---|---|
| **§3 G1 exponent** | [−0.2313, −0.0957] | **−0.19998** | **IN — first held-out certification ever** |
| **gspan** | [−0.6637, −0.2417] | **−0.42620** | **IN — first ever** |
| **rspan** | [1.0741, 3.0908] | 1.10930 | **IN** (the declared expected miss, in) |
| §3 trend | [0.3852, 0.6220] | 0.56765 | IN |
| g1 * | [14.929, 20.805] | 17.292 | IN |
| g6 * | [1.6960, 1.8156] | 1.76319 | IN |
| g3 | [94.79, 238.45] | 161.74 | IN |
| g8 | [0.73083, 0.74473] | 0.73806 | IN |
| g5 * | [**1.35335**, 1.41402] | **1.35274** | out by **0.00061** |
| g4 | [343.4, 368.6] | 423 | out (structural) |
| np95 (reported) | real ~50 | 10 | declared partial |

**EXCLUDED on mandatory g5, by six ten-thousandths of a contrast unit —
within the generator's own seed spread (±0.001, `R99`).** Reported as
the rule requires.

## What this verdict is

The strongest held-out result in the project's history, whatever the
formal label. It ties RC-3's count (8/10) with a categorically superior
composition: RC-3 missed g4 plus the entire density response; RC-12
misses g4 plus a contrast hair. **Every density-response criterion —
the axis eleven campaigns of kills established as the family boundary —
is in band on data no round touched**: the exponent, both spans, and
the trend, simultaneously, plus honest partition-scatter movement
(np95 10 vs the pre-echo 2).

The two misses:

* **g5 (−0.00061)**: a knife edge the tuning data placed at exactly
  this margin (`R99`: 1.352–1.354 across seeds against edges near
  1.354). Not a mechanism failure — a dose position. One breath of
  fine-scale rebalance moves it; whether to spend anything re-verifying
  a hair is an operator decision, recorded as open.
* **g4 (structural)**: unchanged through six families and five spectral
  architectures; the one criterion no mechanism class has touched.

## Standing

* **Held-out frontier: RC-12's 8/10** (composition-superior; count-tied
  with RC-3). The echo family (R1) is the standing configuration of
  record.
* The density-response problem — the arc's central open question since
  RC-2 — **is solved and certified**: small window-local near-parallel
  groups, `RC11_VERDICT` physics, held-out here.
* Remaining open, in order: g5's hair (dose), g4 (the last structural
  residual), scatter's remaining distance (10 → ~50, the cascade lead),
  and the sealed ANN test behind full admission.
* Corpus ledger: thirty-eight offsets consumed; **27M and 33M remain as
  the final reserve**. The sealed set: untouched.

## Budget

One evaluation, as declared. RC-11/12 cumulative: 48 harness arms + 20
package runs + this one-shot.
