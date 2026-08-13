# P(d | gap): articles are segmented, not smoothly graded

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12. Driver `harness/rc1/gapdist_probe.py`; record
`results/gapdist.json`. Follows `R52`.

## The question

`R52` established that the k = 14 dip is filled by the *breadth* of the
within-article distance distribution (p10-p90 spanning 1.72x), not by early
cross-article mass. That leaves three candidate mechanisms, distinguishable by
one measurement rather than three constructions:

* median rises with index gap → **topic drift** along the article (a path);
* median flat, large spread at each gap → **heteroscedastic passage radii**;
* both → a correlated radial process *plus* a path.

`P(d | |i-j| = g)` decides it. 300,000 pairs per gap, `d = sqrt(2 - 2cos)`.

## Both, with heteroscedasticity dominant

| gap | p10 | median | p90 | p90/p10 | mean cos |
|---|---|---|---|---|---|
| 1 | 0.6617 | 0.8513 | 1.2223 | **1.847** | 0.5994 |
| 2 | 0.7100 | 0.9093 | 1.2606 | 1.775 | 0.5317 |
| 4 | 0.7648 | 0.9999 | 1.2784 | 1.671 | 0.4511 |
| 8 | 0.8276 | 1.1999 | 1.2885 | 1.557 | 0.3697 |
| 12 | 0.8710 | 1.2196 | 1.2925 | 1.484 | 0.3296 |
| 16 | 0.9081 | 1.2270 | 1.2945 | 1.426 | 0.3067 |
| 23 | 0.9699 | 1.2330 | 1.2967 | 1.337 | 0.2842 |
| 64 | 1.1496 | 1.2402 | 1.2992 | 1.130 | 0.2505 |
| 128 | 1.1651 | 1.2430 | 1.3007 | 1.116 | 0.2389 |

The median **rises** 0.8513 → 1.2330 across gaps 1→23, a factor of 1.448, so
drift is real. But the spread **at a single gap** is 1.847 at gap 1 — *larger*
than `R52`'s marginal same-article spread of 1.72. Heteroscedasticity is
therefore not an artifact of pooling gaps; it is present at fixed gap and it
dominates.

## The shape rules out a lognormal radial field

**p90 barely moves — 1.2223 → 1.2967 across gaps 1 to 23, only 6% — while p10
moves 47%** (0.6617 → 0.9699). The upper tail is pinned near the global
random-pair scale (~1.24-1.30) at every gap.

A lognormal radial field would shift both tails together. This does not. It is a
**mixture with a gap-dependent weight**: at every gap, some pairs sit at the
global distance as if unrelated, and the fraction that are close decays with
gap. At gap 1, at least 10% of *adjacent* passages are already at global
distance.

Normalising by the global scale:

| gap | 1 | 2 | 4 | 8 | 12 | 23 | 64 |
|---|---|---|---|---|---|---|---|
| median / global | 0.654 | 0.699 | 0.769 | **0.922** | 0.938 | 0.948 | 0.953 |
| p10 / global | 0.509 | 0.546 | 0.588 | 0.636 | 0.670 | 0.746 | **0.884** |

By gap 8 the median pair is 92% of the way to unrelated, so the coherent
fraction falls below half by gap ~6-8. Yet p10 is still 0.88 of global at gap
64, so a minority of pairs remain coherent far out.

That is a **heavy-tailed segment-length distribution**: most coherent runs are
short (fewer than ~8 passages), a few extend much further.

## What this implies for the construction

Every family from `R36` to `R51` modelled an article as one object with a
characteristic extent — a shell, optionally with a path or graded weights
inside. The measurement says an article is instead a **sequence of coherent
segments** with heavy-tailed lengths, where within-segment distance is small and
between-segment distance is essentially global, even inside the same article.

This is orthogonal to everything tried. `R47` varied extent between articles;
`R49` added arrangement levels; `R50` added a contiguous section level above the
article; `R51` varied dimension by level. None of them introduces a
*within-article mixture* in which adjacent rows can be either very close or
entirely unrelated.

It also reframes the `R51` conflict. `G1` (from `r2/r1`) and `s(4)` disagreed,
and `R51` tried to reconcile them by lowering the finest-scale dimension, which
collapsed `G1` to 4.5. A segment mixture makes the local distance distribution
bimodal and nonstationary, which is exactly the regime where those two
estimators stop measuring the same thing. It predicts that `fil_dim` can stay
high — protecting `G1` — while a low `s(4)` comes from the mixing weight rather
than from low dimension. That prediction is untested.

## What is established

* Both drift and heteroscedasticity are present; heteroscedasticity is larger
  (1.847 at fixed gap 1 against a 1.72 marginal).
* The upper tail of `P(d | gap)` is pinned at the global scale, so the mechanism
  is a mixture rather than a continuous radial field.
* The coherent fraction falls below half by gap ~6-8 and has a tail reaching
  past gap 64.

## What is not

* Nothing has been built. The segment model is indicated by the measurement, not
  demonstrated.
* Segment boundaries are inferred from distance statistics, not read from
  article or section metadata, which this corpus does not carry (`R34`).
* Whether a segment mixture reproduces `s(14)` — the point of the exercise — and
  whether it does so while leaving `s(53)`, `g5` and `g6` alone.
