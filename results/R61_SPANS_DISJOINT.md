# Each §3b span is reachable; the two are never reachable together

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12 on NRP A10s. Driver `harness/rc1/gate_check.py`; record
`results/r61.json`. Follows `R60`.

## Why this round exists

`R60` found that `rms` — a convenience statistic introduced in `R58` — points
**opposite** to the registered §3b criterion: the best-rms configuration had both
spans furthest out, while a configuration discarded for poor rms had the ratio
span nearest its band. Rounds `R58`-`R60` were therefore optimising the wrong
objective. This re-tunes against §3b directly.

`PROFILE.md` §3b requires **both** spans in band:
`ratio span` +2.397 ± 0.085 → [+2.227, +2.567], and
`log G1 span` −0.494 ± 0.054 → [−0.602, −0.386].

## The ratio span comes into band, with g6 essentially exact

Break rate at `w_loc` 0.6, branch 64, `d_glob` 30:

| brk | ratio span | | log G1 span | g1 | g5 | **g6** | rms |
|---|---|---|---|---|---|---|---|
| **band / real** | **[+2.227, +2.567]** | | **[−0.602, −0.386]** | **17.23** | **1.369** | **1.696** | — |
| 0.020 | **+2.298** | IN | −0.856 | 4.41 | 1.607 | 1.639 | 7.69 |
| **0.030** | **+2.420** | **IN** | −0.889 | 4.44 | 1.596 | **1.681** | 7.63 |
| 0.040 | +2.653 | | −0.923 | 4.49 | 1.587 | 1.721 | 7.56 |
| 0.050 | +2.697 | | −0.953 | 4.55 | 1.573 | 1.740 | 7.39 |

At brk 0.030 the ratio span is **+2.420 against a target of +2.397 — inside 1%** —
with **g6 1.681 against 1.696, also inside 1%**. `R46` reached the ratio span in
band with a demonstrably wrong curve; this reaches it with the hubness gate
simultaneously matched.

## The log G1 span needs a different w_loc, and they do not overlap

`w_loc` moves both spans monotonically upward:

| w_loc | ratio span | log G1 span | g5 | rms |
|---|---|---|---|---|
| 0.35 | +1.918 | −1.097 | 1.508 | 6.89 |
| **0.60** | **+2.420** IN | −0.889 | 1.596 | 7.63 |
| 0.90 | +3.338 | −0.659 | 1.752 | 9.94 |
| **1.30** | +4.908 | **−0.417** IN | 2.022 | 17.63 |

The in-band windows are **disjoint in `w_loc`**: the ratio span holds for roughly
[0.55, 0.65] and the log G1 span for roughly [1.05, 1.35].

## Two candidate bridges, both refuted

`brk` and `w_loc` act differentially on paper — `w_loc` raises both spans, `brk`
raises the ratio while lowering log G1 — so low `brk` at high `w_loc` should have
pulled the ratio back into band:

| brk | w_loc | ratio span | log G1 span |
|---|---|---|---|
| 0.000 | 1.15 | +3.921 | −0.443 IN |
| 0.005 | 1.15 | +3.987 | −0.454 IN |
| 0.000 | 1.30 | +4.546 | −0.369 |
| 0.010 | 1.30 | +4.825 | −0.379 |

**Refuted.** At `w_loc` 1.15 the ratio span stays near +3.9 even with `brk` = 0,
against a target of +2.4. `w_loc` dominates.

`d_glob` was the second candidate: `R59` measured it moving the ratio span
strongly (+1.192 → +0.708 from 30 → 45) while log G1 barely moved. At `w_loc`
1.15, `brk` 0.005:

| d_glob | ratio span | log G1 span |
|---|---|---|
| 45 | +3.725 | −0.448 IN |
| 65 | +4.187 | −0.446 IN |
| 90 | +3.799 | −0.438 IN |
| 120 | +3.611 | −0.438 IN |

**Refuted.** Across a 2.7x range the ratio span stays at +3.6 to +4.2 — the lever
that moved it at `w_loc` 0.6 does not move it here at all. Its effect is
conditional on `w_loc`, which is itself worth recording: a lever measured at one
operating point cannot be assumed to act at another.

## Conclusion

**Both §3b spans are individually reachable and never jointly reachable** in this
family, across three levers and both directions. That is the same shape of result
as `R33`'s over-constraint of the index cascade: the construction has fewer
effective degrees of freedom than the criterion requires.

`g5` also degrades badly on the log G1 side — 1.94-2.06 against 1.369 at
`w_loc` >= 1.15, where it was 1.354 at the `R58` point — so the log-G1-in-band
configurations fail a mandatory gate by ~45%.

## What is established

* Ratio span **in band** at brk 0.030 / `w_loc` 0.60 (+2.420 vs +2.397), with g6
  simultaneously within 1% (1.681 vs 1.696).
* Log G1 span **in band** at `w_loc` >= 1.15 (−0.417 to −0.454).
* The two in-band windows in `w_loc` are disjoint, and neither `brk` nor `d_glob`
  bridges them.
* `d_glob`'s effect on the ratio span is conditional on `w_loc` — strong at 0.6,
  absent at 1.15.

## What is not

* Any configuration satisfying §3b. It requires both spans and none has both.
* `g1`, still ~4.3-4.6 against 17.23 everywhere in this round, consistent with
  `R60`'s invariance.
* Whether a lever outside {brk, w_loc, d_glob, branch, fil_dim} separates the
  spans. `size_spread`, `log2_pool`, `nlev` and the path weight decay are untried
  against §3b specifically.
