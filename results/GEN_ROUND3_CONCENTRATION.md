# Generator search — round 3: concentration breaks the intrinsic-dimension wall

**Run:** 2026-07-21, NRP Nautilus, 12-shard swarm (indexed Job, cpu=1 each; 480
random-search evals total), **corrected harness** (battery-B queries held out from
the same instance — see below). n=8000, battery B, k=10, train/val only, seal
untouched. Family: `concentration_corpus`.

## The harness bug this round exposed (and fixed)

The first run of this search looked like a total failure — intrinsic dimension
stuck at ~5.4× on every shard, *independent of `local_dim`*. That didn't fit the
theory, so it was diagnosed rather than concluded. `make_evaluate_fn` built the
generator's query set from an **independent seed**; for an instance-random
generator (clusters/subspaces keyed on the seed) a different seed is a *different
manifold*, so the queries landed off the base's clusters and two-NN measured
cross-instance (~300) dimension. Real `queries.npy` lie on the real manifold, so
real never had the problem — the harness silently penalised every concentrated
family. A 3-way diagnostic (local_dim=57):

| battery-B queries formed by… | G1 | G8 |
|---|---:|---:|
| **same instance, held-out split** | **61.7** (real 57.7) | **0.67** (real 0.62) |
| independent seed (the bug) | 328 | 0.07 |

Fixed: one instance split into base + held-out queries (the faithful analog of
real's held-out queries). This also means the prior battery-B G1 numbers for
instance-random families (rounds 1–2 manifold, EC `ec_torus`) were partly
confounded and deserve a recheck under the fix.

## Result: three gates matched at once, including the two that blocked every prior round

Real (n=8k): `G1 id=57.7, G3 eff-rank=187.9, G6 hubness=6.83, G8 pca-ret=0.62`.

| gate | best shards (of 12) | verdict |
|---|---|---|
| **G1 intrinsic dim** | **0.95–1.14×** | **SOLVED** — was stuck at 5.3× in rounds 1–2 |
| G3 effective rank | 0.85–1.28× | reachable (cluster count × spread) |
| G8 PCA retention | **0.95–1.03×** | **SOLVED** — every smooth family died at 0.06–0.12× |
| **G6 hubness** | 0.13–0.21× | the remaining wall |

Best point (shard 8, score 0.493): `G1=55.2 (0.96×), G3=240.8 (1.28×),
G8=0.59 (0.96×), G6=1.0 (0.15×)`; knobs `local_dim≈80, log2_clusters≈3.8,
center_spread≈0.20, within_scale≈0.28, size_tail≈0.50, curvature≈0.79`.

**Why it worked — reach.** Each cluster is a flat `local_dim`-dim linear patch in
its own random subspace (a Grassmannian sample). A flat patch has infinite local
reach (Niyogi–Smale–Weinberger, *Geometric Methods* Ch. 5), so the two-NN
estimator reads the true local dimension — the exact cure for the "globally smooth
but locally wiggly" random-Fourier failure of rounds 1–2. The K independent
subspaces supply the effective rank (G3) and, crucially, break any single low-rank
subspace, which is why **PCA retention (G8) finally matched** — the gate no smooth
manifold could touch. The intrinsic-dimension wall is broken.

## The remaining wall: hubness (G6)

G6 is stuck at ~0.15× on *every* shard, even those with heavy-tailed sizes
(`size_tail≈2.2`) and strong hyperbolic centres (`curvature≈2.8`). Diagnosis:
hyperbolic-arranging a few dozen *cluster centres* does not create the fine
*per-point* density gradient real hubness needs — round 1 got hubness by mapping
*every point* into the Poincaré ball. The concentration family's hubness mechanism
is too coarse.

## Next (round 4): stratified frontier accumulation

The registered round-4 stratified family (`STRATIFIED_PREDICTION.md`) attacks
exactly this: `frontier_conc` piles points onto the low-dimensional strata — a
*per-point* density gradient — while the nested-subspace flags give a genuine
local-dimension *spectrum* (matching G1's centre and G7's spread together). If the
frontier pile-up supplies the missing hubness while holding G1/G3/G8, all three
mandatory gates land together for the first time. That is the next run.

Nothing here passes RC-1; the seal is untouched. Numbers:
`results/gen_round3_concentration.json`.
