# What real has between k=4 and k=20: a within-article spread of 1.7x

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12. Driver `harness/rc1/dipanatomy_probe.py`; record
`results/dipanatomy.json`. Follows `R51`.

## Why measure instead of building

Four mechanisms failed to fill the k = 14 dip and three made it worse
(`R47`, `R49`, `R50`, `R51`). Rather than design a fifth, this measures what
real's neighbourhood actually contains there — the approach that settled the ~23
constant in `R34`.

## The neighbourhood, resolved by k

Real at b = 100 (whole articles present), 600k pool. "Article" is index gap ≤ 23.

| k | r(k) | r(k)/r(4) | frac same-article | frac gap ≤ 128 | median gap |
|---|---|---|---|---|---|
| 1 | 0.7451 | 0.846 | 0.859 | 0.902 | 3 |
| 4 | 0.8809 | 1.000 | 0.731 | 0.778 | 5 |
| 8 | 0.9497 | 1.078 | 0.595 | 0.647 | 10 |
| 11 | 0.9735 | 1.105 | 0.521 | 0.574 | 18 |
| **14** | 0.9895 | 1.123 | **0.463** | 0.518 | 45 |
| **20** | 1.0097 | 1.146 | 0.377 | 0.433 | **29,790** |
| 100 | 1.0733 | 1.219 | 0.100 | 0.134 | 135,394 |
| 500 | 1.1249 | 1.277 | 0.021 | 0.031 | 162,403 |

The median index gap jumps from 45 at k = 14 to 29,790 at k = 20 — the
article-to-global transition, consistent with `R34`. At k = 14 **46% of
neighbours are still same-article**, and the radius has grown only 12% from
k = 4.

## The finding: the within-article distribution is very wide

| population | p10 | median | p90 | n |
|---|---|---|---|---|
| same-article (gap ≤ 23) | **0.6030** | 0.8836 | **1.0346** | 107,134 |
| cross-article | 1.0277 | 1.0991 | 1.1418 | 4,892,866 |

**Same-article distances span a factor of 1.72**; cross-article distances are
packed into a band of 1.11. Only **11.4%** of cross-article neighbours fall
inside the same-article range, so the two populations barely overlap.

This is what fills k = 4…20. Not cross-article mass arriving early — the
overlap is small — but the sheer **breadth of the within-article distribution**.
Walking k from 4 to 14 walks up a wide spread of same-article distances rather
than reaching the edge of a shell.

Every construction in `R36`-`R51` gives an article a *characteristic extent*:
its members sit at similar distances, forming a narrow shell whose edge is the
dip. The measured requirement is the opposite — within one article, passages
must sit at distances spanning nearly 2x.

## This explains R47

`R47` introduced `scale_spread`, a per-article lognormal multiplier on the
extent, and it made the dip **worse**, monotonically. The reason is now clear:
it varied extent *between* articles while leaving each article internally a
shell. That produces some tight shells and some loose ones — deeper minima, as
measured — where what is needed is variance *within* a single article.

The distinction was invisible without this measurement, and `R47`'s negative
result was correct but misattributed: it was recorded as "distributing the
scales does not smooth s(k)", when the accurate statement is "distributing
extents between articles does not, and the within-article spread was never
varied".

## What is established

* At k = 14 real's neighbourhood is still 46% same-article, at a radius only 12%
  above r(4).
* Real's same-article distances span 0.603-1.035 (p10-p90), a factor of 1.72;
  cross-article span 1.028-1.142.
* The two populations overlap by only 11.4%, so the dip region is filled by
  within-article breadth, not by early cross-article mass.
* `R47`'s mechanism varied the wrong quantity, and its conclusion should be read
  narrowly.

## What is not

* Nothing has been built against this. The measured target — a within-article
  distance distribution spanning ~1.7x — has not been implemented or tested.
* The generator's own within-article distance distribution has not been measured
  for comparison, so the size of the gap is inferred from the shell behaviour
  rather than quantified.
* Why real's within-article distances are so broad. Passage length, section
  boundaries and topic drift within an article are all plausible and none is
  measured; the corpus carries no article metadata here (`R34`).
