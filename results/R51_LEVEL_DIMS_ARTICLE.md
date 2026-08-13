# The finest scale is fixable; the k=14 dip is not, by any of four mechanisms

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12. Driver `harness/rc1/levdims_probe.py`; record
`results/levdims.json`. Follows `R50`.

## A diagnosis that was half right

Real's within-article profile *rises*: `s(4)` 8.82 → `s(14)` 16.08. Mine
*fell*: 11.5 → 8.2. **Real's finest scale is its lowest-dimensional; mine was its
highest** — because 45% of the within-article variance was an i.i.d. ball across
the whole `fil_dim` = 64 subspace, which dominates at k = 4 and gives high local
dimension, while the path (varying in few levels at small gaps) took over by
k = 14 and gave lower.

The fix follows directly: per-level dimensions *rising* with level, and no ball.

| lev_dims | g5 | eff_rank | g1 | g6 | ratio | rms | **s(4)** | **s(14)** | s(53) | s(500) |
|---|---|---|---|---|---|---|---|---|---|---|
| **real** | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** | — | **8.8** | **16.1** | **28.9** | **35.7** |
| uniform 64 + ball (`R49`) | 1.675 | 198.6 | 13.10 | 1.671 | 4.608 | **10.84** | 11.5 | 8.2 | 22.8 | 53.0 |
| [6, 10, 16, 26, 40] | 1.744 | 196.7 | 4.86 | 1.568 | 6.804 | 10.96 | **7.7** | 6.1 | 22.9 | 52.2 |
| [4, 8, 16, 32, 64] | 1.779 | 194.8 | 4.47 | 1.590 | 7.356 | 11.04 | **7.2** | 5.3 | 22.4 | 52.9 |

**The diagnosis was right about `s(4)`**: it moves 11.5 → 7.7 against real's 8.8,
and the direction of the finest-scale dimension is now correct.

**It was wrong about the dip.** `s(14)` goes 8.2 → 6.1 → 5.3 — deeper, not
filled — and the overall rms is unchanged (10.84 → 10.96 → 11.04).

## And it costs g1

`g1` collapses from 13.10 to 4.86 and 4.47, against real's 17.23. A path whose
fastest level has 4-6 dimensions has too little dimension at k = 1,2, which is
exactly what TwoNN reads. So within-article structure now faces a direct
tension: `s(4)` wants a low-dimensional finest level, `g1` wants a high one, and
they are the same scale measured two ways.

That tension is new information. `R44`-`R46` had `g1` comfortably in range at
0.93-1.13x throughout; it was never in conflict with anything until the finest
level was made genuinely low-dimensional.

## The dip, after four mechanisms

| mechanism | round | effect on s(14) |
|---|---|---|
| distributed article extents | `R47` | 8.2 → 7.9 (worse) |
| nested arrangement levels | `R49` | unchanged at 8.1-8.3 |
| index-contiguous sections | `R50` | 8.2 → 7.7 (worse) |
| rising per-level dimensions | here | 8.2 → 5.3 (worse) |

Every mechanism that adds or restructures correlated mass near the article makes
it worse. Real reaches 16.1 there. Nothing tried approaches it.

The consistent direction across four unrelated interventions is itself the
finding: this is not a parameter that has not been found, it is a shape the
construction does not produce. Whatever real has between k = 4 and k = 20
supplies neighbours at *intermediate* radius without tightening the innermost
shell, and every mechanism here trades one against the other.

## What is established

* Real's finest within-article scale is its lowest-dimensional, and a rising
  per-level dimension schedule reproduces `s(4)` (7.7 against 8.8).
* Doing so collapses `g1` to 4.5-4.9 against 17.23 — `s(4)` and `g1` are in
  direct tension at the finest scale.
* The k = 14 dip has resisted four distinct mechanisms and worsened under three.

## What is not

* Any mechanism that fills the dip.
* Whether `s(4)` and `g1` can be satisfied together. The two arms here move them
  in opposite directions and no intermediate was measured.
* §3b spans for any arm in `R49`-`R51`.
