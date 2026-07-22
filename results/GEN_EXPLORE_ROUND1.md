# Generator search — round 1: hyperbolic latent solves hubness; the ID/eff-rank coupling is the new wall

**Run:** 2026-07-22, on the real target (Cohere Wikipedia Embed-V3, en, 1024-d)
at `/archive/tqp_real/wiki1024`, `FAMILY=manifold`. Driver:
[`harness/generator/explore_search.py`](../harness/generator/explore_search.py).

Round 0 named the wall: the cluster-Gaussian family fills too many dimensions to
reach real embeddings' ~52-dim intrinsic dimension, and it could not make real
hubness. Round 1 introduces a **nonlinear low-dimensional manifold** family
(`manifold_corpus`): a `latent_dim`-dim latent, optionally mapped into a
**Poincaré ball** (`curvature` knob, the `exp₀` map from *Geometric Methods*
Ch 3 — whose conformal factor packs points near the boundary while a few sit
central, i.e. hubness), lifted to 1024-d through random Fourier features (a curved
immersion, so effective rank stays high and it is not low-rank). 50-eval random
search over the 7 knobs, battery B, n=15 000. **Train/validation only; sealed 25%
never loaded; not RC-1 admission.**

## Result: one gate solved, one gate worse

| gate | real | round-0 best | **round-1 best** |
|---|---:|---:|---:|
| G1 intrinsic dim | 52.6 | 128 (2.4×) | **329 (6.2× — worse)** |
| G3 effective rank | 189.5 | — | 119 (0.63×) |
| **G6 hubness** | 3.78 | 7.9 (2.1×) | **3.20 (0.85× — solved)** |
| G8 PCA-256 retention | 0.64 | — | 0.06 (0.10×) |
| weighted score | — | **0.558** | 0.940 |

Best knobs: `latent_dim≈32`, `freq_scale≈4.1`, `curvature≈2.99` (**at the max**),
`log2_clusters≈7.8`, `size_tail≈1.54`, `noise≈0.29`.

**The win — hubness, via hyperbolic geometry.** The search drove `curvature` to
its ceiling: the Poincaré `exp₀` latent produced hubness **0.85× real**, the
property `null_lowrank` and the round-0 Gaussian family could not make (both
≥2.1× off). The book's Ch 3 mechanism is the right one for hubness. Effective
rank also came within 0.63×.

**The setback — intrinsic dimension got worse, and the score rose.** Reported
plainly: round 1 does **not** beat round 0 overall. Two causes:

- **The RFF lift conflates ID with effective rank.** A high `freq_scale` buys
  eff-rank and hubness but folds the manifold, inflating the *local* intrinsic
  dimension far above `latent_dim` (32 → measured 329). One knob is pulling two
  gates in opposite directions.
- **Random search over 7 knobs is too weak.** The good region (low `freq_scale` +
  `latent_dim≈52` + high `curvature`) is a small corner; 50 random draws settled
  for hubness-at-the-cost-of-ID instead. This is a search limitation, not
  (yet) a proof the family cannot reach it.

## Next (round 2), two separable moves

1. **Decouple ID from effective rank.** Replace the single RFF `freq_scale` with a
   lift that preserves the latent's intrinsic dimension (mostly linear /
   low-curvature, so ID ≈ `latent_dim`) while raising effective rank separately —
   keep the hyperbolic latent for hubness.
2. **Use the real optimizer, not random search.** This is exactly the regime where
   Theory Radar (directed, learned pruning) beats random sampling over a 7-knob
   space, and where structural-fuzzing rejects any candidate that trades a
   mandatory gate away (as random search just did with G1).

Nothing here passes RC-1; the seal is untouched. Numbers:
`results/ovb_gen_manifold.json` (run artifact).
