# The arrangement tunes: s(k) rms falls from ~10.4 to 5.30

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12 on NRP A10s. Driver `harness/rc1/branch_sweep.py`; record
`results/r58.json`. Follows `R57`.

## What was blocking

`R57` left segmentation working — `s(14)` robustly 15.0-16.0 against real's
16.08 — with the **outer curve** untouched: `s(53)` 22.5-23.2 against 28.88 and
`s(500)` ~53 against 35.73. That is an arrangement property, and `R49` had
already shown `branch` moves it more than level count.

The NRP profile from `R57` makes a four-arm sweep cost ~60 s, so this is three
sweeps rather than one.

## Branch has an optimum at 64

At `d_glob` 57, break rate 0.143:

| branch | ratio | rms | s(4) | s(14) | s(53) | s(500) |
|---|---|---|---|---|---|---|
| **real** | **4.050** | — | **8.82** | **16.08** | **28.88** | **35.73** |
| 16 | 5.831 | 9.48 | 8.8 | 14.9 | 23.2 | 51.2 |
| 32 | 5.526 | 7.57 | 8.3 | 17.1 | 23.4 | 46.0 |
| **64** | 4.584 | **7.42** | 9.7 | 16.8 | 26.1 | 44.5 |
| 128 | 5.554 | 8.10 | 8.5 | 16.0 | 24.4 | 47.0 |
| 256 | 5.997 | 11.50 | 9.0 | 19.3 | 23.7 | 53.9 |
| 512 | 6.014 | 14.60 | 10.0 | 19.2 | 22.7 | 60.1 |
| 1024 | 6.014 | 14.60 | 10.0 | 19.2 | 22.7 | 60.1 |

512 and 1024 are **identical**, which is the tell: with `n_art` ~26,000 and three
levels, `27 * branch^2` exceeds the article count at branch >= 512, so the outer
level collapses to a single cluster and further widening is a no-op. At branch 64
the arrangement is effectively two levels — 27 articles and 1,728 — plus global.

## d_glob then halves the error again

At branch 64:

| d_glob | ratio | **rms** | g6 | s(4) | s(14) | s(53) | s(500) | overlap |
|---|---|---|---|---|---|---|---|---|
| **real** | **4.050** | — | **1.696** | **8.82** | **16.08** | **28.88** | **35.73** | **0.114** |
| **30** | 5.091 | **5.30** | 1.296 | **8.2** | **16.3** | 23.7 | 41.9 | 0.0096 |
| 38 | 5.325 | 5.71 | 1.281 | 7.9 | 16.0 | 22.7 | 42.1 | 0.0087 |
| 45 | 4.831 | 6.51 | 1.280 | 8.9 | 16.9 | 25.0 | 43.0 | 0.0051 |
| 57 | 4.584 | 7.42 | 1.333 | 9.7 | 16.8 | 26.1 | 44.5 | 0.0029 |

**rms 5.30**, against ~10.4 for every round from `R49` to `R57` and 11.32 at
`R46`. Roughly half the previous best.

**`s(4)` 8.2 against 8.82 and `s(14)` 16.3 against 16.08 hold simultaneously.**
Those two have never been matched together: `R51` reached `s(4)` 7.7 but with
`s(14)` at 6.1, and `R57` reached `s(14)` 16.0 with `s(4)` at 12.7.

`overlap` also moves for the first time — 0.0029 to 0.0096 — though it remains
two orders below real's 0.114.

## What is still wrong, and it is one shape

`s(53)` is 23.7 against 28.88 and `s(500)` is 41.9 against 35.73. The curve is
**too flat through the middle and rises too steeply at the end**. Both errors are
the same defect seen from two sides, and neither `branch` nor `d_glob` fixes it:
lowering `d_glob` pulls `s(500)` down (44.5 → 41.9) but pulls `s(53)` down with
it (26.1 → 23.7), so the middle never catches up.

The ratio is 5.091 against 4.050 at the best-rms point. Note that the arm with
the *closest ratio* (branch 64, `d_glob` 57, ratio 4.584) has the *worst* rms of
the four — a direct illustration of `R57`'s withdrawal: the ratio is a quotient
of two endpoints and tracks the curve poorly.

## A third arrangement level does not help — hypothesis refuted

The two levers had been swept independently: `branch` at `d_glob` 57, then
`d_glob` at branch 64. That left an untested corner. At branch 64 only **two**
arrangement levels are populated (27 articles and 1,728; the third exceeds
`n_art`), so the natural reading of the `s(53)` deficit was that the middle of
the curve needs a third populated level — which branch 16 provides (27, 432,
6,912) and which had only ever been measured at `d_glob` 57.

Tested at `d_glob` 30:

| branch | rms | s(53) | s(500) | overlap |
|---|---|---|---|---|
| 12 | 7.12 | 24.6 | 44.7 | 0.0029 |
| 24 | 5.88 | 22.8 | 43.5 | 0.0121 |
| 32 | 5.70 | 22.8 | 43.4 | **0.0245** |
| **64** | **5.30** | 23.7 | 41.9 | 0.0096 |

**Refuted.** More populated levels make it monotonically worse (7.12 → 5.88 →
5.70 → 5.30), and `s(53)` does not improve at all — 24.6, 22.8, 22.8 against
23.7 at branch 64. The middle-of-curve deficit is not a level-count problem, so
whatever produces real's `s(53)` = 28.88 is not more arrangement hierarchy.

Incidentally `overlap` peaks at branch 32 (0.0245, the highest measured against
real's 0.114) where rms is 5.70, so `overlap` and rms trade against each other
here rather than improving together.

The branch-16 arm did not emit before its pod terminated; three of four.

## What is established

* `branch` has a genuine optimum at 64, and above ~512 the outer level degenerates
  to one cluster.
* `d_glob` 30 with branch 64 gives **rms 5.30**, roughly half the previous best.
* `s(4)` and `s(14)` are simultaneously within 7% and 1.5% of target.
* `overlap` responds to the arrangement (0.0029 → 0.0096), having been fixed at
  ~0 through every earlier mechanism.

## What is not

* `s(53)` (23.7 vs 28.88) and `s(500)` (41.9 vs 35.73) — one shape defect, not
  addressed by either lever swept here.
* `g6` 1.296 against 1.696, and `overlap` still ~12x short.
* The registered gates. `g1` was not measured with `geometry.id_twonn`, and `g5`
  not at all, in any arm of `R56`-`R58`.
* What produces real's `s(53)` = 28.88. A third populated arrangement level was
  the obvious candidate and is refuted above; no other mechanism is designed.
