# Hubness is super-cluster density, and the floor was a held-fixed parameter

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/wloc_probe.py`; records
`results/wloc.json`, `wloc2.json`. Follows `R43`, which it corrects.

## The floor was not a floor

`R43` reported that g6 hits a floor near 7 at `fil_scale` 1.00 — four
combinations of the two known mechanisms landing within 5% of each other — and
that two hypotheses for its cause were refuted. It is not a floor. **`w_loc` had
been 0.4 in every arm since `R36` and was never varied against g6.**

This is the third time in this arc that a "nothing moves X" conclusion turned
out to be a statement about the sweep rather than the family — after g5 in `R38`
(corrected in `R40`) and rank-versus-ramp in `R38` (corrected in `R39`).

## The mechanism

Hubness is created by **density inhomogeneity**: points in denser regions become
neighbours of many others. In this construction the centre of an article is
`cs[super] @ bg + w_loc * (per-article)`, so with 110 articles per super-cluster
and a large `fil_scale`, the articles of one super-cluster overlap and each
super-centre becomes a dense blob — a hub region. `w_loc` sets how much of a
centre is its own rather than its super-cluster's.

Measured in both directions, at `fil_scale` 1.00, `path_mix` 0.7,
`size_spread` 1.2:

| w_loc | per_super | eff_rank | g6 |
|---|---|---|---|
| 0.4 | 2000 | 21.3 | 47.684 |
| 0.4 | 400 | 74.2 | 19.882 |
| 0.4 | 110 | 157.2 | 7.171 |
| **0.8** | 110 | 203.7 | **1.849** |
| 1.5 | 110 | 300.1 | 1.819 |
| 3.0 | 110 | 356.3 | 1.882 |

Strengthening the super-cluster level (larger `per_super`) drives g6 to 47.7;
weakening it (larger `w_loc`) collapses g6 to 1.85, real's value being 1.696.
Beyond `w_loc` 0.8 hubness stops responding entirely — 1.849, 1.819, 1.882 — so
the mechanism saturates once the clumping is gone.

## On dimensionality

Hubness is known to grow with intrinsic dimensionality through distance
concentration (Radovanović et al., 2010), and this family shows it: across the
`fil_scale` scan of `R43`, `eff_rank` 106 → 126 → 157 tracked g6 1.79 → 5.13 →
7.17.

**Real is the counterexample.** It has the highest effective rank measured
(182.3) and the lowest hubness (1.696), so dimensionality cannot be the whole
account. The `w_loc` result shows why: raising it took `eff_rank` from 157.2 to
203.7 while g6 fell from 7.171 to 1.849 — the two moved in *opposite* directions,
which the dimensionality effect alone cannot produce. Density inhomogeneity was
the dominant term, and once removed the two decouple.

## All three mandatory gates, together

With g6 stable, `fil_scale` is free to spend on g5 (`R40`: it drives g5 down).

| w_loc | fil_scale | g1 * | g5 * | g6 * | eff_rank | b=100 ratio |
|---|---|---|---|---|---|---|
| **real** | | **17.23** | **1.369** | **1.696** | **182.3** | **4.050** |
| 0.8 | 1.00 | 16.03 | 1.859 | 1.849 | 203.7 | 7.728 |
| 0.8 | 1.40 | 16.00 | 1.549 | 1.882 | 310.9 | 8.599 |
| **0.8** | **1.80** | **15.96** | **1.401** | **1.883** | 434.0 | 9.417 |
| 0.6 | 1.40 | 16.02 | 1.487 | 2.899 | 288.1 | 8.151 |
| **0.6** | **1.00** | **16.06** | **1.757** | **2.189** | **177.5** | 6.970 |

At `w_loc` 0.8, `fil_scale` 1.80 the three mandatory gates are simultaneously
within 11%: **g1 0.93x, g5 1.02x, g6 1.11x**. Nothing in the project has done
that. From `R40` through `R43`, g6 was 4–11x out whenever g5 was near.

At `w_loc` 0.6, `fil_scale` 1.00 the position is better balanced: g1 0.93x,
g5 1.28x, g6 1.29x, **eff_rank 0.97x** — four quantities within 30%, with the
ramp the only large miss.

## What is left

The conflict has moved **off the mandatory set**. g5 wants `fil_scale` ≈ 1.85
and `eff_rank` wants ≈ 0.95; both cannot hold, but `eff_rank` is not mandatory.

The ramp is now the dominant failure: 6.97–9.42 across this round against real's
4.050, and it has not been below 6.0 anywhere in `R42`–`R44`. `R36`'s 3.900
remains the best ever measured and came from a build that fails almost
everything else. No mechanism found since has improved it.

## What is established

* Hubness in this family is super-cluster density inhomogeneity, demonstrated in
  both directions.
* `R43`'s floor is withdrawn; it was `w_loc` held fixed.
* Effective rank and hubness are decoupled once the clumping is removed, which
  is why real can have both high dimension and low hubness.
* Two operating points now exist where the mandatory gates are jointly close.

## What is not

* The ramp. It is the one quantity that no mechanism in `R40`–`R44` has moved,
  and it is now the binding failure.
* §3b spans and s(k) curves at either new operating point — only the b=100 ratio
  has been carried through since `R41`.
* Whether `eff_rank` can be brought down at fixed g5 by a knob other than
  `fil_scale`; `d_glob`, `d_loc` and `fil_dim` were all held fixed at 90, 64 and
  22 through this round.
