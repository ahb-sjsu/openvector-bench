# Round 13 stage 0 — P-13A FAILS: the phenotype does not quantize

Measured 2026-08-07 on the real Cohere Embed-V3 corpus
(`/archive/tqp_real/wiki1024`, 42 sharded parts sampled across parts,
n_base = 49,979, n_query = 1,000 committed real queries, dim 1024, train/val
only, seal untouched). Driver `harness/rc1/r13_stage0.py`, raw record
[`r13_stage0.json`](r13_stage0.json). Registered in
[`PREREG_ROUND13.md`](PREREG_ROUND13.md) §4 P-13A with the v1.1 amendment.

**P-13A fails as registered. No layer-3 control work proceeds.** The
prereg's failure clause applies: report the measured dimensionality of the
phenotype space and stop.

## What was measured

A codebook fitted on latent features alone (layer 1 corpus geometry: three
neighbour radii, radius slope, local intrinsic dimension, anisotropy; layer
2 query exposure: query distance and query mass) is scored by how much it
tells us about held-out response (N_k at k = 10/30/100 and best
reverse-neighbour rank). Response never enters the fit. The baseline is the
best single latent feature cut into the same number of cells.

| K | MI ratio vs best single feature (k10 / k30 / k100 / rank) | ARI across seeds | passes |
|---|---|---|---|
| 2 | 0.30 / 0.27 / 0.27 / 0.24 | 1.000 | no |
| 4 | 0.41 / 0.39 / 0.41 / 0.40 | 0.833 | no |
| 6 | 0.42 / 0.40 / 0.42 / 0.42 | 0.965 | no |
| 8 | 0.44 / 0.43 / 0.45 / 0.45 | 0.568 | no |
| 10 | 0.46 / 0.45 / 0.47 / 0.47 | 0.450 | no |
| 12 | 0.46 / 0.46 / 0.49 / 0.48 | 0.467 | no |
| 64 (diagnostic, gates nothing) | 0.79 / 0.78 / 0.77 / 0.75 | — | — |

Registered thresholds were MI ratio ≥ 2.0 and ARI ≥ 0.7. The measured
ratio never exceeds **0.49** inside the registered ceiling, and the
reference partition at K = 64 — five times the ceiling — still reaches only
0.79. **A multivariate codebook of the latent space carries less
information about retrieval response than one-dimensional quantile binning
of a single latent feature, at every state budget tested.**

## Two findings, both robust

**1. Query exposure dominates every corpus-geometry feature.** The best
single feature is `query_mass` for **all four** response variables at
**every** K. Density, radius spectrum, local intrinsic dimension and
anisotropy each carry less information about who gets retrieved than a
scalar measure of how much query mass sits near a point. This is the
round-7 result measured directly on the corpus rather than inferred from a
gate: a point is not a hub because of where it sits, it is a hub because of
what the queries ask for. The three-layer separation the round-13 proposal
introduced is thereby vindicated as a *description* — layer 2 is not an
afterthought to layer 1, it is the dominant term — even though the
codebook built on it fails.

**2. The latent space has no well-separated modes beyond about six.**
Seed stability is high at K ≤ 6 (ARI 0.83–1.00) and collapses at K ≥ 8
(0.45–0.57). If the phenotype were a small set of discrete states, k-means
would recover them stably at the state count that matters. It does not.
Occupancies at K = 12 are also unremarkable, no dominant or empty state
(0.5 %–14 %), which is what a partition of a continuum looks like rather
than a discovery of modes.

Together: retrieval phenotype in real embedding geometry is a **continuum
dominated by one axis**, not a small alphabet of hubness states.

## Instrument limitation, stated plainly

k-means minimizes variance in the latent space, not mutual information
with response. With eight standardized features it spends its state budget
isotropically, so it resolves `query_mass` at roughly K^(1/8) levels while
the baseline resolves it at K. Part of the measured gap is therefore
attributable to the quantizer, not to the phenotype. The K = 64 reference
was added (prereg v1.1) to separate these and only partly succeeds: 64
cells over eight dimensions is still under two levels per axis.

What the diagnostic *does* establish is that the gap does not close with
scale — the ratio rises from 0.46 to 0.79 while the state budget rises
five-fold, and it does not cross 1.0. A phenotype that were genuinely
low-dimensional in these features should be reachable by an
isotropic partition once the budget exceeds the number of true states by a
wide margin. It is not.

A relevance-weighted quantizer (feature weights fitted on training rows,
response still held out for scoring — anti-circular) would test the
residual question. **That is a new registered prediction, not a re-run of
this one.** Re-testing the same hypothesis with a better instrument after
seeing this result and reporting the second number as the finding is
precisely the calibration circularity this round exists to avoid. The
author's call whether to register it.

## What survives for the campaign

- P-13B (anti-hub taxonomy) is **not gated on P-13A** and remains
  runnable: it asks whether the five anti-hub categories are separable by
  latent code and whether G6 is blind to them. Finding 1 raises its prior —
  if query exposure dominates, the category "points the query marginal
  never visits" should be both large and invisible to a corpus-side gate.
- P-13C (orthogonal control) is gated and does not proceed.
- The standing round-13 cascade proposal is untouched by this result: it
  concerns the subsample covariance of a generated density field, which
  this measurement does not address.

## Reproduction

```
CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=6 PYTHONPATH=<repo> \
R13_REAL_DIR=/archive/tqp_real/wiki1024 R13_N=50000 \
python3 harness/rc1/r13_stage0.py
```

Ran on Atlas CPU (the venv's torch cannot initialize against the installed
driver, so the GPU path was unavailable); package 0 held 77–79 °C against
its 82 °C mark throughout, inside the standing thermal rule.
