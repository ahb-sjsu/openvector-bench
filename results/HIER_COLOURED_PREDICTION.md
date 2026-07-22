# Pre-registration — the coloured-hierarchy family (round 6)

**Registered before the gating run** (the discipline of `PREREG_RC1.md`). Train/validation
only; the sealed 25% is never loaded; not RC-1 admission. Family:
[`openvector_bench/generator_search.py`](../openvector_bench/generator_search.py)
(`hier_coloured_corpus`, `HIER_COLOURED_PARAMS`). This is the round registered in round 5's
P3: hubs and spectrum set by **separate mechanisms** — Zipf hierarchical centre placement
(round 5's G6 mechanism, kept verbatim) inside an explicit Mahalanobis reshape of the
centred covariance toward a designed power law (the codebook probe's confirmed G3 knob).

**Disclosure:** a five-point screening smoke (round-5 hub-end knobs, colouring swept, single
seed) was run on Atlas before this registration. It already answers round 5's open question,
and positively: **the recolouring does not destroy the hubs — it amplifies them.** At
`spectrum_decay` 0.4/0.6 (mix 1.0), G3 = 2.03×/1.38× with G6 = 5.10×/4.48× *simultaneously*
— the round-5 Pareto axis (G6 × G3, nothing in the middle) is broken by construction. The
smoke also shows where the cost went: at decay 0.6, G1 = 2.01×, G7 = 2.95×, G8 = 0.35× —
the reshape's expansion of the compressed directions inflates the *local* readings. Nothing
below is a blind prediction about whether G6 and G3 can coexist; the registered question is
whether the **full joint point** exists.

## Registered predictions

**P1 — the five-gate joint point exists (make-or-break).** The colouring owns G3/G4, the
centre hierarchy owns G6, and the within-cluster knobs (`local_dim`, `within_scale`,
`size_tail`) own G1/G7/G8 — three claimed-independent mechanisms. *Prediction:* the 12-shard
search finds a single point with **all five mandatory gates — G1, G3, G6, G7, G8 — within
[0.5, 2.0]× of real simultaneously**, the first in the campaign. *Falsified if* every
shard's best point has at least one mandatory gate outside [0.5, 2.0]×.

**P2 — the G6 × G3 axis is dead as a trade-off.** Refining the smoke into a registered
claim: within the decay window that holds G3 ≥ 0.5×, G6 is *controllable at or above* 1×
(the hierarchy knobs retain their round-5 range under the colouring). *Falsified if* the
search's G3-in-band points cap below G6 = 0.5× — i.e. the smoke's joint readings were a
seed artefact.

**P3 — the honest risk: the tension has moved to the local axis, and may be intrinsic.**
The reshape acts on *global* covariance directions, but every local neighbourhood lives in
the same ambient space: flattening the dominant modes expands exactly the directions the
local flat patches were compressed into, inflating two-NN dimension (G1 up), spreading the
per-point local-ID distribution (G7 up), and decohering the PCA subspace from the true
neighbourhoods (G8 down — 0.35× in the smoke, and G8's registered floor has been the
campaign's most fragile band). If `local_dim`/`within_scale` cannot counter-tune this —
because the colouring's local distortion is anisotropic where the patches are isotropic —
the family fails on the local axis, P1 misses, and the round-7 direction is a
*local-covariance-aware* colouring (reshape only the subspace orthogonal to the patch
union, or per-cluster whitening before placement).

## Protocol

NRP Nautilus swarm, 12-shard Indexed Job (`FAMILY=hier_coloured`, `N_EVALS=40`/shard,
shard 0 anchored at family defaults), n = 8000 + 1000 same-instance held-out queries,
battery B, k = 10, target = `target_n8000.json`. Best point re-measured with the full
8-gate battery. Result and falsifier readout go to `results/GEN_ROUND6_COLOURED.md`.
