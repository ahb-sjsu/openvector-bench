# Segmented articles fill the k=14 dip, after five mechanisms failed

**Exploratory, not a registered round. PARTIAL — 3 of 4 arms; see the run note.**
No admission claim, seal untouched. Measured 2026-08-12 on an NRP A10. Driver
`harness/rc1/seg_sweep.py` with `harness/rc1/hashgpu.py`; record
`results/r56.json`. Follows `R55`.

## What R55's failure mode named

`R55` falsified the breadth reading and, more usefully, showed *how* the gate
failed: when all levels switch off, two rows in one article both collapse onto
the **article centre** and become identical — `d50_same` reached 0.001. Gating a
level removes a row's *variation* while leaving the *shared* component intact.

Real needs the opposite. So an article becomes a sequence of **segments**, each
with its own centre: pairs within a segment are close, pairs in different
segments of the same article are unrelated by construction.

Segmentation is hierarchical so it stays random-access — the segment of row `p`
is `p >> k` where `k` is the smallest level whose keyed break-bit fires, giving
geometric block lengths and the heavy tail `R53` measured, with no scan over
predecessors.

## The dip fills

| brk | ratio | rms | s(4) | **s(14)** | s(53) | D_article | d50 same | overlap |
|---|---|---|---|---|---|---|---|---|
| **real** | **4.050** | — | **8.8** | **16.1** | **28.9** | **1.72** | **0.884** | **0.114** |
| 0.00 | 6.514 | 10.78 | 8.2 | 10.3 | 23.2 | 1.24 | 0.896 | 0.0000 |
| **0.15** | **4.181** | 10.73 | 12.7 | **16.0** | 22.8 | 1.30 | 1.060 | 0.0006 |
| 0.35 | 1.310 | 16.86 | 41.1 | 22.7 | 22.3 | 1.11 | 1.070 | 0.0007 |

**`s(14)` reaches 16.0 against real's 16.1** at a break rate of 0.15, from 10.3
with segmentation off. The registered ratio lands at **4.181 against 4.050**,
within 3%.

The dip had resisted five mechanisms — distributed article extents (`R47`),
nested arrangement levels (`R49`), index-contiguous sections (`R50`), rising
per-level dimensions (`R51`), and level gating (`R54`/`R55`) — and worsened under
four of them. Breaking the shared component fills it on the first attempt.

## The stated hypothesis was wrong, and that matters

`R55` concluded that `overlap` was the discriminating quantity, since it had
never left 0.000 while `D_article` moved freely. **That is not what happened.**
`overlap` reached only 0.0006 here, against real's 0.114, while `s(14)` went to
target.

So the dip is not filled by same-article pairs sitting at the global distance.
It is filled by *resetting the shared centre partway through an article*, which
raises the local growth dimension directly without needing far-end mass. The
`overlap` reading was a correlate of the mechanism in real, not the lever.

This is the sixth time in this arc that a quantity identified as "the missing
one" turned out to be a symptom. The pattern is now well enough attested to
state plainly: summary statistics of a neighbourhood do not identify the
construction that produces it, and the only reliable move has been to change a
mechanism and measure what follows.

## What is still wrong

* **`s(4)` overshoots**: 12.7 against 8.8, where the un-segmented build had 8.2.
  Segmentation raised the finest scale along with the middle.
* **`s(53)` is unmoved at 22.8** against 28.9, so the outer curve is untouched.
* **`rms` barely improves** (10.78 → 10.73), because `s(4)` degraded as much as
  `s(14)` gained. The curve is a better *shape* and not yet a better *fit*.
* `D_article` 1.30 and `overlap` 0.0006 remain far from 1.72 and 0.114.

The break rate is sharply tuned: 0.35 overshoots catastrophically (`s(4)` 41.1,
ratio 1.310), so the working region is narrow around 0.15 and was not resolved
finely.

## Run note — partial

Four arms planned, **three completed**. The NRP pod was reaped at ~50 s, as in
`R55`; both rounds' pods are killed in a 40–55 s window on different nodes, which
is most likely the platform's GPU-utilisation enforcement catching the CPU-bound
phases between GPU work. Results here were captured from the live pod log by
polling at 32/44/56 s rather than from the job's final JSON, so `brk` 0.55 is
unrun and `results/r56.json` is transcribed from that log.

Throughput was 14 s per arm. NRP resources deleted after the run.

## What is established

* Segmented articles fill the k = 14 dip: `s(14)` 10.3 → 16.0 against 16.1.
* The registered ratio reaches 4.181 against 4.050.
* `overlap` is **not** the lever — it stayed at ~0.0006 while the dip filled.
* The mechanism is breaking the *shared* component, not widening the variation.

## What is not

* A better overall fit. `rms` is flat because `s(4)` overshoots by as much as
  `s(14)` improves.
* Any movement in `s(53)`, `D_article` or `overlap` toward their targets.
* A finely resolved break rate; 0.15 works and 0.35 fails badly, with nothing
  measured between.
* The gates. `g1`, `g5` and `g6` were not measured in this round at all.
