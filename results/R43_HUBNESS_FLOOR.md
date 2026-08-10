# The hubness floor is real, is not pool reuse, and sits on a monotone frontier

> **Corrected by `R44`.** The floor is **withdrawn**. `w_loc` had been 0.4 in
> every arm since `R36` and was never varied against g6; raising it to 0.8
> collapses g6 from 7.171 to 1.849 while *raising* eff_rank. The measurements
> below stand, as does the refutation of pool reuse; the claim that g6 cannot go
> below ~7 does not. Third instance in this arc of a "nothing moves X" reading
> that described the sweep rather than the family.

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/mix_probe.py`; records
`results/mix3.json`, `pool.json`. Follows `R42`.

## Composing the two mechanisms

`R42` found two hubness mechanisms working in opposite regimes but never composed
them at their best settings. All arms below at `fil_scale` 1.00, where g5 ≈ 1.6
and `eff_rank` ≈ 160:

| mix | spread | g5 | eff_rank | g1 * | g6 * | b=100 ratio |
|---|---|---|---|---|---|---|
| **real** | | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** |
| 0.0 | 0 | 1.551 | 166.4 | 17.86 | 18.438 | 6.173 |
| 0.7 | 0 | 1.590 | 165.6 | 14.90 | 11.316 | 8.066 |
| 0.4 | 0.8 | 1.616 | 162.3 | 17.73 | 9.825 | 6.753 |
| 0.7 | 0.8 | 1.634 | 162.1 | 15.42 | 7.964 | 7.608 |
| 0.7 | 1.2 | 1.684 | 157.2 | **16.17** | 7.171 | 6.546 |
| 1.0 | 0.8 | 1.655 | 161.8 | 10.59 | 7.143 | 8.943 |
| 0.85 | 1.0 | 1.667 | 159.4 | 13.42 | **6.819** | 7.879 |

They compose and are not redundant: 18.438 → 11.316 (mix) → 9.825 (tail) →
7.964 (both) → 7.171 (stronger tail).

**Then g6 stops at 6.8–7.2.** Four combinations spanning `path_mix` 0.7–1.0 and
`size_spread` 0.8–1.2 land within 5% of each other, at 4x real's 1.696. Pushing
either harder does not help — full path with tail (7.143) is no better than
mix 0.7 with a stronger tail (7.171).

## The floor is not direction-pool reuse

`log2_pool` had been 13 in every arm of `R34`–`R42`: 8,192 shared directions for
~26,000 articles drawing 22 each, about 70 articles per direction. Articles
sharing several directions sit close regardless of their centres, which was a
plausible hubness source independent of both mechanisms.

| log2_pool | directions | articles/direction | fil_scale | g6 |
|---|---|---|---|---|
| 13 | 8,192 | ~70 | 1.00 | 7.171 |
| 15 | 32,768 | ~18 | 1.00 | 7.818 |
| 16 | 65,536 | ~9 | 1.00 | 7.407 |
| 13 | 8,192 | ~70 | 0.85 | 5.126 |
| 16 | 65,536 | ~9 | 0.85 | 5.447 |

**Refuted.** An eightfold increase in pool size changes g6 by less than 4%, and
in the wrong direction at both `fil_scale` values. This was flagged as having the
same status as `R37`'s conjecture about g5; like that one, it is wrong.

## The frontier is monotone — there is no interior optimum

Scanning `fil_scale` at the best mixture (`path_mix` 0.7, `size_spread` 1.2):

| fil_scale | g5 | eff_rank | g1 * | g6 * | b=100 ratio |
|---|---|---|---|---|---|
| **real** | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** |
| 0.70 | 1.963 | 106.1 | 14.90 | **1.790** | 6.788 |
| 0.85 | 1.848 | 125.8 | 16.14 | 5.126 | 6.047 |
| 1.00 | 1.684 | 157.2 | 16.17 | 7.171 | 6.546 |

g5 and `eff_rank` improve monotonically as g6 degrades, with no turning point
between the endpoints. The midpoint is not a compromise worth taking: at 0.85,
g6 is already 3x out while g5 and rank are still 1.35x and 0.69x.

The b=100 ratio sits at 6.0–6.8 across the whole scan against real's 4.050, and
nothing in `R42` or `R43` moved it.

## Status of the family

Every mandatory gate is individually reachable and no configuration holds all
three:

* g1 is available almost everywhere (16.1–17.9 against 17.23),
* g6 is reachable only at `fil_scale` ≈ 0.70,
* g5 and `eff_rank` need `fil_scale` ≈ 1.00,
* and the two requirements are joined by a monotone trade with no interior
  optimum.

The best single position remains `path_mix` 0.7, `size_spread` 1.2,
`fil_scale` 1.00: g1 0.94x, `eff_rank` 0.86x, g5 1.23x, g6 4.23x, ramp 1.62x.

## What is established

* The two hubness mechanisms compose, and together take g6 from 18.4 to 7.2.
* That is a floor: four different combinations reach it and none passes it.
* The floor is not caused by direction-pool sharing.
* The `fil_scale` trade is monotone, so the family cannot be tuned into
  satisfying g5, `eff_rank` and g6 simultaneously.

## What is not

* What does set the floor. Two hypotheses are now refuted (rank in `R38`, pool
  reuse here), and no third has been measured.
* Whether the super-cluster level contributes — `per_super` has been 110
  throughout `R36`–`R43`, anchored by measurement but never varied against g6.
* §3b spans and s(k) curves for any arm in `R42`–`R43`.
