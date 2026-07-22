# RC-1 round 2 — formal §5 grid admission of the round-8 candidate: NOT ADMITTED (0/24)

**Run:** 2026-07-22, Atlas, the registered PREREG_RC1 v2 machinery in full:
n ∈ {25k, 50k, 100k, 200k} × k ∈ {10, 30, 100}, 5 subsamples, both batteries, exact
blocked k-NN, one k=100 neighbour structure per (corpus, n, subsample), equivalence
intervals per §5, **all three admission criteria** (the scaling-exponent criterion was
missing from the shipped scorer and was added before this run — commit `06187a6`).
**Validation-stage run:** real rows are train/validation only (sealed rows excluded by
the registered hash); the sealed 25% remains closed — a sealed one-shot only ever runs
against a candidate that has passed here. Candidate: `hier_query_corpus` at the round-8
point; battery-B queries are the family's own query block (§4 analogous-query clause —
the query generator is part of this candidate and is registered as such).

## Verdict

**NOT ADMITTED.** Count rule **0/24** cells; **42** mandatory-gate cell failures;
**6** scaling-exponent failures (all six are G6 hubness growth). Reported per the
binding falsification rule: a miss, as a miss.

This is the expected outcome, stated in the pre-run disclosure: the candidate was
fitted at [0.5, 2.0]× bands at n=8k; §5 demands ±15% (±20% for G2/G4/G7) over
25k–200k. The value of the run is the *map* it produces.

## The gate-by-gate map (24 cells; median ratio gen/real and range)

| gate | pass | median R | range | reading |
|---|---:|---:|---|---|
| G5 relative contrast | **24/24** | 1.02 | [0.99, 1.05] | matches — and separates nothing, exactly as §8 anticipated |
| G2 ball-growth | 7/24 | **0.97** | [0.64, 1.47] | *centre is right* — the round-7 mechanism holds at scale; interval width fails cells |
| G6 hubness | 3/24 | 0.64 | [0.23, 1.39] | battery-B close (0.86× at 25k), battery-A far; growth too shallow (below) |
| G1 intrinsic dim | 3/24 | 1.19 | [1.09, 1.29] | **fitted at 8k, drifts at scale** (below) |
| G8 PCA retention | 1/24 | 0.70 | [0.53, 0.93] | degrades with n |
| G3 effective rank | 0/24 | 1.93 | [1.92, 1.93] | flat, scale-independent miss — a mis-tuned colouring, not a mechanism gap |
| G4 dims90 | 0/24 | 2.24 | [2.22, 2.24] | same knob as G3 |
| G7 local-ID IQR | 0/24 | 0.54 | [0.27, 0.83] | spread halves at scale |

## The three findings that set round 9

**1. Real's G1 is n-flat; the candidate's is not.** Real reads 53–55 (battery A) /
60–63 (B) across a 8× range of n — the two-NN estimator is *pinned*, consistent with
the fine-scale near-duplicate structure diagnosed in the codebook-probe round
(`diag_target.json`: r1 1%-quantile 0.375 vs median 0.86). The candidate's flat
93-dim patches read 64 → 76 as sampling densifies (slope +0.04/+0.06 per decade vs
real's +0.01) — inside the |Δ| ≤ 0.05 tolerance, but the *level* exits the band by
100k. The n=8k fit was real; it does not transfer. The missing ingredient is the one
mechanism the campaign never built: **short-range near-duplicate structure** that pins
the two-NN reading independently of n.

**2. Hubness growth is the mandatory-gate killer — in both batteries, for different
reasons.** All six scaling-exponent failures are G6. Battery B: the candidate starts
close (11.0 vs 12.8 at 25k) but grows at +0.13/decade vs real's +0.22 — a *fixed*
`query_tail` gives a fixed query concentration, while real's query-induced hubness
compounds with corpus size. The query model needs an n-coupled concentration (the
capture-basin account predicts exactly this: basin sizes shrink as ~1/n while real's
per-basin query mass does not). Battery A: real reads 9.4–11.4 where the candidate
reads 2.1–4.8 — see finding 3.

**3. Battery A's query set inherits real's row ordering — a protocol observation that
is itself a Bond-Metric datum.** The registered harness draws battery-A queries as the
*first* `hold` corpus rows; Wikipedia rows arrive topically ordered, so real's
battery-A queries are topically **clustered** — a de facto concentrated query marginal
inside the "corpus-to-corpus" battery (its G6 = 9.4 at 25k, versus ≈1.5 for uniform
base→base queries at 8k in `diag_hubs.json`). The candidate's held-out rows are
exchangeable by construction and cannot mimic ordering. Two registered-process options
for round 9, to be decided *before* the next run: (a) re-register battery-A query
sampling as uniform (a harness change with a §9-style disclosed rationale), or
(b) keep the protocol and require the generator to model row-order correlation as part
of the corpus process. Either way the asymmetry is now documented rather than latent.

## What is *not* a wall

G3/G4 (1.93×/2.24×, dead-flat in n): the recolouring target spectrum is simply tuned
to the wrong shape for §5 bands — `spectrum_decay`/`reshape_mix` are proven strong
controllers (the round-7 Jacobian's dominant column). G5 passes everywhere. G2's
centre is right (0.97): the query-model mechanism for ball growth survives 25×
scale-up — the failure mode is subsampling-interval width, not bias.

## Round-9 target list (in falsification order)

1. **Near-duplicate short-range structure** → pins G1 flat in n (and should tighten
   G7); testable against `diag_target.json` before any swarm run.
2. **n-coupled query concentration** → G6 battery-B growth +0.22/decade.
3. **Battery-A protocol decision** (registered, either way) → resolves the A-side G6/G1 gap.
4. **Colouring retune at §5 bands** → G3/G4 (knob exists; fit, don't invent).
5. G7/G8 re-fit at scale after 1–4.

Iteration count to date (§7 duty): 8 pre-registered gating rounds + 7 disclosed
screening probes + this admission run; the seal has never been opened. Artifacts:
[`rc1_round2_scores.json`](rc1_round2_scores.json) (full per-cell ratios + CIs +
exponents), [`rc1_round2_cells.json`](rc1_round2_cells.json) (240 raw cells).
