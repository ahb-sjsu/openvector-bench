# A path inside the article fixes hubness and costs the intrinsic dimension

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/path_probe.py`; records
`results/path.json`, `path2.json`. Follows `R40`.

## Where the constraint had moved

`R40` found that `fil_scale` governs g5 and `eff_rank` together, reaching both
targets near 1.0–1.4, at the cost of g6 hubness exploding to 21. g6 is
mandatory, and no round had attacked it.

The book does not help here — its only use of "hub" is Kleinberg's
hubs-and-authorities for link analysis (pp. 62, 66), not k-occurrence hubness.
The mechanism came from the project's own measurements instead.

`build()` places the 23 article rows **i.i.d. in a `fil_dim`-ball**. With 23
points in a 22-dimensional ball, whichever row lands nearest the ball centre is
the nearest neighbour of many of its siblings — one systematic hub per article,
across 26,000 articles, worsening as `fil_scale` makes articles ball-dominated.

Real's article is not a ball but a **path**: `R30` measured cosine decaying
0.598 → 0.304 across index gaps 1 → 16. In a path no row is central to all
others. `R33` closed the cascade as a *global* model; within a 23-row article it
is exactly what was measured.

## An implementation error, and what it cost

The first attempt drew fresh coefficients per row at every level, sharing only
the *directions*. That is a 110-dimensional ball, not a path, and it sent g1 to
**85.52** against real's 17.23 while halving g6. It tested nothing.

Corrected, the coefficients are shared within each block of `2^s` consecutive
positions, so rows near each other in the article genuinely share structure.

## Result

| build | fil_scale | w_mean | g5 | eff_rank | g1 * | g6 * | random cos | b=100 ratio |
|---|---|---|---|---|---|---|---|---|
| **real** | | | **1.369** | **182.3** | **17.23** | **1.696** | **0.2279** | **4.050** |
| ball | 0.45 | 0 | 2.658 | 75.7 | 17.80 | 1.586 | 0.011 | 5.437 |
| ball | 1.00 | 0 | 1.551 | 166.4 | 17.86 | 18.438 | 0.007 | 6.173 |
| path | 0.70 | 0 | 1.993 | 106.3 | 10.16 | **1.637** | 0.009 | 7.889 |
| path | 1.00 | 0 | 1.609 | 165.9 | 10.05 | 8.126 | 0.007 | 9.448 |
| path | 1.40 | 0 | **1.386** | 283.5 | 9.94 | 13.091 | 0.005 | 11.505 |
| path | 1.00 | 1.0 | 1.626 | 167.8 | 10.16 | 16.970 | **0.3253** | 8.129 |

**The mechanism is confirmed.** At `fil_scale` 0.70 the path gives g6 = 1.637
against real's 1.696 — within 3.5% — where the ball at the same setting gave
3.754. Replacing the ball with a path cuts hubness by more than half at fixed
spread, exactly as the one-hub-per-article account predicts.

**And it costs g1.** The intrinsic dimension is now pinned near 10 (10.16, 10.05,
9.94, 10.16) regardless of `fil_scale`, against real's 17.23. The ball had g1 at
17.8–17.9, matched. A path through 22 directions with geometrically decaying
weights is locally lower-dimensional than a ball in those same directions —
locally, only the fastest level varies.

`w_mean` behaves as `R40` predicted for anisotropy — 1.0 gives random cosine
0.3253 against real's 0.2279, so roughly 0.65 is indicated — but it inflates g6
from 8.126 to 16.970, so it is not free after all.

## Status: the three mandatory gates are pairwise reachable, never jointly

| configuration | g1 | g5 | g6 |
|---|---|---|---|
| ball, fil_scale 0.45 | ✓ 17.80 | ✗ 2.658 | ✓ 1.586 |
| ball, fil_scale 1.00 | ✓ 17.86 | ~ 1.551 | ✗ 18.438 |
| path, fil_scale 0.70 | ✗ 10.16 | ✗ 1.993 | ✓ 1.637 |
| path, fil_scale 1.40 | ✗ 9.94 | ✓ 1.386 | ✗ 13.091 |

No configuration measured gets all three. The ramp is separately worse
throughout this sweep — 7.9 to 11.5 against 4.050 — where `R36`'s linear ball at
`fil_scale` 0.45 gave 3.900.

## What is established

* The hubness mechanism is identified and demonstrated: i.i.d. article members
  create one hub each; a path does not.
* g6 is reachable (1.637 against 1.696) and is no longer an unattacked gate.
* g1 and g6 trade against each other through the ball-versus-path choice, and
  g5 trades against g6 through `fil_scale`.

## What is not

* Whether an intermediate structure — a path with a wider fastest level, or a
  path plus a small isotropic component — recovers g1 while keeping g6. Only the
  two extremes were measured.
* The §3b spans and s(k) curves for any path arm; only the b=100 ratio was
  carried through.
* The article size has been fixed at 23 and `size_spread` at 0 in every arm of
  this arc. Heavy-tailed group sizes are the standard hubness mechanism and
  remain untried, as does the Zipf occupancy already exposed in `PARAMS`.

## Operational note

Package 0 reached 83 °C during this round with two of my own probes running
concurrently. Per the standing thermal rule I shed the stale one — the probe
running the buggy path implementation, whose output was invalid — and
temperatures returned to 75–77 °C. No user workload was affected.
