# A learned emitter: scaffold works, first fit inconclusive

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-09. Module
[`openvector_bench/learned_gen.py`](../openvector_bench/learned_gen.py), driver
[`harness/rc1/fit_learned_gen.py`](../harness/rc1/fit_learned_gen.py), record
[`learned_gen_fit.json`](learned_gen_fit.json).

## Why try a learned map at all

`R25_ANISOTROPY_CONTROLS.md` established that the ramp is carried by structure
**beyond the first two moments** — a Gaussian with real's exact mean and
covariance gives +0.021 against real's +0.511 — so any family determined by its
covariance is excluded a priori. `family_profile_scan.json` then found all ten
registered families produce a *falling* profile at every rung. Six are closed on
mechanism. Hand-designing the missing structure has failed repeatedly; a learned
map obtains it without having to guess its form.

## Three things the scaffold establishes

**1. It is cheap enough to be legal.** `DISTRIBUTION.md` §3 orders sources
*regenerate → cache → mirror* because regeneration beats fetching. That is a
**ratio**, so no amount of compute rescues a slow emitter — this is what kills
the encoder route, where LaBSE's 17.7 kB/s/core is ~2300x slower than the
network. The bound is ~4 MFLOPs/row; a 1024→64→1024 map costs **0.131
MFLOPs/row**, thirty times inside it.

**2. It can be bit-exact.** Noise comes from `bitmap_gen`'s splitmix64, so it is
integer-exact and random-access. The Gaussian uses **Irwin-Hall** (twelve
uniforms minus six) rather than Box-Muller or an inverse CDF, because that needs
only additions — no transcendentals, no libm. The only remaining float work is a
small fixed matmul plus `tanh`, both pinnable in a fixed-point port.

**3. The objective is the geometry itself, not a surrogate.** I had previously
claimed the battery is non-differentiable and would need one. That is wrong:
`s(r)` derives entirely from `r(k)`, and `torch.topk` passes gradients to the
selected distances, so exact k-NN sits inside the autograd graph.

Verified: the numpy deployment path and the torch graph agree to **5.5e-08**, so
a fitted map emits through the real code path rather than existing only inside
autograd.

## The first fit does not reproduce the profile

Evaluated through the deployment path with the registered estimator, 3000
queries, three seeds:

| rung | target ratio | fitted (mean ± sd) |
|---|---|---|
| 5,000 | 1.576 | 0.274 ± 0.027 |
| 10,000 | 2.151 | 0.335 ± 0.040 |

Target trend +0.828, fitted **+0.088**.

## Why this is inconclusive rather than a refutation

Training loss reached 5e-5 while the true ratio sat at 0.27. That gap is the
result: **the optimiser was fitting noise.** With 384 queries and a freshly
resampled rung subset at every step, the median `r(k)` values it chased were
themselves noisy, so a low loss on noisy draws is not a fit to the curve. The
shape term also averages fifteen consecutive differences, diluting precisely the
endpoint errors that the ratio depends on.

So the run says nothing about whether a per-row map of hash noise *can* express
the ramp. That question — whose negative answer would be the more valuable one,
since it would make row-to-row dependence *necessary* rather than optional —
remains open.

### An objective bug worth recording

The first attempt scored `Σ (log r_gen(k) − log r_real(k))²`. That is dominated
by the overall *scale* of the radii: a near-constant offset in log r contributes
most of the loss and nothing to the profile. The optimiser reduced the loss 3x
while the trend rose to +0.619 at step 40 and then **collapsed to −0.282** — it
walked away from a good profile because the objective did not reward it. Since
`s = dlog k / dlog r` and `dlog k` is fixed by the grid, matching `dlog r` *is*
matching `s(r)`; the loss now scores consecutive differences with the level
pinned separately and weakly.

Two incidental facts from that failed run are worth keeping: the map reached
trend **+0.619** unprompted, so it is not obviously incapable; and the
deployment-path check passed there too.

## What it would take to conclude

1. Queries ≥ 2000 and a **fixed** rung subsample, so the objective is not itself
   noisy — this is the change that matters most.
2. Endpoint-weighted or ratio-explicit loss terms, so the statistic being
   targeted is the one the spec scores.
3. Evaluation through the deployment path at every checkpoint, not the in-loop
   diagnostic, which was misleading in both runs.
4. A capacity sweep; hidden=64 was chosen for cost headroom, not from evidence.

## Standing caveat

If a fit ever succeeds, it establishes only that *some* memoryless per-row map
can produce the profile — not that the mechanism is right. 131k parameters
against 48 targets is Goodhart-maximal, exactly what `GENERATOR_SEARCH.md` §5
exists to distrust, and adversarial validation plus RC-2 would carry the entire
evidentiary burden.
