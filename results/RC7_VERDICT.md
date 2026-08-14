# RC-7: the one-shot verdict — five of ten, excluded, and the band lottery measured

**Registered round.** Freeze: `spec/RC7_FREEZE.md` (identity `fa6342a0…`,
seed 3001, geometric-only bar re-registered before evaluation, expected
outcome and risks stated). Records: `results/rc7_heldout.json` (blocks
6M/17M/29M/40M — untouched), `results/rc7_generator.json`. Measured
2026-08-14 on Atlas GPU 1; hash verified in-run.

## The verdict table

| criterion | fresh-block band | frozen F8 | verdict |
|---|---|---|---|
| g1 * | [14.53, 18.74] | 15.74 | **IN** |
| g5 * | [1.372, 1.404] | 1.365 | out (−0.007) |
| g6 * | [1.682, 1.798] | 1.759 | **IN** |
| g3 | [80.3, 224.9] | 163.4 | **IN — first held-out g3 ever** |
| g4 | [343.6, 363.9] | 426 | out (structural) |
| g8 | [0.728, 0.744] | 0.739 | **IN** |
| §3 trend | [0.445, 0.602] | 0.533 | **IN** |
| §3 G1 exponent | [−0.210, −0.161] | −0.131 | out |
| rspan | [1.751, 2.410] | 1.388 | out |
| gspan | [−0.553, −0.477] | −0.205 | out |
| np95 (reported) | real 47–50 | 2 | known deficit, declared |

**EXCLUDED: 5/10, mandatory g5 by 0.007.**

## The diagnosis, in two parts

**1. The band lottery fired — and is now measured.** The stated risk was
a narrow fresh gspan draw; what arrived was the narrowest draw in the
project's history on FOUR statistics at once. These four blocks are
homogeneous strongly-articulated regions: gspan −0.49…−0.54 (sd 0.019,
vs 0.092 across the 10-block set), g1exp −0.17…−0.20, no weak-response
block in the draw. The generator's own numbers moved less than seed
noise from `R88` (g1 15.74 vs 15.70–15.87; gspan −0.205 vs −0.191…
−0.212): **the verdict variance is in the four-block sample of the real
corpus, not in the generator.** RC-3's 8/10 rode a wide draw; RC-7's
5/10 a narrow one. With real's block heterogeneity (`R68`: density
response varies 2.4×) comparable to configuration differences,
four-block one-shot verdicts are lottery tickets. **Methodological
consequence, binding on any future round: register the held-out draw at
≥ 8 blocks before freezing.**

**2. One miss is the configuration's own.** rspan 1.39 against fresh
1.75–2.41: the dup ladder depresses the ratio span — visible in every
R85/R88 run (1.15–1.42) but inside the wide tuning band, so it never
gated. It is a real cost of p_dup 0.05, now registered.

## Standing after the verdict

* **The held-out frontier remains RC-3's verdict** (8/10, mandatory trio
  IN, identity `e8423665…`).
* F8 remains the in-sample robust frontier (8/10 at 4 seeds, `R88`) and
  the package default; its held-out one-shot is this exclusion.
* What RC-7's verdict adds beyond the exclusion: held-out confirmations
  that survived even the narrow draw — g3 in band held-out for the first
  time (the sheet), trend mid-band, g8, g1, g6.
* Open, in order: the band-lottery rule (≥8 blocks) before any next
  one-shot; the dup ladder's rspan cost joins the pinch algebra;
  scatter and g4 unchanged.

## Budget

One evaluation, as declared. Consumed offsets now twenty-two; the
remaining ~18 clean 600k slots are enough for two 8-block draws.
