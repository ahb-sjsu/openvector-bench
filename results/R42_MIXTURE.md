# The mandatory gates split cleanly by scale, and no setting holds all three

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/mix_probe.py`; records
`results/mix.json`, `mix2.json`. Follows `R41`.

## What was being tested

`R41` left g1 and g6 trading through the ball-versus-path choice: the i.i.d.
ball matched g1 (17.8 against 17.23) and blew hubness up, the path matched g6
(1.637 against 1.696) and pinned g1 near 10. Both are mandatory and only the
extremes had been measured.

Two mechanisms were added. `path_mix` interpolates the within-article
displacement, `u = sqrt(1-mix)*u_ball + sqrt(mix)*u_path`, preserving the
variance and changing only the correlation structure. `size_spread` draws
lognormal article lengths — skewed group sizes are the standard hubness
mechanism, and were 0 in every arm of `R34`–`R41`.

## Result

| mix | fil_scale | spread | g5 | eff_rank | g1 * | g6 * | b=100 ratio |
|---|---|---|---|---|---|---|---|
| **real** | | | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** |
| 0.0 ball | 0.70 | 0 | 1.891 | 106.4 | 17.65 | 3.993 | 6.115 |
| 0.4 | 0.70 | 0 | 1.932 | 106.2 | **17.01** | 2.518 | 6.297 |
| 0.7 | 0.70 | 0 | 1.963 | 106.1 | 14.90 | **1.790** | 6.788 |
| 1.0 path | 0.70 | 0 | 1.993 | 106.3 | 10.16 | **1.637** | 7.889 |
| 0.4 | 0.70 | 0.8 | 1.995 | 103.9 | **17.55** | 3.634 | 6.222 |
| 0.0 ball | 1.00 | 0 | 1.551 | 166.4 | 17.86 | 18.438 | 6.173 |
| 0.4 | 1.00 | 0 | 1.572 | 165.9 | **17.12** | 16.495 | 7.064 |
| 0.7 | 1.00 | 0 | 1.590 | 165.6 | 14.90 | 11.316 | 8.066 |
| 0.4 | 1.00 | 0.8 | 1.616 | 162.3 | **17.73** | 9.825 | 6.753 |

## The mixture works, and only at low spread

At `fil_scale` 0.70 the interpolation behaves better than either extreme
suggests. mix 0.4 holds g1 at 17.01 — as good as the pure ball — while cutting
g6 from 3.993 to 2.518. mix 0.7 reaches **g6 1.790 against real's 1.696**, a
5.5% match, at g1 14.90. A linear reading of `R41`'s extremes would have put g1
near 14.6 at mix 0.4; it is 17.01, so g1 is cheaper to keep than the extremes
implied.

**But the mixture does not transfer to `fil_scale` 1.00**, which is the setting
that matters: it cuts g6 by 37% at 0.70 and only 11% at 1.00 (18.438 → 16.495).
Whatever drives hubness at large spread is not the ball-versus-path structure.

## Heavy-tailed sizes help where the mixture does not

`size_spread` 0.8 cuts g6 by **40% at `fil_scale` 1.00** (16.495 → 9.825) while
*worsening* it at 0.70 (2.518 → 3.634). The mechanism is real and its sign
depends on the regime — at low spread, articles are tight and unequal sizes
create hubs; at high spread they are diffuse and unequal sizes break up the
uniform overlap that was creating them.

It also lifts g1 slightly (17.12 → 17.73 at `fil_scale` 1.00). But 9.825 against
1.696 is still 5.8x, so it does not close the gate.

## The state: gates split cleanly by scale

| `fil_scale` | g1 | g5 | g6 | eff_rank |
|---|---|---|---|---|
| 0.70 | ✓ 17.01 (mix 0.4) | ✗ 1.93 | ✓ 1.79 (mix 0.7) | ✗ 106 |
| 1.00 | ✓ 17.12 | ~ 1.57 | ✗ 9.83 (best) | ✓ 163 |

`fil_scale` 0.70 gives the two neighbourhood gates and misses the two scale
quantities; 1.00 gives the two scale quantities and misses hubness by 5.8x. g1
is available at both. **No configuration measured holds all three mandatory
gates.**

The ramp is 6.2–8.1 across every arm here against real's 4.050, and neither
mechanism improved it — `R36`'s 3.900 remains the best and comes from a build
that fails `dims90` and g5.

## What is established

* g1 and g6 are partly separable, and the ball-path mixture is the knob.
* g6 is reachable (1.790 against 1.696) but only at `fil_scale` 0.70.
* Skewed article sizes are a genuine hubness mechanism whose sign flips with
  `fil_scale`, and they help by 40% exactly where the mixture fails.
* The obstruction is now sharply located: **hubness at the spread required by
  g5 and eff_rank.**

## What is not

* Whether combining higher `size_spread` (>0.8) with mix 0.7 at `fil_scale` 1.00
  closes g6. The two mechanisms were not composed at their respective best
  settings — the arm (mix 0.7, `fil_scale` 1.00, spread 0.8) was not run.
* §3b spans and s(k) curves for any arm in this round; only the b=100 ratio was
  carried through.
* Whether the ramp is recoverable at all in this family, given that ten
  configurations now sit between 6.1 and 11.5.

## Run note

The first attempt ran three of ten arms before Atlas CPU Package 0 reached
85 °C with concurrent load from another process (load average 8.5); the probe
was shed by script name per the thermal rule. It was resumed at 4 threads
instead of 6 once the box quietened, peaking at 80 °C and settling at 72–77 °C.
No other workload was affected in either instance.
