# A registered §3b statistic lands in band, on a curve that is qualitatively wrong

**Exploratory, not a registered round. PARTIAL — see the run note.** No admission
claim, seal untouched. Measured 2026-08-10. Driver
`harness/rc1/final_probe.py`; record `results/final.json`. Follows `R45`.

## The interpolation held

`R45` bracketed real's ramp between `d_glob` 45 and 90 and interpolated ≈ 57
without building it. Built:

| d_glob | g5 * | eff_rank | g1 * | g6 * | b=100 ratio | ratio span | log G1 span |
|---|---|---|---|---|---|---|---|
| **real** | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** | **+2.397 ± 0.085** | **−0.494 ± 0.054** |
| 57 | 1.674 | **186.1** | 19.41 | 1.802 | **3.879** | **+2.473** | −0.088 |
| 70 | 1.676 | 207.4 | 19.20 | 1.781 | 4.376 | **+2.372** | −0.058 |

**The `PROFILE.md` §3b ratio span lands inside the registered ±2 sd band
[+2.227, +2.567] at both `d_glob` values.** No generator in the project has
satisfied a registered §3b criterion before. `eff_rank` is 1.02x and the b=100
ratio 0.96x at `d_glob` 57 — both essentially exact — with all three mandatory
gates within 22%.

## And it does not mean what it looks like

**The second §3b statistic fails badly.** The log G1 span is −0.088 and −0.058
against a registered −0.494 ± 0.054, far outside [−0.602, −0.386]. `PROFILE.md`
§3b requires *both* spans in band, so this is not an admission-shaped result.

**More seriously, the s(k) curve is qualitatively wrong.** At `d_glob` 57,
b = 100:

| k | 4 | 8 | 14 | 28 | 53 | 100 | 263 | 500 |
|---|---|---|---|---|---|---|---|---|
| real | 8.82 | 11.46 | 16.08 | 23.40 | 28.88 | 31.29 | 34.82 | 35.73 |
| generator | 12.72 | 11.22 | **8.57** | 11.88 | 18.58 | **13.07** | 37.98 | 49.35 |
| difference | +3.90 | −0.24 | −7.51 | −11.52 | −10.30 | −18.22 | +3.16 | +13.62 |

Real rises smoothly and monotonically. The generator **oscillates** — down to
8.57 at k = 14, up to 18.58 at k = 53, down again to 13.07 at k = 100, then
overshooting to 49.35. Rms error 11.32 against a curve whose full range is 27.

That is the signature of **discrete scales**: the article (23 rows), the
super-cluster (110 articles) and the five path levels each imprint a bump, and
between them the growth dimension falls back. Real has a continuum of scales and
no such structure.

So the in-band ratio span is **endpoint coincidence**. `s(4)` and `s(500)` happen
to bracket correctly at this parameter setting while everything in between is
wrong by up to 18 units. `PROFILE.md` §1 registers the ratio, so the statistic
is legitimately in band as written — but the geometry that produces it is not
real's, and the criterion is being satisfied for the wrong reason.

This is the `R27` failure mode recurring in a subtler form: matching a scored
summary through a mechanism the target does not use. It was caught here only
because the full curve was measured, which had not been done at any operating
point since `R33`.

## What this says about the family

The construction has three hard scales. Real does not. No amount of tuning
`w_loc`, `fil_scale`, `fil_dim` or `d_glob` will smooth an oscillation whose
period is set by the number of structural levels — that requires either many
more levels or scales drawn from a distribution rather than fixed.

`R41` already introduced `size_spread` to make article sizes heavy-tailed, and
it is 1.2 in these arms; that smooths *one* of the three scales. The
super-cluster size (110) and the path level count (5) remain fixed.

## Run note — partial

Three `d_glob` arms planned, two completed. Atlas CPU Package 0 reached 83 °C
with two long-running processes belonging to another user on the box; the probe
was shed by script name per the thermal rule and temperatures returned to 70 °C.
The `d_glob` 90 arm was a control whose gates were already measured in `R45`.

## What is established

* The §3b ratio span is reachable and lands in band at two `d_glob` values.
* At `d_glob` 57: mandatory gates within 22%, `eff_rank` 1.02x, ramp 0.96x.
* The s(k) curve oscillates with a period set by the construction's discrete
  scales, and does not resemble real's at any k between 14 and 100.
* The log G1 span is not reachable at this operating point.

## What is not

* Whether smoothing the remaining fixed scales — distributed super-cluster
  sizes, more path levels — removes the oscillation. Untested.
* Whether the log G1 span and the ratio span can be satisfied together anywhere
  in this family.
* Bit-exactness and random access, untouched since `R32`.
