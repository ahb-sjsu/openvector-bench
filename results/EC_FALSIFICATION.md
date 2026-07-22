# Can an elliptic curve generate embedding geometry? A registered falsification

**Run:** 2026-07-21, Atlas, on the real target (Cohere Embed-V3 Wikipedia, 1024-d,
`/archive/tqp_real/wiki1024`), non-sealed rows only. Driver
[`harness/generator/ec_experiment.py`](../harness/generator/ec_experiment.py),
generators [`openvector_bench/ec_generators.py`](../openvector_bench/ec_generators.py).
Grid: `n ∈ {8k, 16k}`, `k ∈ {10, 30, 100}`, both batteries (battery B on the real
`queries.npy`), 3 subsamples. **Train/validation only; the sealed 25% was never
loaded; this is a screening grid, not the sealed RC-1 admission run.**

The question: "can't you pick points on an elliptic curve as a generator?" It has
two readings, and we built and measured both.

## Result: every candidate is rejected — and two of my predictions were wrong

Ratios `T_gen / T_real` at battery B, `k=10`, `n=16000`. Real reference:
`G1 id=61.4, G3 eff-rank=190, G5 contrast=1.20, G6 hubness=9.44, G8 pca-ret=0.61`.
**Mandatory gates bold** (must be in `[0.85, 1.15]` in *every* cell to be admitted).

| gate | ec_ff (crypto) | ec_torus (geom) | gaussian_null | manifold_best |
|---|---:|---:|---:|---:|
| **G1 intrinsic dim** | **0.006×** | **5.63×** | **5.29×** | **5.31×** |
| G2 ball-growth | 0.57× | 6.68× | 8.14× | 7.08× |
| G3 effective rank | 4.62× | 0.50× | 5.07× | 1.19× |
| G4 dims-90 | 2.29× | 0.24× | 2.41× | 2.09× |
| **G5 rel. contrast** | **0.88×** | **0.87×** | **0.88×** | **0.87×** |
| **G6 hubness** | **0.14×** | **0.21×** | **0.13×** | **0.55×** |
| G7 local-ID IQR | 0.49× | 4.31× | 3.85× | 3.97× |
| G8 PCA retention | 1.00× | 1.52× | 0.06× | 0.08× |
| **admitted?** | **no** | **no** | **no** | **no** |

Nothing is admitted; no mandatory gate is even close for the EC objects. The
falsification stands. But the *failure modes* were not what I predicted, and the
honest record is that the prediction scorecard is mixed:

**ec_ff — I predicted it would mimic the iid Gaussian null (high intrinsic
dimension). Wrong.** It does the opposite: intrinsic dimension **collapses to
≈ 0.4 (0.006×)** and, worse, *decreases* with `n` (scaling slope **−1.37** vs
real ≈ 0). The mechanism is real, not an estimator artifact: the coordinates are
drawn from a finite table of `x`-values and the modular products `k·j mod ord`
collide, so the corpus contains **near-duplicate rows**; the two-NN estimator
correctly reports a degenerate near-zero dimension. Cryptographic diffusion does
not produce Gaussian-like geometry — it produces a *degenerate arithmetic
lattice*, an even more decisive (and different) failure than the null. Prediction
direction wrong; conclusion (rejected, far from real, no hubness at 0.14×) right.

**ec_torus — I predicted "right category (ID ≈ 52), no hubness." Half wrong, and
the wrong half is the interesting one.** Hubness is indeed absent (0.21×). But the
intrinsic dimension is **not** 52 — it reads **345 (5.63×)**, statistically
indistinguishable from the Gaussian null. A flat 52-torus uniformly sampled at
`n = 16000` is **undersampled**: `16000^(1/52) ≈ 1.2` points per dimension, so
every local neighbourhood looks random and the two-NN estimator sees the ambient,
not the manifold. **The right nominal dimension does not buy the right measured
dimension.** Real embeddings hit ID ≈ 61 at the *same* `n` because they are
**concentrated** — clustered and curved — so the local dimension reads low even
when the sample is sparse. This is the deepest output of the experiment: what
makes real embeddings hard is *inhomogeneity*, not low nominal dimension. It is
also the direct explanation for why the manifold family needs its clustering and
its hyperbolic curvature — and why "just use a low-dimensional manifold" fails.

## Scaling (slope of `log T` vs `log n`, battery B, k=10)

| gate | real | ec_ff | ec_torus | gaussian_null | manifold_best |
|---|---:|---:|---:|---:|---:|
| G1 intrinsic dim | +0.04 | **−1.37** | +0.05 | +0.08 | +0.05 |
| G6 hubness | +0.21 | +0.46 | +0.27 | +0.49 | +0.36 |

Real hubness **grows with `n`** (slope +0.21; the level rises from ~3 at `n≈12k`
to 9.4 at `n=16k`), which is itself a registered lesson: matching one `n` is not
enough, and the EC objects never enter the hubness regime at any `n`.

## What this settles, and what it leaves

- **Elliptic curves are not an embedding-geometry generator, in either sense.**
  The cryptographic object collapses the intrinsic dimension (near-duplicates);
  the geometric object is the right category but, flat and uniform, is
  statistically the null at realistic `n` and has no hubness. The very property
  that makes EC valuable for keys — uniform, unpredictable scalar multiples — is
  the property real embeddings most lack.
- **The lesson transfers to the search.** The blocker is not "find a low-dim
  manifold" (a torus is one and fails); it is "reproduce the *concentration* —
  the clustering + curvature that make a sparse sample read low-dimensional and
  produce hubness." Only `manifold_best`, via the hyperbolic latent, is even
  partway on hubness (0.55×) and effective rank (1.19×) here, and its hubness
  *grows* with `n` (slope 0.36) — the one candidate moving in the right
  direction. That is the family the generator search continues to refine.
- **My predictions are corrected in the record, not quietly dropped.** The
  headline claim (no EC construction is admitted) held; the two mechanism
  predictions did not, and are marked wrong above.

Nothing here passes RC-1; the seal is untouched. Numbers:
[`results/ec_experiment.json`](ec_experiment.json).
