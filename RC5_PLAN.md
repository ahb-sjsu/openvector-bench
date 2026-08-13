# RC-5: the centre-subspace architecture

**Status: plan, 2026-08-13.** Successor to `RC4_PLAN.md` after both RC-4
kills (`results/RC4_VERDICT.md`). RC-4's refutations were architectural
diagnoses: in this family every component draws directions from one shared
pool, so the corpus spectrum and the neighbour structure move together —
while real holds dims90 357 with PCA retention only 0.737, meaning real's
neighbour-relevant variance lives disproportionately outside its top PCA
dimensions. RC-5 changes the architecture instead of the pool profile.

## 1. The mechanism

**Segment centres move to a dedicated `d_cen`-dimensional orthonormal
subspace** (a QR frame drawn at seed time, like the arrangement frames),
leaving the within-segment path and the per-row ball on the full-spread
pool:

* centre variance — the large, shared, between-segment component —
  concentrates into ~`d_cen` dimensions: the global spectrum's bulk
  narrows, driving dims90 (g4) toward real's 357;
* fine variance — small, per-row, neighbour-determining — stays spread
  over the full 1024 dims: the top-256 projection (g8) loses it, driving
  retention *down* toward real's 0.737;
* within-segment neighbour rankings are governed by the fine components
  (the centre is shared within a segment), so g1/g5/trend should be
  approximately invariant — this is the decoupling claim.

`pool_alpha` becomes a fine-scale-only lever once centres leave the pool;
its frozen 0.22 may want to relax toward 0.

## 2. Registered expectations and kill

Directional predictions, stated before the first arm: g4 falls with
`d_cen` (strongly, once d_cen + arrangement dims < ~400); g8 falls; g3
falls with d_cen (eff rank bounded by centre subspace + fine tail) — the
risk is g3 leaving its band [151, 200] from below; g1/g5 near-invariant.

**Kill:** if no (d_cen, w_loc, alpha) cell holds g4 ≤ 363 and g8 ≤ 0.743
and g3 ≥ 151 simultaneously (the exact joint every pool-shaping form
failed), the centre-subspace architecture is refuted as the decoupler and
the g4+g8+g3 joint is recorded as beyond this family in all tried
architectures.

## 3. Phases

* **A** — harness sweep: d_cen ladder (96–384) × {alpha 0/0.22/0.35} ×
  {w_loc 0.6/0.7}, plus seed and density-recenter probes. 16 arms.
* **B** — refinement/composition at the joint (if A opens it), including
  interaction with brk (density criteria) and rho (g6). 16 arms.
* **C** — package port (param `d_cen`, default 0 = frozen RC-3 identity
  untouched), verification, 4-seed pre-freeze.
* **D** — freeze + one-shot on fresh offsets, expected outcome declared
  first. Only if the robust scorecard beats RC-3's 8/10.

Envelope ≤3 harness sweeps. Tuning bands: `results/rc4_bands14.json`.
Budget so far: 0 arms.
