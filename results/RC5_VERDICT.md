# RC-5: the centre-subspace architecture is refuted — the spectral triple is off the family's surface

**Registered close, no freeze, no one-shot spent.** Two harness sweeps (32
arms, `R78`/`R79`, drivers `harness/rc1/rc5a.py`, `rc5b.py`, raw
`results/r78.txt`, `r79.txt`) against `RC5_PLAN.md`'s pre-registered kill.

## What the architecture did and did not do

Segment centres moved to a dedicated `d_cen`-dim orthonormal subspace,
fine components staying on the full-spread pool.

* **The retention prediction was confirmed exactly** (`R78`): g8 falls
  monotonically with d_cen (0.742 → 0.698 across 0–384) — fine variance
  escapes the top-256 projection as designed. The decoupling *mechanism*
  works.
* **The dims90 prediction failed with a diagnosis** (`R78`): a flat frame
  *adds* a uniform spectral block, raising g4 (413 → 499). The old
  pool-drawn centres were already α-shaped; flatness was the regression.
* **The repair re-couples the trade** (`R79`): giving the centre subspace
  a decaying spectrum (`cen_beta`) moves g4 down only by dragging g8 up
  and g3 down along the same one-parameter curve as every pool form —
  β 0.8: g4 385, g8 0.765, g3 79. Across all 32 arms, no cell approaches
  the registered joint (g4 ≤ 363, g8 ≤ 0.743, g3 ≥ 151); whenever
  g4 < 400, g8 > 0.74 and/or g3 < 110. **The kill fires.**

## The accumulated statement, now five architectures strong

dims90, PCA retention, and effective rank move on a **one-parameter trade
surface** in this family — under the α power law, the two-scale floor,
pool-size composition, the partitioned pool (RC-4), and the centre
subspace flat or spectrally profiled (RC-5). Real's triple
(357 / 0.737 / ~175) is off that surface. Whatever real does — plausibly
per-direction variance that is *coherent across segments* in some
dimensions and *incoherent* in others, rather than any per-component
subspace split — this family's compositional structure cannot express it.
That is a property of the family worth publishing, not a search failure:
five falsifiable mechanisms were named in advance and each was killed by
its own registered criterion.

Incidental positives recorded for completeness (none survive the g3/g4
misses): dc256/β0.5/wl0.7 pushed the trend to +0.730; the s137 seed check
put g1exp in band at −0.128 — the harness's g1exp noise straddles its
band edge, consistent with `R74`.

## Standing

The frontier remains **RC-3's frozen D12** (8/10 held-out, mandatory trio
IN, identity `e8423665…`). No RC-5 configuration beats it robustly; the
fresh blocks stay clean. A successor family, if attempted, should start
from the trade-surface statement above rather than from more levers on
this one.

## Budget

32 arms (Phase A 16, B 16; the envelope's third sweep intentionally
unused — the kill had fired). No real blocks consumed.
