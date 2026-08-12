# Distributing the scales does not smooth s(k) — the arrangement is the wrong shape

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-11. Driver `harness/rc1/smooth_probe.py`; record
`results/smooth.json`. Follows `R46`.

## The hypothesis

`R46` found the s(k) curve oscillates — dips at k = 14 and k = 100, overshoot at
500, rms 11.32 — and attributed it to three *discrete* scales in the
construction (article 23, super-cluster 110, five path levels) where real has a
continuum.

The dips are informative: s falls where radius grows faster than count, which is
a **gap** in the distance distribution. Well-separated clusters produce exactly
that. So the proposed fix was to smear the scales:

* `scale_spread` — a per-article lognormal multiplier on `fil_scale`, so
  articles have distributed *extents* rather than all sitting in one shell,
* `sup_spread` — lognormal super-cluster occupancy instead of uniform 110,
* `nlev` — more path levels inside the article, 5 → 8.

## All three make it worse

At `w_loc` 0.6, `fil_scale` 1.0, `fil_dim` 64, `d_glob` 57:

| scale_spread | sup_spread | nlev | g5 | eff_rank | g1 | g6 | ratio | **rms** |
|---|---|---|---|---|---|---|---|---|
| — (`R46` baseline) | — | 5 | 1.674 | 186.1 | 19.41 | 1.802 | 3.879 | **11.32** |
| 0.5 | 0 | 5 | 1.761 | 177.3 | 13.33 | 1.986 | 4.974 | 13.79 |
| 1.0 | 0 | 5 | 2.130 | 146.3 | 13.49 | 1.914 | 7.584 | 15.07 |
| 0.5 | 0.8 | 5 | 1.752 | 151.9 | 13.46 | 2.015 | 3.593 | 15.27 |
| 0.5 | 0 | 8 | 1.809 | 167.3 | 14.09 | 1.779 | 5.269 | 14.33 |

**Every arm is worse than baseline, and `scale_spread` is monotonically worse**
(13.79 → 15.07). The k = 100 dip deepens rather than filling: 13.07 at baseline,
4.1 at `scale_spread` 0.5, 3.3 at 1.0.

The reason is visible in hindsight. Distributing article *extents* does not
average the shell away — it produces some very tight articles and some very
diffuse ones, and the tight ones cut *deeper* local minima. Variance in extent
adds structure rather than removing it.

One thing did improve: `s(4)` moved to 8.6 against real's 8.82, from 12.72. The
smallest scale is fixable this way; the middle of the curve is not.

## Where the smooth rise must come from

`R34` established that only ~23 of a row's neighbours are index-local, and that
the count saturates there. Yet real's `s(k)` keeps rising smoothly from k = 4 to
k = 500 — well past the article — reaching 35.73.

So **the cross-article structure itself has a rising dimension profile**. The
smooth rise is a property of the arrangement, not of the article, and no amount
of smearing the article can produce it.

The arrangement here has exactly **two** levels: a super-cluster centre and a
per-article offset. Two levels give a rise and then a plateau, which is what the
overshoot at k = 500 and the collapse at k = 100 actually are. `nlev` in this
round varied the *path* levels inside the article — the wrong hierarchy
entirely.

## What is established

* Distributing article extents, super-cluster occupancy, or path-level count
  does not smooth s(k); all three make it worse.
* `scale_spread` is monotonically harmful and should not be revisited.
* `s(4)` alone is reachable by `scale_spread` (8.6 against 8.82), decoupled from
  the rest of the curve.
* The oscillation is a property of the **arrangement's two-level structure**, not
  of the article's discreteness.

## What is not

* Whether a genuinely multi-level arrangement — three or four nested clustering
  scales in the centre cloud, rather than one super-cluster level — produces the
  smooth rise. This is the indicated next test and has never been run;
  `R35` built a two-level centre cloud and measured only its endpoints, never
  the intermediate shape.
* Whether such a construction can keep the gates that the two-level version
  reaches.
