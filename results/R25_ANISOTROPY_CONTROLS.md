# Anisotropy is neither sufficient nor necessary for the dimension ramp

**Exploratory, not a registered round.** A measurement of the TARGET; no
generator, no admission claim, seal untouched. Measured 2026-08-09 on Atlas,
registered head pool (600k contiguous rows), registered protocol, so every
number compares directly with the anchors. Driver
[`anisotropy_controls.py`](../harness/rc1/anisotropy_controls.py), record
[`anisotropy_controls.json`](anisotropy_controls.json).

## The objection this closes

Real embeddings are famously anisotropic — a narrow cone rather than a sphere
(Mimno & Thompson, EMNLP 2017; Gao et al., "representation degeneration", ICLR
2019; Ethayarajh, EMNLP 2019). This corpus shows it plainly: ‖mean(X)‖ = 0.477
on unit vectors, effective rank 182 of 1024 ambient, and the whole measurement
band at r ∈ [0.86, 1.13] where the chordal maximum is √2 ≈ 1.414.

So the first response to a rising growth dimension is: *this is a restatement of
known anisotropy.* That had to be answered with measurements. The anisotropy
literature is entirely **global** — average cosine, IsoScore, spectral decay —
and has never been scale-resolved, so there was nothing to cite in either
direction.

## Design: two tests pointing opposite ways

**A. Synthesize the anisotropy alone.** A Gaussian with the corpus's *exact*
empirical mean and covariance, unit-normalised: real's cone, real's spectrum,
real's effective rank, and nothing else. If anisotropy produced the ramp, this
must reproduce it. (A far sharper null than `null_lowrank`, whose linear
1.0→0.3 taper at rank 190 is not real's spectrum.)

**B. Strip the anisotropy from real.** Two variants, because whitening is not
unique — and reporting both was pre-committed, since disagreement would itself
have been the finding:

* `whitened_topk` — PCA-whitening inside the top-K subspace holding 99% of
  variance (K = 659). Restricting to top-K keeps the inverse well-conditioned;
  a full Σ^−1/2 would amplify near-null directions into noise and test nothing.
* `abtt_8` — all-but-the-top (Mu & Viswanath, ICLR 2018): centre and project out
  the 8 leading principal directions.

Every arm reports ‖mean‖ and effective rank, so each manipulation is auditable
rather than asserted.

## Results

| arm | dim | G1 exponent | s_ratio trend | ‖mean‖ | eff. rank |
|---|---|---|---|---|---|
| real | 1024 | −0.168 | **+0.511** | 0.477 | 182 |
| gaussian_exact_cov | 1024 | +0.062 | **+0.021** | 0.480 | 196 |
| whitened_topk | 659 | −0.179 | **+1.030** | 0.016 | 620 |
| abtt_8 | 1024 | −0.172 | **+0.624** | 0.019 | 270 |

*Synthetic families for reference: |trend| ≤ 0.13.*

**The manipulations did what they claim.** The Gaussian matches real's
anisotropy to within noise (‖mean‖ 0.480 vs 0.477; effective rank 196 vs 182).
Both whitening variants remove it (‖mean‖ → 0.016 / 0.019; effective rank → 620
/ 270).

## Conclusions

1. **Anisotropy is not sufficient.** A Gaussian carrying real's exact first and
   second moments gives a trend of **+0.021** — flat, inside the synthetic
   control band. Everything reproducible from the mean and covariance produces
   no ramp.
2. **Anisotropy is not necessary.** Both de-anisotropised versions of real keep
   the ramp (**+1.030** and **+0.624**) and keep the ladder unchanged (−0.179
   and −0.172 against −0.168). The two independent routes agree, which was the
   pre-registered condition for a clean read.
3. **The cone was partly masking the effect.** Removing it *strengthens* the
   ramp, because anisotropy compresses the measurement band: r ∈ [0.86, 1.13]
   for real against [1.14, 1.35] whitened, so clearing the cone exposes more of
   the profile.

The objection is closed from both sides. The ramp is carried by structure
beyond the second moment — which is also why no Gaussian-based null, however
carefully matched, has reproduced it.

## Limits

* The whitened arm lives in a 659-dimensional subspace, so its ramp is a
  property of that projection of real, not literally of real. `abtt_8` keeps all
  1024 dimensions and agrees, which is why both were run.
* This says nothing about *what* does carry the ramp — only that it is not the
  first two moments. Third-and-higher-order structure, hierarchical topical
  composition and near-duplicate density all remain live and untested.
* One pool, one embedding model. `R23_F2_TRANSFER.md` covers cross-model
  transfer; `R24_SAMPLING_PROTOCOL.md` covers cross-position stability.
