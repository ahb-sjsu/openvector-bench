# Generator search — round 8: the registered target, achieved — six gates + real anatomy, seed-stable

**Run:** 2026-07-22, NRP Nautilus, 12-shard swarm (`FAMILY=hier_q`,
`ANATOMY_TARGET=1.1426`, shard-0 warm start as disclosed; cold shards re-drew the
round-7 candidate pools by construction — same per-shard RNG — so the round is also a
**matched re-ranking experiment** on the anatomy-priced score). Pre-registration:
[`ROUND8_PREDICTION.md`](ROUND8_PREDICTION.md). Train/val only; seal untouched.

## P1 — CONFIRMED: the campaign's goal, as registered

Best point (shard 0, score 0.245 — the **warm-started anchor itself**, round-7
shard 1's knobs with the Jacobian-informed `spectrum_decay` 0.39→0.54). Full battery +
anatomy on three fresh seeds:

| gate | seed 0 | seed 1 | seed 2 | |
|---|---:|---:|---:|---|
| G1 intrinsic dim | 1.05× | 1.00× | 1.05× | ✓ |
| **G2 ball-growth** | **1.06×** | **1.12×** | **1.17×** | ✓ |
| G3 effective rank | 1.83× | 1.90× | 1.92× | ✓ |
| G6 hubness (battery B) | 1.36× | 1.43× | 1.28× | ✓ |
| G7 local-ID IQR | 0.79× | 0.76× | 0.84× | ✓ |
| G8 PCA retention | 0.84× | 0.82× | 0.85× | ✓ |
| G5 relative contrast | 1.01× | 1.00× | 1.01× | (✓, unregistered) |
| **anatomy: b→b skew / max** | **1.76 / 102** | **1.38 / 52** | **1.91 / 104** | ✓ real: 1.50 / 78 |

**Six gates in [0.5, 2.0]× and anatomy in band, on every seed — real's numbers by
real's mechanism.** The only gate out of band anywhere is G4 (2.28×, never in the
registered six; it tracks the colouring's spectral tail and is round-9 polish, not a
wall). Honest attribution: the 480 random evals added nothing — **the winning point is
the warm-start anchor**, i.e. the round was won by round 7's diagnosis plus one
derivative, not by search. The Jacobian's ∂G3/∂θ_s = −9.9 predicted the G3 correction
directionally (2.50→1.0 linearly; 2.50→1.83 actually — half the linear step, as
expected on a curved response).

## P2 — CONFIRMED: pricing flips the optimizer's preferred mechanism

Matched re-ranking (same candidates, new score): the new top four — shards 0, 1, 10, 7
(sampled skew 1.68, 1.62, 0.79, 1.04) — are **exactly round 7's warm start + the three
anatomy-clean shards**; round 7's score-best super-hub point fell #1 → #6 (skew 5.14)
and the skew-22.9 monster stayed buried. Four of the top six are anatomy-clean
(registered: majority). The pathology did not find a cheaper neighbour.

## P3 — mild, one estimator note

Anatomy readings at the best point varied 1.38–1.91 across seeds without leaving the
band; the noisy-compass risk did not bite at 2000 queries. One honest observation for
the record: the sampled estimator is *softer on super-hubs* than the full graph
(round-7 shard 8: full-graph skew 22.9 → sampled 2.6, barely under the P2 line) — if a
future family lives near the boundary, score the full-graph skew or raise
`anatomy_queries`.

## The Jacobian, in full (registered in round 7; 3 seeds, central differences)

Mean J, rows (G3, G6, G2) × columns (θ_s=`spectrum_decay`, θ_q=`query_tail`,
θ_r=`equalize`); [`r7_jacobian.json`](r7_jacobian.json):

```
[ -9.94    -0.0067  -0.0012 ]
[ -0.074    0.048   -0.0030 ]
[  0.44    -0.011    0.0032 ]
```

- **θ_s → G3: proven locally** (−9.9, two orders dominant in its column) and
  validated prospectively by the warm start.
- **θ_q → G6: established large-signal, saturated locally.** The mean is positive but
  the per-instance derivative flips sign (+0.19/−0.12/+0.08, same-seed central
  differences — landscape heterogeneity, not estimator noise): at `query_tail = 2.35`
  the knob is near the top of its 0.19×→2.20× sweep. The axis is real; its local slope
  there is not usable.
- **θ_r → G2: locally inert** (~10⁻³): at `size_tail = 0.16` the substrate is already
  homogeneous — the knob's work is done. G2's largest local mover is in fact θ_s
  (+0.44): the colouring's spectral shape moves the d10 window.
- **The registered condition-number expectation is NOT met**: det ≠ 0 but
  cond(J) ≈ 4.1×10³ (and the row-dominance printout "all rows dominated by θ_s" is a
  units artifact — dominance was registered per column). Clean three-axis local
  controllability is **not** established at this operating point: one axis is local,
  one large-signal, one exhausted. Reported as the partial miss it is; the
  inverse-function-theorem claim stays restricted accordingly in the paper.

Nothing here passes RC-1; the seal is untouched (RC-1 admission additionally requires
battery A, all k, and cell-wise gates — G4 among them). Numbers:
[`gen_round8_anatomy.json`](gen_round8_anatomy.json), [`r7_jacobian.json`](r7_jacobian.json).
