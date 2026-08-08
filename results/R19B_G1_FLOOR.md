# The G1 floor — my hypothesis was backwards, and what replaces it converges

Measured 2026-08-08 on Atlas. Driver
[`r19b_g1_floor.py`](../harness/rc1/r19b_g1_floor.py), record
[`r19b_g1_floor.json`](r19b_g1_floor.json). n = 25,000, dim 1024, k = 10,
10,000 queries, 2 seeds. Real G1 at this rung is **26.64**.

## The registered hypothesis is refuted, and the driver described it wrongly

I predicted that between-cluster geometry sets the floor, so that removing
clusters would remove it and adding clusters would raise G1.

**Both halves are backwards.** With one cluster G1 is **218**, not lower than
the clustered 39. And G1 **falls** steeply as clusters are added, rather than
rising.

The driver's pre-written verdict for this branch reads "neither removing
clusters nor sweeping their count moves the floor." **That text is wrong.**
Cluster count moves G1 by a factor of seven. The branch fired because the
condition only tested whether G1 *rises* with count, so an effect in the
opposite direction fell through to a description that does not fit. The
hypothesis is refuted, and the canned account of how is not to be trusted. The
lesson is that a pre-written verdict has to enumerate directions, not just
outcomes.

## What was measured

**PURE, one cluster.** G1 is flat and enormous, and `local_dim` is nearly
inert.

| `local_dim` | 6 | 12 | 24 | 48 | 94 |
|---|---|---|---|---|---|
| G1 | 218.3 | 215.2 | 214.6 | 211.1 | 202.4 |

**FROZEN, 78 clusters.** A U, minimum at `local_dim` 24.

| `local_dim` | 6 | 12 | 24 | 48 | 94 |
|---|---|---|---|---|---|
| G1 | 72.5 | 45.6 | **39.4** | 46.9 | 63.4 |
| purity | 0.462 | 0.364 | 0.281 | 0.228 | 0.199 |

**KSWEEP, cluster count at `local_dim` 12.** The lever.

| clusters | 1 | 4 | 16 | 78 | 256 |
|---|---|---|---|---|---|
| G1 | 215.2 | 179.3 | 103.2 | 45.6 | **32.4** |
| purity | 0.122 | 0.150 | 0.254 | 0.364 | 0.453 |

Cluster count is what sets G1, and it does so strongly:
**G1 ≈ 253 · k^−0.368** across two and a half decades, with residuals inside
±18%. Purity rises with count, so more clusters means neighbourhoods sit more
firmly inside one cluster, which is the opposite of what the hypothesis
assumed.

## The convergence

Extrapolating the fit to real's corrected targets:

| n | real G1 | clusters implied |
|---|---|---|
| 25,000 | 26.64 | ~454 |
| 50,000 | 22.78 | ~695 |
| 100,000 | 19.92 | ~1001 |
| 200,000 | 18.42 | ~1238 |

Those counts imply a cluster-growth exponent of **0.482**.

Round 17c swept the growth exponent from 0.22 to 0.55 and found hub scaling
statistically indistinguishable across the whole range, pooling to +0.514
against real's +0.51. **0.482 sits inside that range.**

So a single mechanism, cluster count growing as roughly n^0.48, would put the
family on real's value for hub scaling and produce the falling intrinsic
dimension that [`R19_LOCALDIM_FIT.md`](R19_LOCALDIM_FIT.md) found missing.
Round 18 already established that growth is the lever for the first. This says
it may be the lever for the second, for a different reason: more clusters
partition the space more finely, so neighbourhoods sit inside smaller and
lower-dimensional pieces.

That is the first time in this campaign that two independent gate failures
have pointed at the same knob.

## What this does not establish

**The level is far off.** The capacity family carries about 101 clusters at
n = 25,000 and would need roughly 454. That is 4.5 times more, and it is a
level change, not the growth change the convergence is about. Both are needed.

**Cluster size collides with the floor rule.** At 454 clusters and 22,222 base
rows the mean cluster holds 49 points. `local_dim` at the U's minimum is 24,
so 49 clears it, but not by much, and round 17b's precondition work showed
what happens when clusters approach the local subspace dimension.

**The fit is approximate.** Residuals reach 18% and the extrapolation to 454
runs beyond the measured range, which topped out at 256.

**The U in `local_dim` is unexplained.** G1 rises at both ends, which looks
like an isotropic noise term dominating when the structured signal is very
low-dimensional. That is a hypothesis suggested by a curve shape, not a
measurement, and inferring a mechanism from an outcome curve is the error this
campaign has made repeatedly. It needs its own test before anyone relies on
it.

**None of this is a registered result.** It is a diagnostic. The convergence
is a prediction to be registered and tested, not a finding.

## What to do next

Register a family with cluster count growing as n^0.48 from a level near 450
at n = 25,000, and test it against **both** gates at once. The prediction is
specific enough to fail cleanly: hub scaling within ±0.15 of +0.51, and G1
within its equivalence band at every rung. Both come from the same parameter,
so a family that hits one and misses the other refutes the convergence rather
than half-confirming it.
