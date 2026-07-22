# Pre-registration — the hierarchical-concentration family (round 5)

**Registered before the gating run** (the discipline of `PREREG_RC1.md`). Train/validation
only; the sealed 25% is never loaded; not RC-1 admission. Family:
[`openvector_bench/generator_search.py`](../openvector_bench/generator_search.py)
(`hier_concentration_corpus`, `HIER_PARAMS`).

**Disclosure:** a three-point screening smoke (defaults + two knob pokes, n=8000, battery B,
k=10, single seed) was run on Atlas *before* this registration to confirm the family executes
and to time it. Its readings inform the predictions and are quoted here so nothing is
presented as a blind hit that wasn't: at defaults **G6 = 1.00×, G1 = 1.02×, G7 = 1.17×,
G8 = 0.98× — and G3 = 0.03×**. The wall moved: hubness is no longer the failure mode, the
**global spectrum** is. What remains genuinely open — and is what this round registers — is
whether the *joint* point exists.

## Why this family

Round 4's diagnosis: the radial `exp_0`/curvature map is discarded by unit-normalisation, so
curving cluster *centres* never touches the angular geometry the gates read — hubness on the
sphere is **angular density variation**, and every cluster-structured family capped at
G6 ≈ 0.2×. The fix builds the angular gradient directly into **centre placement**: each
centre is a sum over `n_levels` scales of codebook vectors chosen by a heavy-tailed (Zipf
`branch_tail`) draw, so a few coarse angular regions are dense (hubs) and most are sparse,
while each leaf cluster remains a flat `local_dim` patch (G1/G8) with heavy-tailed sizes
(G7 assist). The codebook-probe screening independently confirmed the mechanism class: Zipf
cluster sizes alone gave G6 = 1.54×.

## Registered predictions

**P1 — the joint G6 × G3 point exists (make-or-break).** The smoke shows the two failure
modes are now *complementary*: hierarchy (deep levels, strong Zipf) gives G6 ≈ 1× but
collapses effective rank (G3 = 0.03×); at `n_levels = 1`, low tail, the family reduces to
round-3 concentration, which held G3 = 0.78× but sat on the G6 wall. *Prediction:* the knob
space between the extremes contains a point with **G6 ≥ 0.5× and G3 ≥ 0.5× simultaneously**
(each ≥ 2.5× better than the respective family-collapse value), and the 12-shard search finds
it. *Falsified if* the best point — and every shard's best — has G6 < 0.35× **or** G3 < 0.35×:
that would mean hierarchy-for-hubness and rank are a genuine trade-off this construction
cannot escape, i.e. the hub directions and the spectrum directions cannot be decoupled by
codebook geometry alone.

**P2 — the local-patch gates survive the trade.** G1, G7, G8 are set by the *within-cluster*
structure (`local_dim`, `within_scale`, `size_tail`), which the G6/G3 tension does not touch.
*Prediction:* at the best point G1 ∈ [0.7, 1.3]×, G8 ∈ [0.7, 1.3]×, G7 ∈ [0.6, 1.4]×.
*Falsified if* recovering G3 (more codebook directions / weaker decay) drags the local
readings out of band — that would mean the "flat patch in a random subspace" story is wrong
and the gates were riding the hierarchy itself.

**P3 — the honest risk: G3 recovery destroys the hubs.** The obvious G3 fix (many effective
codebook directions: `n_levels` low, `level_decay` high, weak `branch_tail`) is *exactly* the
anti-hub direction — the same knobs serve both masters with opposite signs. If the Pareto
frontier between G6 and G3 is sharp (the falsifier of P1 fires), the registered conclusion is
that **hubness and rank need separate mechanisms** — e.g. hierarchical placement *within* a
high-rank designed (Mahalanobis) colouring, the codebook-probe's one confirmed spectrum knob —
and that goes to round 6, reported as a P1 miss here.

## Protocol

NRP Nautilus swarm, 12-shard Indexed Job (`FAMILY=hier`, `N_EVALS=40`/shard, shard 0 anchored
at family defaults), n = 8000 + 1000 same-instance held-out queries, battery B, k = 10,
target = `target_n8000.json` (real n=8k profile). Best point re-measured with the full
8-gate battery. Result and falsifier readout go to `results/GEN_ROUND5_HIER.md`.
