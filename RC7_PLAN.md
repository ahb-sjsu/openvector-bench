# RC-7: the continuum arrangement

**Status: plan, 2026-08-13.** Designed from RC-6's kill
(`results/RC6_VERDICT.md`): additive components cannot scatter partitions
at geometry-compatible amplitudes, in three compositional forms. The
remaining explanation is architectural — **the family's coarse structure
is discrete generative clusters, and k-means recovers them by
construction.** Real's IVF recall climbs slowly across ~50 cells because
its neighbourhoods straddle the arbitrary boundaries a partitioner draws
on an *unclustered continuum*. RC-7 replaces the clustered arrangement
with exactly that.

## 1. The mechanism

The nested-cluster arrangement (27·branch^L articles per cluster, one
frame per level) is replaced by a **smooth coarse manifold**:

* each article draws a latent position `u_a ∈ [0,1)^d_lat` (keyed
  uniform — random-access clean);
* its coarse vector is a **band-limited random field** evaluated at
  `u_a`: a sum of random Fourier features over `n_freq` frequencies per
  octave, with per-octave bandwidths mirroring the old per-level frames
  (the octave ladder preserves the multi-scale structure that carried
  the §3 trend, `R66`), each octave in its own subspace;
* nearby latents → nearby coarse vectors, with no cluster boundaries
  anywhere: k-means must tile the manifold arbitrarily, and any
  neighbourhood of extent comparable to a tile straddles several.

Everything else — articles, segments, path + ball, rho, pool_alpha, and
(pending `R85`) the near-dup ladder — is inherited from the standing
candidate.

Bit-exactness note for the eventual port: `cos` is libm; the package
implementation uses a frozen quarter-wave table (the article-law trick,
`R48` discipline). The harness explores with `torch.cos`.

## 2. Registered predictions and kills

* **P1 (scatter).** nprobe@95 rises with coarse weight and field
  curvature (bandwidth), toward real's 47–50, because tile boundaries
  cut neighbourhoods — with **no outlier components** (occupancy CV
  should stay near real's 0.39, unlike RC-6's 0.55+). **Kill:** np95 ≤ 5
  everywhere the mandatory trio holds ⇒ the continuum hypothesis is
  refuted and partition scatter is recorded as beyond both families.
* **P2 (regression).** The octave ladder preserves the §3 trend and
  spans within the 14-block bands at some operating point — the
  continuum must not cost the density response the clusters carried.
  **Kill:** trend cannot re-enter [0.357, 0.657] anywhere np95 > 10.
* **P3 (anatomy).** same-article fraction of top-10 falls toward real's
  ~0.66 as the coarse field gains weight — cross-article neighbours now
  arise from latent proximity (ambient, not clustered), the form RC-6's
  topics could not supply.

## 3. Phases

* **A** — harness screening on the `R85` base: d_lat {2, 4, 8} ×
  bandwidth octaves × coarse weight, full panel + ANN panel. 16 arms.
* **B** — composition/refinement at the P1 pocket; brk/rho re-centring.
  ≤2 sweeps.
* **C** — package port (cosine table, defaults inert), fidelity,
  multi-seed.
* **D** — freeze + one-shot on fresh blocks with BOTH panels registered,
  expected outcome declared first; only if the robust scorecard beats
  the standing candidate on the joint (geometry ∧ np95).

Envelope ≤4 harness sweeps. Heavy sweeps run on Atlas GPU 1 (the NRP
watchdog kills long hashing pods, `RC6_VERDICT` budget note). Budget so
far: 0 arms.
