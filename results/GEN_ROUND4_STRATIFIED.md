# Generator search — round 4: the stratified spectrum matches G1 *and* G7; hubness is the last wall

**Run:** 2026-07-21, NRP Nautilus, 12-shard swarm (corrected harness, same-instance
held-out queries). n=8000, battery B, k=10, train/val only, seal untouched.
Family: `stratified_corpus` (each cone a Whitney flag of nested subspaces).
Pre-registration: [`STRATIFIED_PREDICTION.md`](STRATIFIED_PREDICTION.md).

## Result against the registered predictions

Real (n=8k): `G1 id=57.7, G3 eff-rank=187.9, G6 hubness=6.83, G7 local-ID IQR=20.8,
G8 pca-ret=0.62`. Best point (shard 3), measured with the full battery incl. G7:

| gate | value | ratio | |
|---|---:|---:|---|
| G1 intrinsic dim (spectrum **centre**) | 49.6 | **0.86×** | ✓ |
| **G7 local-ID IQR (spectrum spread)** | 20.9 | **1.00×** | ✓ **first family to match it** |
| G3 effective rank | 145.8 | 0.78× | ✓ |
| G8 PCA retention | 0.82 | 1.32× | ✓ |
| **G6 hubness** | 1.25 | **0.18×** | ✗ the wall |

**P1 — CONFIRMED.** Setting the strata dimension spectrum matches the local-ID
**distribution**: centre (G1 = 0.86×) *and* spread (G7 = **1.00×**) together. No
single-dimension family can do this — the concentration family (round 3) has G7 ≈ 0
by construction (one local dim per cluster → no spread). The Whitney-flag
construction delivers exactly what it was designed for.

**P3 — bet paid off.** G1 did **not** overshoot despite an ~91-dim top stratum: the
densely-populated deep strata pulled the ID distribution to target (0.86×), so the
undersampled tail did not dominate the two-NN readout. The honest risk did not fire.

**P2 — NOT supported.** `frontier_conc` does not supply hubness: G6 stuck at 0.18×
across *every* shard (0.14–0.23×), essentially where the concentration family sat.
Piling points onto the frontier is not a strong enough density gradient.

**P4 — measured, not yet tested.** `whitney_b_defect = 0.588` at the best point (the
construction is not (b)-regular). The registered claim — that the gates are
*insensitive* to this defect at matched spectrum — needs a paired experiment
(matched G1/G3/G7, varied defect) and is not settled here.

## The scoreboard: one mandatory gate left

Across rounds 3–4 the concentration/stratified structure now matches **G1, G3, G7,
G8** (and G5 sits near band). **G6 hubness is the sole hard wall** — every
cluster-structured family caps at ~0.2×, while real is 6.8.

The diagnosis is now sharp. Round 1's smooth manifold *did* reach hubness (0.85×)
by mapping **every point** through the Poincaré `exp_0` map — a *per-point* radial
density gradient that packs points near the boundary (hubs) with few central. The
concentration and stratified families apply curvature only to the **cluster/cone
centres** (a few dozen points), which is too coarse to make the fine per-point
gradient hubness needs.

## Round 5 direction (structural, not a re-tune)

Combine what each family proved: keep the flat-local-subspace / nested-flag
structure that matches G1/G3/G7/G8, and add round 1's **per-point** hyperbolic
packing for G6 — a global radial density warp applied to all points (or a strongly
hyperbolic layout of *many* centres), chosen so it packs the boundary without
destroying the local flat-patch reach. Hubness is a global-density property; it
needs a global-density mechanism, not a cluster-level one.

Nothing here passes RC-1; the seal is untouched. Numbers:
`results/gen_round4_stratified.json`.
