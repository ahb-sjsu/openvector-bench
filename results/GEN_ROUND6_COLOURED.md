# Generator search — round 6: P1 CONFIRMED — the first five-gate joint match of the campaign

**Run:** 2026-07-22, NRP Nautilus, 12-shard swarm (indexed Job, cpu=1 each; 480
random-search evals + anchored defaults). n=8000, battery B, k=10, train/val only,
seal untouched. Family: `hier_coloured_corpus` (round-5 Zipf centre hierarchy inside
a designed Mahalanobis recolouring). Pre-registration (smoke disclosed):
[`HIER_COLOURED_PREDICTION.md`](HIER_COLOURED_PREDICTION.md).

## Result against the registered predictions

Real (n=8k): `G1 id=57.7, G3 eff-rank=187.9, G6 hubness=6.83, G7 local-ID IQR=20.8,
G8 pca-ret=0.62`.

**P1 — CONFIRMED.** The best point (shard 11, score 0.355 — the lowest of the
campaign; round-5 best was 0.697, round-3 0.493) holds **all five registered gates
inside [0.5, 2.0]× simultaneously**, and does so on three fresh seeds, not just the
search seed:

| gate | seed 0 | seed 1 | seed 2 | |
|---|---:|---:|---:|---|
| G1 intrinsic dim | 0.81× | 0.80× | 0.87× | ✓ |
| G3 effective rank | 0.58× | 0.58× | 0.52× | ✓ |
| G6 hubness | 0.92× | 0.60× | 0.64× | ✓ |
| G7 local-ID IQR | 0.94× | 1.04× | 0.99× | ✓ |
| G8 PCA retention | 0.76× | 0.77× | 0.79× | ✓ |
| G5 relative contrast | 1.20× | 1.21× | 1.20× | (✓, unregistered) |

Knobs: `local_dim≈75, log2_clusters≈10.8, n_levels≈4.3, level_decay≈0.51,
branch_tail≈0.58, within_scale≈0.47, size_tail≈1.35, spectrum_decay≈0.42,
reshape_mix≈0.79`. Five other shards also found G3-and-G6 jointly in band — the
region is broad, not a corner.

**The seed check earned its place.** The runner-up (shard 0: G6 = 1.36× on the
search seed) collapses to G6 = 0.40–0.47× on fresh seeds — a seed artefact the
score alone would have shipped. The winner's G6 (0.60–0.92×) is the noisiest of its
five gates (hubness skew is a heavy-tail statistic), but stays in band.

**P2 — CONFIRMED: the G6 × G3 axis is dead.** Shards with G3 in band span G6
0.25–1.36× *at the search's choosing* (shard 6: G3 = 3.37× with G6 = 1.19×; shard 3:
G3 = 1.52× with G6 = 1.00×). Rank and hubness now move independently — the round-5
falsification identified a limitation of codebook geometry, not of the problem.

**P3 — did not fire.** The registered risk (colouring's local distortion
un-tunable) was wrong: the search recovered G1/G7/G8 into band while keeping the
colouring strong (`reshape_mix ≈ 0.79`). The local patches co-tune with the reshape.

## Honest scope: the next wall is G2, and RC-1 is still not passed

The registered P1 was the five gates above; the full battery has eight. At the best
point: **G2 ball-growth ID = 0.14×** (2.1 vs real 15.1) on every seed, and G4
dims90 sits at the band edge (1.93–1.99×). G2 reads the *growth* of neighbour
counts across radii: the family's neighbourhoods are two-scale (tight flat patch,
then a jump to the next cluster), so ball counts plateau where real corpora grow
smoothly through intermediate scales. A within-cluster radius *spectrum* (each
cluster a mixture of scales, not one `within_scale`) is the natural mechanism and
the round-7 candidate. Nothing here passes RC-1; the seal is untouched.

## The campaign scoreboard after six rounds

| gate | status | mechanism (round) |
|---|---|---|
| G1 intrinsic dim | **jointly matched** | flat local patches (3) |
| G3 effective rank | **jointly matched** | Mahalanobis recolouring (6) |
| G5 relative contrast | in band at best point | — |
| G6 hubness | **jointly matched** | Zipf hierarchical centres (5) + survives colouring (6) |
| G7 local-ID spread | **jointly matched** | size/depth heterogeneity (4→6) |
| G8 PCA retention | **jointly matched** | subspace diversity (3) |
| G2 ball-growth ID | **0.14× — the new wall** | none yet (round 7) |
| G4 dims90 | band edge (~2×) | partially owned by the colouring |

Numbers: [`results/gen_round6_coloured.json`](gen_round6_coloured.json)
(12 shards + full battery × 3 seeds at the top two points).
