# The ramp moves too, and the whole profile lands within 25%

**Exploratory, not a registered round. PARTIAL — see the run note.** No admission
claim, seal untouched. Measured 2026-08-10. Driver
`harness/rc1/fildim_probe.py`; records `results/fildim.json`, `dglob.json`.
Follows `R44`.

## Applying the pattern deliberately

Three times in this arc a "nothing moves X" conclusion turned out to describe
the sweep rather than the family — g5 (`R38`→`R40`), rank-versus-ramp
(`R38`→`R39`), hubness (`R43`→`R44`). `R44` closed by naming the ramp as
"unmoved by any mechanism in `R40`–`R44`" and asking which parameter had been
held fixed while that conclusion formed. `d_glob` (90), `d_loc` (64) and
`fil_dim` (22) had all been constant since `R36`.

The ramp is `s(500)/s(4)` and ours was too **high**, so `s(4)` — the
within-article local dimension — was too low. `fil_dim` sets exactly that, and
`R34` had already measured that the within-article manifold reads about half its
requested `fil_dim`.

## fil_dim moves the ramp

At `w_loc` 0.6, `fil_scale` 1.00, `path_mix` 0.7, `size_spread` 1.2:

| fil_dim | g5 | eff_rank | g1 * | g6 * | s(4) | s(500) | ratio |
|---|---|---|---|---|---|---|---|
| **real** | **1.369** | **182.3** | **17.23** | **1.696** | **8.82** | **35.73** | **4.050** |
| 22 | 1.757 | 177.5 | 16.06 | 2.189 | — | — | 6.970 |
| 40 | 1.701 | 180.2 | 19.26 | 1.946 | 10.71 | 59.92 | 5.596 |
| **64** | 1.670 | **181.0** | 19.05 | 1.869 | 12.24 | 61.08 | **4.990** |

`s(4)` rises from roughly 5 to 12.24 against real's 8.82, and the ramp falls
6.970 → 4.990. **Fourth instance of the pattern.**

`d_loc` is not a lever: 64 → 100 changed the ramp by 0.008 (5.596 → 5.604).

## The best position measured in the project

`w_loc` 0.6, `fil_scale` 1.00, `fil_dim` 64, `d_glob` 90, `path_mix` 0.7,
`size_spread` 1.2:

| quantity | value | real | ratio |
|---|---|---|---|
| g1 * | 19.05 | 17.23 | 1.11 |
| g5 * | 1.670 | 1.369 | 1.22 |
| g6 * | 1.869 | 1.696 | 1.10 |
| eff_rank | 181.0 | 182.3 | **0.99** |
| b=100 ratio | 4.990 | 4.050 | 1.23 |

**All five within 25%, with all three mandatory gates inside 22%.** For
comparison, at the start of this arc (`R40`) g5 was 1.94x and g6 was 12x, and
before `R34` the ramp did not exist at all.

A second arm reaches g5 1.358 and g6 1.663 — both essentially exact — at
`w_loc` 0.8, `fil_scale` 1.80, `fil_dim` 40, but pays `eff_rank` 446.1 (2.4x)
and ramp 7.483.

## d_glob brackets the ramp

`s(500)` was 61.08 against real's 35.73. `d_glob` sets the cross-article
dimension and had also been fixed since `R36`:

| d_glob | g5 | eff_rank | g1 * | g6 * | s(4) | s(500) | ratio |
|---|---|---|---|---|---|---|---|
| **real** | **1.369** | **182.3** | **17.23** | **1.696** | **8.82** | **35.73** | **4.050** |
| 45 | 1.672 | 129.1 | 18.78 | 1.835 | 12.15 | **45.11** | **3.714** |
| 90 | 1.670 | 181.0 | 19.05 | 1.869 | 12.24 | 61.08 | 4.990 |

The ramp now **brackets** real: 3.714 below, 4.990 above. Interpolating,
`d_glob` ≈ 57 gives ratio ≈ 4.05 — but `eff_rank` there is ≈ 143 (0.78x), so a
mild ramp-versus-rank trade remains through this parameter.

## Search budget, disclosed

`GENERATOR_SEARCH.md` §5.3. **Approximately fifty arms across `R40`–`R45`.** That
is a substantial multiple-comparisons load and the results should be read
accordingly. Two mitigations, neither complete: the structural constants
(article 23, `per_super` 110) are measured rather than tuned, and each round
tested a *named mechanism* with a stated prediction rather than scanning blindly
— `fil_dim` was predicted to raise `s(4)` before it was run, and did.

## Run note — partial

Four `d_glob` arms were planned; **one completed.** Atlas CPU Package 0 reached
82 °C, the high threshold, with load 7.9 including two long-running processes
belonging to another user. The probe was shed by script name per the thermal
rule; temperatures returned to 73 °C. `d_glob` 60 and 30, and the `d_glob` 60 /
`fil_dim` 40 arm, are unmeasured — `d_glob` ≈ 57 is an interpolation, not a
measurement.

## What is established

* The ramp responds to `fil_dim` through `s(4)`, as predicted.
* `d_loc` does not affect it.
* `d_glob` moves `s(500)` and brackets real's ramp between `d_glob` 45 and 90.
* A configuration exists with all five headline quantities within 25% and all
  three mandatory gates within 22%.

## What is not

* The interpolated `d_glob` ≈ 57 point has not been built or measured.
* `s(4)` is 12.24 against 8.82 and `s(500)` is 61.08 against 35.73 — the ramp is
  close because both are high, not because either is right. Whether that matters
  depends on whether the registered criterion is the ratio or the curve, and
  `PROFILE.md` §1 registers the ratio.
* §3b spans and the full s(k) curve have not been measured at this operating
  point; only the b=100 ratio and the eight gates.
* Bit-exactness and random access remain untouched since `R32`.
