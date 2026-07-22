# WP5-lite result: P1 FALSIFIED on both systems; P2 and P3 confirmed — anatomy is operational, the descriptor is not yet sufficient

**Run:** 2026-07-22, Atlas CPU, 26.4 min, driver `harness/wp5/wp5lite.py` (committed
with the launched run), registration [`WP5LITE_PREDICTION.md`](WP5LITE_PREDICTION.md)
(written before any index was built). Raw curves and D-matrix:
[`wp5lite.json`](wp5lite.json). Sealed rows never loaded. Reported per the binding
rule: misses as misses.

## Headline numbers (median over 3 seeds/subsamples per corpus)

Work to reach recall@10 = 0.90, and the registered sup-log gap D vs real over
recall ∈ [0.80, 0.99] (band = max(2·δ_real, log 1.5) = **0.405**):

| corpus | HNSW µs @ r=.90 | HNSW max recall | D_hnsw | IVF ndis @ r=.90 | D_ivf |
|---|---:|---:|---:|---:|---:|
| **real** | 167 | 0.999 | (floor 0.119) | 1497 | (floor 0.069) |
| **rd8** (matched gates+anatomy) | 97–151 | 1.000 | **1.06 — OUT (2.9×)** | 301–515 | **2.39 — OUT (10.9×)** |
| **rd6** (same G6, super-hubs) | — | **0.77–0.85** | unreachable | 2384–2567 | 0.64 — OUT (1.9×) |
| **null** (Gaussian) | — | **0.55–0.56** | unreachable | 13 483–13 591 | 2.78 — OUT (16×) |

## P1 — behavioral sufficiency: **FALSIFIED, both systems**

The round-8 candidate — six gates in band and real's hub anatomy at the fitting
scale — does **not** present the same operational problem as real. The direction is
systematic: **rd8 is easier than real everywhere** — ~1.2–1.7× cheaper at r=0.90 on
HNSW (gap growing to 2.9× across the interval) and **3–5× cheaper on IVF**
(ndis 301–515 vs ~1500).

Per the registration, the divergence is reported against the pre-named suspects:

- **IVF (D=2.39): the pre-named G3 suspect is confirmed in kind.** IVF probe
  economics are governed by coarse partition structure. rd8's 2^6.3 ≈ 79-cluster
  hierarchy under a spectrum already known 1.9× too concentrated (RC1 round 2)
  makes kmeans partitions nearly lossless — a handful of probes recovers
  everything. Real's mass is spread across partitions; it needs ~5× the distance
  computations at the same recall.
- **HNSW (D=1.06): consistent with the missing graded short-range ladder** (the
  round-9 frontier, `ROUND9_PROBES.md`). Real's graded near-duplicate μ-ladder
  forces fine-scale navigation work near the target; rd8's uniform-sparse patches
  build a cleaner navigable graph (its hub-rank ρ under approximation is 0.86–1.00
  vs real's 0.96 at *lower* ef). Scale is a contributing caveat: gates were fitted
  at n=8k, this test ran at 16k, and RC1 round 2 documents the candidate's G1
  drift with n.

**Consequence for the programme (Objective B):** gates + A_hub, matched at the
fitting scale, are **not yet a behaviorally sufficient descriptor** — the Level
2→3 rung is not passed. This is the cheap early negative the experiment was
designed to force. The constructive content: both divergences point at exactly
the two descriptor components the geometry campaign had already identified as
missing (spectrum shape beyond effective rank; the graded short-range ladder) —
the behavioral evidence independently ratifies the round-9 agenda rather than
opening a new front.

## P2 — discrimination: **PASSED** (the endpoint is sensitive; P1 is informative)

The null diverges catastrophically and measurably: on HNSW it **cannot reach
recall 0.57** at any ef ≤ 256 (maximal divergence, formally D = ∞ > 2·D_rd8);
on IVF D = 2.78 (16×, near-brute-force ndis ≈ 13.5k of 16k). Both systems clear
the > log 2 requirement. The test is therefore valid: P1's falsification reflects
the corpora, not an insensitive endpoint.

## P3 — anatomy is operational: **PASSED, beyond the registered prediction**

rd6 shares real's scalar battery-B G6 by construction (round-6 winner) with
opposite anatomy (centrality-driven super-hubs, b→b skew 7.0, max count 369).
Registered prediction: tail divergence — p95 per-query work ≥ 2× real at r≈0.95
and/or hub-rank Spearman lower by ≥ 0.2. Observed:

- **p95 latency 1.49–1.83 ms vs real 0.41–0.44 ms — 3.5–4.4×** (all seeds; the
  registered ≥2× clause passes decisively). Even p50 is ~4× (rd6 needs ef=256
  where real needs 48).
- Hub-rank ρ under HNSW: 0.76–0.85 vs real's 0.96 (Δ = 0.11/0.17/0.20 by seed —
  the ≥0.2 clause is met on one seed; the "and/or" is carried by the work clause).
- **Beyond the registration:** the divergence is not confined to the tail — rd6's
  HNSW recall **saturates at 0.77–0.85**; recall ≥ 0.9 is *unreachable* at any
  ef in the grid. Same scalar hubness, opposite operational fate: the super-hub
  anatomy doesn't just cost latency, it caps what the graph index can achieve.

This is the Bond Metric differential-testing claim demonstrated on real indexes:
**one-number hubness is operationally non-identifying** — two corpora sharing G6
differ by an *unreachable recall regime* on HNSW and 5× on IVF work.

## What this changes

1. **Round 9 gains a behavioral endpoint.** When the paraphrase-cloud family
   closes the geometric gaps (ladder + spectrum shape), re-run this protocol —
   the prediction that closing those two gaps collapses D_hnsw and D_ivf toward
   the band is now the natural WP5 follow-up registration, and a far stronger
   claim than geometric matching alone.
2. **The tqp `EXPLAIN` planner must be calibration-based.** Φ(W) does not yet
   predict recall–cost; any cost model shipped now must come from measured
   micro-sweeps at ANALYZE time, with the descriptor used for interpolation
   hints only. (Adopted as the design constraint for the `tqp query` verbs.)
3. **The Bond Metric paper's §Implications gets its evidence.** P3 upgrades the
   differential-testing claim from proposal to measurement; the paper should
   cite this result doc.

Iteration duty: single registration, single run, no protocol changes mid-flight;
any follow-up runs under a new numbered registration.
