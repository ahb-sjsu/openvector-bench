# Within-article breadth is not sufficient: D_article passes 1.72 and s(14) never turns

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12 on an NRP A10. Driver `harness/rc1/nrp_sweep.py` with
`harness/rc1/hashgpu.py`; record `results/r55.json`. Follows `R54`.

## The pre-registered test

`R52` concluded that the k = 14 dip is filled by the **breadth** of the
within-article distance distribution (real spans 1.72x p10-p90). The
falsification condition was stated before the run: *if `D_article` reaches ~1.7
and `s(14)` still does not move, that interpretation is wrong.*

`R54` reached only 1.39 before an Atlas thermal event, so the test was
inconclusive. This completes it.

## Result: falsified

| gate | D_article | d50 same | d50 cross | overlap | **s(14)** | ratio | rms |
|---|---|---|---|---|---|---|---|
| **real** | **1.72** | **0.884** | **1.099** | **0.114** | **16.1** | **4.050** | — |
| 1.00 | 1.22 | 0.896 | 1.289 | 0.000 | 10.4 | 6.374 | 10.55 |
| 0.70 | 1.39 | 0.794 | 1.272 | 0.000 | 7.0 | 6.440 | 9.15 |
| 0.50 | 1.61 | 0.699 | 1.258 | 0.000 | 5.1 | 7.007 | 9.56 |
| 0.30 | **2.19** | 0.563 | 1.241 | 0.000 | 3.4 | 8.675 | 10.69 |
| 0.15 | degenerate | 0.397 | 1.225 | 0.000 | 2.1 | 15.151 | 11.93 |
| 0.05 | degenerate | 0.001 | 1.214 | 0.000 | 0.6 | 11.594 | 12.75 |

**`D_article` passes clean through the target** — bracketed between 1.61 at
gate 0.50 and 2.19 at gate 0.30, against real's 1.72 — and **`s(14)` falls
monotonically across the entire sweep**, 10.4 → 7.0 → 5.1 → 3.4 → 2.1 → 0.6,
away from real's 16.1. It never turns.

Pairwise within-article breadth is therefore **not sufficient** to produce the
dip. `R52`'s interpretation is falsified as stated.

## Why it fails, which is the useful part

The failure mode is legible in `d50_same`. The gate widens the distribution by
**collapsing the near end** — 0.896 → 0.563 → 0.001, rows becoming near-identical
when no level fires — rather than pushing same-article pairs *out* toward the
global scale. At gates 0.15 and 0.05 `p10` reaches ~0 and `D_article` degenerates
entirely.

Decisively: **`overlap` is exactly 0.000 at every gate**, against real's 0.114.
No mechanism in this family has ever moved it off zero (`R54`, and all six arms
here).

So real does not have a *wider* within-article distribution in the sense this
mechanism produces. It has **same-article pairs sitting at the global distance** —
mass at the far end, not stretch at the near end. `R53` already showed this
directly: `p90` of `P(d | gap)` is pinned near the global scale at *every* gap
including gap 1, where at least 10% of adjacent passages are already unrelated.

The refined target is therefore the **conditional** structure, not the marginal
spread: at small gap, a mixture of coherent pairs and already-global pairs, with
the mixing weight decaying in gap. `D_article` was the wrong summary to optimise;
`overlap` is the discriminating one.

## Method note: the sweep moved to NRP GPU

`R54` ended with Atlas CPU Package 0 at 99 C, one degree below critical, with
another workload on the box. This sweep needs only the generator and measured
constants, so it was moved to an NRP A10 (0 of 4 heavy GPU slots in use; the 1T
fleet is swarm-class and does not compete).

Two things had to be got right, and both are recorded because they are traps:

* **Memory.** The first pod was OOMKilled at 32 Gi. The cause was hashing dense
  `(n_art, max_len, fil_dim)` tables: with lognormal sigma 1.2 the longest
  article runs to ~1700 rows, so the level-0 table alone is ~8.6 GB before
  uint64/float64 temporaries. Hashing **per row per chunk** — which is what a
  genuine random-access emitter does anyway — fixes it.
* **GPU utilisation.** The second pod was killed by NRP after 36 s. Keeping the
  hash in numpy on the CPU left the GPU idle through the build, below the
  platform's 40% rule. The hash was therefore ported to torch.

That port risked exactly the divergence `R48` warns about, because torch's `>>`
on int64 is arithmetic where uint64 needs logical. It is handled by masking every
shift, and — the point — **numpy remains the reference and `hashgpu.verify`
asserts bit-equality on all four entry points at startup, aborting the run on any
mismatch**. It passed on both CPU and the A10.

Throughput: **12 s per arm on the A10** against roughly 10 minutes on Atlas.

NRP resources were deleted after the run.

## What is established

* `D_article` is reachable and exceedable; it does not produce the dip.
* `s(14)` moves monotonically the *wrong* way as within-article breadth grows.
* `overlap` has never left 0.000 in any arm of any mechanism tried.
* The discriminating quantity is `overlap`, not `D_article`.

## What is not

* Any mechanism that places same-article pairs at the global distance. None has
  been designed.
* Whether `overlap` and `s(14)` move together. The prediction is that they do,
  and it is untested.
* The `g1` column in this round uses an inline TwoNN MLE rather than
  `geometry.id_twonn` and is **not comparable** to earlier rounds; it is omitted
  from the table above for that reason.
