# The local_dim re-fit fails, and says why in a useful way

Measured 2026-08-08 on Atlas. Driver
[`r19_localdim_fit.py`](../harness/rc1/r19_localdim_fit.py), record
[`r19_localdim_fit.json`](r19_localdim_fit.json). Capacity family at α = 0.38,
ladder n ∈ {25,000, 50,000, 100,000, 200,000}, k = 10, 10,000 queries at every
rung so ρ is matched, 2 seeds. Targets are P-17cG's corrected real values.

**No `local_dim` passes every rung. The defect is structural, not a mis-set
parameter.**

## The sweep

Real G1: **26.64, 22.78, 19.92, 18.42** across the ladder. Falling.

| `local_dim` | G1 at 25k / 50k / 100k / 200k | ratios |
|---|---|---|
| 12 | 41.0 42.1 43.5 45.3 | 1.54 1.85 2.18 2.46 |
| 18 | 37.3 37.9 39.4 40.1 | 1.40 1.66 1.98 2.18 |
| **24** | **37.3 38.7 39.6 39.7** | **1.40 1.70 1.99 2.16** |
| 30 | 38.5 40.0 40.7 42.3 | 1.45 1.76 2.04 2.29 |
| 40 | 42.4 43.6 45.0 45.6 | 1.59 1.91 2.26 2.48 |
| 55 | 47.9 50.0 50.5 52.1 | 1.80 2.20 2.54 2.83 |
| 75 | 55.8 56.9 59.4 61.6 | 2.09 2.50 2.98 3.34 |
| 94 (frozen) | 61.2 64.5 65.9 68.1 | 2.30 2.83 3.31 3.70 |

## Two independent failures, either of which is fatal

**The level cannot be reached.** G1 is not proportional to `local_dim`. Taking
it from 94 down to 12 moves G1 only from ~62 to ~41, and the function is not
even monotone: it bottoms out near `local_dim` 18 to 24 at G1 ≈ 37 and rises
again below that. The family has a **floor of about 37** at ambient dimension
1024, against a target that reaches down to 18.4. Half the target range is
unreachable at any parameter value.

**The trend runs the wrong way.** Real's G1 falls by a third across the
ladder, 26.64 to 18.42. The candidate's is essentially flat: at the best value
it reads 37.3, 38.7, 39.6, 39.7, drifting slightly *upward*. So the ratio
widens from 1.40 to 2.16 not because the candidate moves but because real
falls away from a stationary candidate.

`local_dim` is a level parameter. No setting of a level changes the sign of a
trend, which is why this was registered in advance as the outcome that would
mean the defect is structural. It is.

Since G1 is mandatory in **every** cell, the family cannot be admitted by
re-fitting this parameter, and the best available value would still fail all
four rungs.

## What this does not touch

**Round 18 stands.** Count growth lowers hub scaling and its rate does not. It
is a within-family contrast at matched ρ under one protocol, and a wrong
intrinsic dimension is common to both its arms.

**Round 17c stands.** Its +0.514 ± 0.065 against real's +0.51 is a hub-scaling
result measured against targets sampled correctly, verified in
[`R17G_BATTERY.md`](R17G_BATTERY.md).

Both remain true of a family that fails a different gate. That is not a
contradiction, it is what a battery of eight gates is for.

## What it gives the next family

A requirement precise enough to build against, which is more than the campaign
had an hour ago.

**Local intrinsic dimension must fall with n.** Real corpora become locally
lower-dimensional as they grow, which is what denser sampling of a manifold
does: more neighbours within the same radius means the local neighbourhood is
better approximated by fewer directions. The round-8 family has no mechanism
producing this. Its clusters are generated at a fixed latent dimension, so
adding rows fills the same subspaces and the measured dimension stays put.

A family that satisfies it needs local dimension to be a consequence of
sampling density rather than a parameter. That is the same move the
capacity-limited process made for cluster count, where the fix was to let the
quantity emerge from the draw rather than be set. Whether the same trick works
here is the next question, and it is a design question rather than a search.

**Second, the ambient floor needs explaining.** G1 bottoming at ~37 while
`local_dim` goes to 12 means something other than that parameter is setting
the measured dimension at the bottom of its range. Probably the between-cluster
geometry, since a query's nearest neighbours can span clusters. Worth one
cheap diagnostic before any family is built, because a floor at 37 would block
a corrected family too.

## Status

The frozen round-8 family, and everything derived from it including the
capacity variant, fails a mandatory gate for a reason no parameter fixes. The
family is not admissible and re-fitting will not make it so.

This is the clearest negative result the campaign has produced, and it is more
useful than the several ambiguous ones before it, because it names the missing
mechanism rather than reporting that a number was off.
