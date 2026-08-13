# A learned emitter cannot produce the ramp — row-to-row dependence looks necessary

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

## Second fit, with the objective corrected: a meaningful negative

The first fit was inconclusive because the objective was noisy and mis-scaled
(both diagnosed below). With those fixed — scale-invariant loss, fixed rung
draws, 2000 queries, hidden width 128 (262k parameters, still only 0.26
MFLOPs/row) — the loss **converges** (9e-5, flat from step 80 through 199) and
the answer is stable:

| rung | target ratio | fitted |
|---|---|---|
| 5,000 | 1.576 | 0.387 |
| 10,000 | 2.151 | 0.427 |

Target trend +0.828, fitted **+0.057**. The map produces a *falling* profile —
ratio below 1 — like all ten hand-designed families. The residual is ~95%
relative error (real's `dlog r` is ~0.010 per k-step; RMS error 0.0095), so this
is not a near miss.

### Why a per-row map cannot do it — the mechanism

A per-row map sends iid noise through one fixed smooth function, so rows are iid
draws from a single pushforward distribution. At small radii a smooth map is
locally linear, so the local dimension tends to the Jacobian rank — **high** at
small r — and falls as curvature bites at larger r. A falling profile is what
this construction produces *by default*.

Real's profile rises, which requires neighbourhoods that are **low**-dimensional
at small radius: nearby rows constrained to a low-dimensional set — same article,
paraphrase, near-duplicate. With iid rows such neighbours occur only by
coincidence at a rate fixed by the density. In a real corpus they are
**structural**, and their density is what drives `s_lo` down as n grows.

This is the third independent route to the same wall: the filament family
saturates because one characteristic scale is resolved and then exhausted
(`R21C`); the cascade family cannot separate level-dominance from distance
collapse (`R21D`); and a per-row map cannot manufacture structural near-duplicates
at all. **Row-to-row dependence looks necessary, not optional.**

### Caveats on the negative

One architecture (2-layer MLP, tanh, skip), 200 steps, one learning rate, one
initialisation, two rungs. The loss plateau is evidence of convergence to *an*
optimum, not proof of the global one. The mechanism argument above is reasoning,
not measurement, and would deserve its own test — e.g. a deliberately
cluster-forming map, which is no longer a per-row map and therefore concedes the
point.

## Appendix: three objective bugs, each caught by arithmetic

Each produced a confident wrong answer, and each was found by checking a number
against the quantity it was supposed to represent rather than against intuition.

**Bug 1 — a noisy objective.** Training loss reached 5e-5 while the true ratio
sat at 0.27: the optimiser was fitting noise. With 384 queries and a freshly
resampled rung subset at every step, the median `r(k)` values it chased were
themselves noisy, so a low loss on noisy draws is not a fit to the curve. The
shape term also averages fifteen consecutive differences, diluting precisely the
endpoint errors that the ratio depends on.

**Bug 2 — a level term that dominated.** `w_level` was set to 0.05 to "weakly"
pin the radii. Real's log-radius span is only ~0.15 across the k grid, so each
`dlog r` is ~0.010 and the shape term is ~1e-4, while the level mismatch
contributed ~2e-3 — the nominally weak term was **25x** the one that mattered,
and the cheapest way to satisfy it was to shrink radii, which squashed the
profile. It is now zero, and that is a correctness point rather than tuning:
the registered statistic is scale-invariant (under `r -> c*r`, `dlog r` is
unchanged), so no level term is needed at all.

**Bug 3 — the wrong quantity entirely.** The first attempt scored `Σ (log r_gen(k) − log r_real(k))²`. That is dominated
by the overall *scale* of the radii: a near-constant offset in log r contributes
most of the loss and nothing to the profile. The optimiser reduced the loss 3x
while the trend rose to +0.619 at step 40 and then **collapsed to −0.282** — it
walked away from a good profile because the objective did not reward it. Since
`s = dlog k / dlog r` and `dlog k` is fixed by the grid, matching `dlog r` *is*
matching `s(r)`; the loss now scores consecutive differences, with no level
term at all (see Bug 2).

Two incidental facts from that failed run are worth keeping: the map reached
trend **+0.619** unprompted, so it is not obviously incapable; and the
deployment-path check passed there too.

## What would overturn the negative

1. A capacity or architecture sweep — one 2-layer MLP is thin evidence about the
   whole class of per-row maps.
2. More rungs and longer fits; two rungs and 200 steps is the minimum that
   supports a trend at all.
3. Most decisive: a deliberately cluster-forming map. If a **non**-iid
   construction reaches the ramp where this one cannot, that confirms the
   mechanism rather than just the outcome — though such a construction is no
   longer a per-row map, which concedes the point.

## Standing caveat

If a fit ever succeeds, it establishes only that *some* memoryless per-row map
can produce the profile — not that the mechanism is right. 131k parameters
against 48 targets is Goodhart-maximal, exactly what `GENERATOR_SEARCH.md` §5
exists to distrust, and adversarial validation plus RC-2 would carry the entire
evidentiary burden.
