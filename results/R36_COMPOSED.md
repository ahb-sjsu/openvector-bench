# Two measured scales, composed: the ramp matches, the sparse regime does not

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Drivers `harness/rc1/centre_widek.py`,
`harness/rc1/composed_probe.py`; records `results/centre_widek.json`,
`composed.json`. Follows `R35`.

## The super-cluster scale, measured rather than swept

`R35` reproduced real's cross-article profile but rested on `per_super ≈ 200`
found by sweeping, in a working region where 24 of 36 arms collapsed. That is
the failure mode of `R28` and `R30`, so it was anchored before being used.

The article scale came from a k-NN gap cliff in index space. Above the article
there is no index locality (`R35`), so the analogue must be geometric: if
article centres cluster at some scale M, the centre cloud's `s(k)` should turn
over near k = M. Measuring the profile of 26,087 article centres out to
k = 4000:

| k (articles) | 4 | 12 | 28 | 63 | **110** | 252 | 578 | 1325 | 4000 |
|---|---|---|---|---|---|---|---|---|---|
| s(k) | 31.04 | 35.16 | 37.06 | 37.64 | **38.28** | 36.74 | 36.18 | 34.70 | 32.01 |

The profile peaks at **k ≈ 110 articles** and declines thereafter. Both scales in
the construction are now measured: ~23 rows per article, ~110 articles per
super-cluster.

The swept value of 200 was the right order of magnitude, which is reassuring
about `R35` but is no longer what justifies the parameter.

## The composition, and the prediction it was tested against

Articles of 23 contiguous rows around centres drawn from a two-level
hash-assigned hierarchy at `per_super` = 110. Stated before the run: *if the
anchored centre cloud matches real's centre profile, and articles are sized to
give within-article `s(4)` ≈ 8.8, the composed corpus should give b=100 ratio
≈ 4.05 and b=1 ratio ≈ 1.28 without either being fitted.*

| | s(4) | s(500) | ratio | G1 | μ |
|---|---|---|---|---|---|
| **real b=100** | **8.82** | **35.73** | **4.050** | **15.85** | **1.0576** |
| fd30 fs0.45 | 9.35 | 36.46 | **3.900** | 19.88 | 1.0493 |
| fd22 fs0.45 | 7.89 | 36.15 | 4.580 | 16.92 | 1.0592 |
| **real b=1** | **27.40** | **35.13** | **1.282** | **26.09** | **1.0293** |
| fd30 fs0.45 | 22.16 | 37.69 | 1.701 | 18.46 | 1.0437 |
| fd22 fs0.45 | 20.49 | 36.77 | 1.794 | 18.76 | 1.0441 |

| | ratio span | log G1 span |
|---|---|---|
| **real** | **+2.397 ± 0.085** | **−0.494 ± 0.054** |
| fd30 fs0.45 | +2.823 | +0.049 |
| fd22 fs0.45 | +3.420 | −0.165 |
| fd16 fs0.45 | +3.532 | −0.338 |

**The dense regime holds.** At b=100 the ramp is 3.900 against 4.050 — within
3.7% — with `s(4)` within 6% and `s(500)` within 2%. For context, every family
before `R34` measured ratio ≈ 1.0, and `R34` itself overshot at 7.8. This is the
first time the ramp has been quantitatively matched rather than merely produced.

**The ratio span is +2.823 against +2.397 ± 0.085.** Eighteen percent high, and
5 sd outside the registered band, so it does not pass — but the sequence across
rounds is +0.12 (`R32`), +7.58 (`R34`), +2.82 here.

**The sparse regime does not hold.** At b=1 the ratio is 1.70 against 1.282 and
G1 is 18.5 against 26.09. The log G1 span still has the wrong sign at the arm
that fits everything else, and the arms that get its sign right (fd16, −0.338)
fit the ratios worse. The two spans trade against `fil_scale`.

## Why the sparse regime fails

The centre calibration did not reach its own target. The best of 18 arms gave
s(4) 28.35 against 31.04 and **G1 49.74 against 39.84** — the k < 4 residual
identified in `R35` is unchanged, and it propagates: b=1 sampling puts roughly
one row per article, so the composed corpus at b=1 *is* the centre cloud, and it
inherits the centre cloud's error.

So the remaining defect is still the one `R35` isolated, at the same scale, and
it is now shown to be load-bearing rather than cosmetic: it sets the b=1 regime,
the b=1 regime sets one end of both spans, and the spans are the registered
criterion.

## Search budget, disclosed

`GENERATOR_SEARCH.md` §5.3. **18 centre-calibration arms and 6 composed arms,
24 in total.** Two of the five structural parameters are measured constants
(article 23, per_super 110) and were not tuned; `d_loc`, `d_glob`, `w_loc`,
`fil_dim` and `fil_scale` were swept. The b=100 ratio and both spans were not
among the quantities the sweep optimised — the centre sweep targeted the centre
cloud alone, and the composition sweep was run once against fixed targets.

## Status

Not a candidate. But the position is materially different from every prior
round:

* the ramp is matched to 3.7%, from two measured scales,
* the ratio span is within 18% of a band it has never previously approached,
* the single remaining defect is localised, measured, and shown to be the cause
  of the failures downstream of it.

## What is not established

* **The k < 4 defect is unexplained.** `R35` recorded its shape; nothing since
  has identified what real does between k = 1 and k = 4 that a two-level cloud
  does not.
* Whether fixing it fixes the b=1 regime and both spans, or merely one.
* Bit-exactness and random access, untouched since `R32`. The construction is
  index-addressable in principle — article is `i // 23`, super-cluster is a hash
  of the article — but uses a numpy RNG and materialised tables.
* Nothing has been measured at rungs other than the §3b ladder, and the eight
  registered gates in `PREREG_RC1` have not been evaluated on this family at all.
