# Density is the variable, and it excludes i.i.d. generators outright

**Registered as `PROFILE.md` §3b on 2026-08-10, before any generator was scored
against it.** Measured 2026-08-10. Drivers `harness/rc1/density_ladder.py`,
`harness/rc1/density_grid.py`, `harness/rc1/density_controls.py`; records
`results/density_ladder.json`, `density_grid.json`, `density_response.json`,
`density_controls.json`.

## What forced this

`R28` closed the filament family: it fit five targets at reduced scale and, at
the registered protocol, inverted the sign of the G1 exponent. The diagnosis was
that occupancy had been defined at pool level while the geometry responds at
rung level, and the two protocols differ 5x in the rung/pool ratio. The
requirement that followed was that a candidate must reproduce *how the profile
moves with density*, not merely its values at one operating point.

That requirement turned out to be measurable, sharp, and — for one large class
of generators — impossible to satisfy.

## The two ladders measure different things

`PROFILE.md` §3 varies n at a fixed 600k pool. A rung of n rows therefore sits
at density `n/600k`: **row count and density move together**, and the registered
`trend` is their sum. Separating them needs a factorial design.

Nine cells, n ∈ {25k, 50k, 100k} × pool ∈ {200k, 400k, 600k}
(`density_grid.json`):

| response | ∂/∂log n | ∂/∂log density |
|---|---|---|
| ratio | −0.189 ± 0.176 (1.1σ) | **+0.844 ± 0.137 (6.1σ)** |
| log G1 | +0.073 ± 0.037 (2.0σ) | **−0.217 ± 0.029 (7.6σ)** |

Two consequences.

**The registered trend is a near-cancellation.** +0.451 is the sum of a large
positive density term and a negative row-count term. A family can land the sum
at one operating point with both components wrong — which is precisely what the
filament family did.

**G1 is a function of density alone.** Its row-count partial is consistent with
zero, and its density partial (−0.217) sits close to the ladder exponent
registered in §3 (−0.170). Two independent measurements of what is evidently one
quantity.

## The registered ladder

Fixed n = 25,000; pool varies. Four independent contiguous 600k blocks at corpus
offsets 0 / 10M / 20M / 30M, so the quoted uncertainty is real block-to-block
variance (`density_ladder.json`).

| density | pool | ratio (± sd) | G1 (± sd) |
|---|---|---|---|
| 0.5000 | 50,000 | 3.722 ± 0.074 | 16.27 ± 0.58 |
| 0.2500 | 100,000 | 2.582 ± 0.144 | 17.08 ± 0.39 |
| 0.1250 | 200,000 | 1.774 ± 0.068 | 19.52 ± 0.36 |
| 0.0625 | 400,000 | 1.464 ± 0.018 | 23.62 ± 0.24 |
| 0.0417 | 600,000 | 1.325 ± 0.026 | 26.66 ± 0.56 |

**Row count is identical in every row of that table.** The ratio still moves 2.8x
and G1 1.6x. Density is the primary variable of this profile; row count is close
to incidental.

Registered summaries are fixed-endpoint contrasts: **ratio span +2.397 ± 0.085**
and **log G1 span −0.494 ± 0.054**, both between densities 0.500 and 0.0417.

### Why a contrast rather than a slope

The response is strongly convex — the local slope of ratio against log density
runs +0.41, +0.46, +0.98, +1.79 across the four intervals, a factor of four. A
slope fitted over the ladder would depend on which pools were chosen. That is
the same span dependence that disqualified `beta` in `PROFILE.md` §1, and it was
nearly repeated here: a linear fit was the first thing written, and only reading
the interval slopes showed it was a protocol-dependent number. The endpoints of
a contrast are part of its definition, so it has no such freedom.

## What this excludes, and why it is not a measurement

For a generator that emits rows **i.i.d.**, density is not a variable. Drawing n
rows from a pool of 50,000 and from a pool of 600,000 yields identically
distributed samples, so both spans are exactly zero. **No parameter setting
changes this**, because no parameter can make an i.i.d. sample aware of how many
siblings were generated alongside it.

Measured at the registered protocol (`density_controls.json`):

| family | ratio span | log G1 span |
|---|---|---|
| **real (target)** | **+2.397 ± 0.085** | **−0.494 ± 0.054** |
| i.i.d. isotropic Gaussian | −0.015 | +0.025 |
| i.i.d. Gaussian, real's exact mean + covariance | −0.004 | −0.002 |
| filament, 4 points/thread | +0.013 | +0.011 |
| filament, 48 points/thread | +0.014 | +0.025 |

A ~28σ separation on the ratio span, and the controls confirm the structural
argument rather than merely losing to it.

The exact-covariance control is the sharper of the two. `R25` established that
anisotropy is neither sufficient nor necessary for the *ramp*; this extends that
to the density response, and here the reason is structural rather than
empirical. Any family whose rows are conditionally independent given a fixed
parameter vector is excluded a priori, however elaborate that parameter vector
is.

This is the first registered criterion in the project that rules out a
construction **class** rather than a parameter region. Satisfying it requires
geometry resting on finite *shared* structure that subsampling genuinely thins —
a fixed set of centres, threads or latents — because only then does a pool exist
to be dense or sparse in.

**Shared structure is necessary but not sufficient**, and the filament rows
above are the demonstration. Both arms have threads, and both span ~0. The
reason is `filament_gen.py:126`, `owner = rng.integers(0, n_thread, n)`: thread
membership is assigned uniformly at random over the row index, and `n_thread` is
fixed by the *generation* size rather than the pool. A prefix of P rows
therefore contains every thread, thinned proportionally, and the expected
co-thread count in a draw of n is `n/n_thread` **independent of P**. The family
has structure; it has no density variable. `R30` follows this up — it is a
property of row ordering, and it is fixable.

## An error worth recording

The first factorial grid drew **one** holdout from the 600k corpus and then used
`body[:P]` as the base for each pool. For P < 600k that makes the split
non-exchangeable: the queries span the whole corpus while the base spans only
its head. This is the defect `R23` documents (G1 16.1 → 65.7 under a
non-exchangeable split), reintroduced two rounds after being catalogued.

It is worth recording because of *how it failed*. G1 read 39.1 / 30.3 / 26.0
across pools 200k / 400k / 600k — smooth, monotone in pool size, and entirely
plausible as a density effect. The only tell was that the 600k cell, where the
split is exchangeable by construction, matched the known-good value exactly
while the others did not. An artifact that varies smoothly with the variable
under study is not self-announcing, and the per-pool holdout is a correctness
requirement rather than a refinement.

## What is now in the fitness

`generator_search.make_evaluate_fn` gains `density_target`, and two prior
defects are fixed:

1. **The rungs now come from a 600k pool** (`profile_pool`). They previously came
   from a pool of `max(profile_ns) + profile_nq` = 205k, putting the top rung at
   97.6% density against the target's 33%. The fitness was scoring candidates
   against a target measured at a density they never operated at — the same
   error class as `R28`'s occupancy definition.
2. **Queries are a uniform holdout from the pool**, not a tail slice.

One 600k pool serves both terms, so the density criterion adds only five k-NN
passes at fixed n = 25,000.

## What this does not establish

* **No generator passes.** This is a sharper criterion, not a candidate. It
  narrows the search space by excluding a class; it does not indicate what
  inside the remaining class would work.
* **The spans are registered at n = 25,000 only.** Whether they are stable in
  the fixed row count is `PROFILE.md` P5 and is not yet measured.
* **Why real has this response is not explained.** That a fixed finite corpus
  thins under subsampling is the mechanism in outline, but nothing here says
  which structure — topical, near-duplicate, or something else — carries it.
