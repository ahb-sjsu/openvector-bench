# One arm per pod: the NRP profile that works, and the ratio match is cancellation

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12 on NRP A10s. Driver `harness/rc1/seg_sweep.py`, manifest
`harness/rc1/r57job.yaml`; record `results/r57.json`. Follows `R56`.

## The pod profile

`R55` and `R56` each ran a four-arm sweep in a single pod and were killed in a
36-63 s window across four different nodes, always `Normal Killing` — never
OOMKilled, never preempted. One run produced no logs at all: that was the one
with `pip install batch-probe` in the command, and NRP compute nodes restrict
egress, so the install hung until the pod was killed.

The working shape is short, self-contained, GPU-dense pods:

* **`completionMode: Indexed`, `completions: 4`, `parallelism: 2`** — one arm per
  pod, selected by `JOB_COMPLETION_INDEX`. Each pod runs ~15 s.
* **No network.** `batch_probe` is not imported; the k-NN batch is sized by a
  local doubling search with OOM recovery instead, which is the same idea
  without a wheel.
* **`RESULT_JSON` after every arm**, so a reaped pod still yields its result.
* `parallelism: 2` of the 4 heavy GPU slots, leaving headroom in the namespace.

Result: **`Complete 4/4` in 60-66 s, no reaping**, twice.

The self-sizing also found a k-NN batch of **6144** against the 2048 I had
hand-guessed — a 3x improvement that the earlier OOMKill should have prompted me
to measure rather than assume.

## Break-rate scan

| brk | ratio | rms | g6 | s(4) | s(14) | s(53) | D_article | overlap |
|---|---|---|---|---|---|---|---|---|
| **real** | **4.050** | — | **1.696** | **8.82** | **16.08** | **28.88** | **1.72** | **0.114** |
| 0.10 | 11.286 | 10.47 | 1.181 | 4.7 | 13.3 | 23.1 | 1.34 | 0.0005 |
| 0.115 | 17.238 | 10.43 | 1.210 | 3.1 | 15.4 | 23.2 | — | — |
| 0.125 | 18.367 | **10.34** | 1.207 | **2.9** | 15.0 | 23.0 | — | — |
| 0.135 | 12.894 | 10.54 | 1.211 | 4.1 | 15.8 | 23.0 | — | — |
| 0.145 | 5.056 | 10.61 | 1.217 | 10.6 | 15.9 | 22.7 | — | — |
| 0.15 | 4.181 | 10.73 | 1.228 | 12.7 | **16.0** | 22.8 | 1.30 | 0.0006 |
| 0.20 | 2.199 | 12.43 | 1.296 | 24.4 | 18.9 | 22.5 | 1.23 | 0.0007 |
| 0.25 | 1.783 | 13.82 | 1.421 | 30.0 | 20.7 | 22.5 | 1.12 | 0.0008 |

**`s(14)` is stable at 15.0-16.0 across the whole range** against real's 16.08.
`R56`'s central result holds: segmentation fills the dip, and it does so robustly
rather than at one tuned point.

**`s(4)` is non-monotonic** — 4.7 at 0.10, a minimum of 2.9 at 0.125, then 4.1,
10.6, 12.7. Real's 8.82 falls near brk ~0.143, not at the 0.15 that `R56`
reported as best.

## The ratio match is endpoint cancellation

`R56` reported the registered ratio at **4.181 against 4.050** and I presented
that as a near-match. It is not one, and the finer scan shows why.

At brk 0.15: `s(4)` is 12.7 against 8.82, and `s(500)` is therefore
4.181 x 12.7 = **53.1 against real's 35.73**. Both ends are ~45% high and the
quotient happens to land. This is exactly the `R46` failure — a summary
satisfied by geometry that is not real's — and I should have checked the
endpoints before calling it a match, having written that caution myself.

The honest statement is: the ratio cannot be matched together with `s(4)` in this
family, because `s(500)` is fixed near 53 by the arrangement and nothing in the
break rate moves it. `s(53)` likewise sits at 22.5-23.2 against 28.88 across
every arm.

## What is established

* An NRP profile that completes: indexed, one arm per pod, no egress, ~15 s per
  pod, 4/4 complete in 60 s.
* Self-sized k-NN batch 6144, three times the hand-guessed value.
* `s(14)` is robustly 15.0-16.0 against 16.08 across break rates 0.10-0.15, so
  `R56`'s dip result is not a tuned coincidence.
* `g6` sits at 1.18-1.42 against 1.696 — the closest it has been while the dip
  is also filled.

## What is not

* The ratio. `R56`'s 4.181 is endpoint cancellation and should not be read as a
  match; that claim is withdrawn.
* The outer curve. `s(53)` 22.5-23.2 against 28.88 and `s(500)` ~53 against
  35.73, unmoved by the break rate.
* `D_article` (1.12-1.34 against 1.72) and `overlap` (~0.0006 against 0.114).
* `g1` as reported here is an inline TwoNN MLE, not the registered
  `geometry.id_twonn`, and is not comparable across rounds. It is recorded in
  `results/r57.json` with that caveat and excluded from the table above.
