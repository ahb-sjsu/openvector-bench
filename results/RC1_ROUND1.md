# RC-1 round 1 — the battery discriminates; no generator yet

**Run:** 2026-07-20, 300 cells. Target: Cohere Wikipedia Embed-V3 (en),
1024-d, unit-normalized. Grid: n ∈ {25k, 50k, 100k, 200k} × k ∈ {10, 30, 100}
× 5 subsamples, batteries A (corpus→corpus) and B (held-out query→corpus),
under the registered angular metric. Data: `rc1_cells.json`,
scores: `rc1_scores.json`.

**There is no fitted generator yet.** The candidates scored here are the three
frozen nulls, so this round answers one question only: *is the battery an
instrument, or a formality?*

## Result: the registered expectation is MET

| candidate | admitted | cells meeting the count rule | mandatory-gate failures |
|---|---|--:|--:|
| null_gaussian | **no** | 0/12 | 27 |
| null_shuffle | **no** | 0/12 | 25 |
| null_lowrank | **no** | 0/12 | 24 |

No frozen null satisfies the admission rule (PREREG §8), so the battery is
sufficient to reject the three ways of being wrong that we registered in
advance. It is *not* thereby shown sufficient to accept a generator that is
subtly wrong — that is what RC-2 exists for.

## The measured target profile (battery A, medians)

| n | k | ID (two-NN) | rel. contrast | hubness skew | PCA-256 retention | eff. rank |
|--:|--:|--:|--:|--:|--:|--:|
| 25k | 10 | 52.2 | 1.221 | 5.44 | 0.629 | 178.1 |
| 25k | 100 | 52.2 | 1.151 | 1.88 | 0.658 | 178.1 |
| 200k | 10 | 52.1 | 1.290 | 14.10 | 0.603 | 179.2 |
| 200k | 100 | 52.1 | 1.214 | 4.99 | 0.634 | 179.2 |

Two properties worth noting, both invisible at a single operating point:

- **Intrinsic dimension is stable in n** (52.2 → 52.1 across an 8× range) —
  it is a property of the distribution, as it should be.
- **Hubness grows steadily with n** (1.88 → 2.49 → 3.37 → 4.99 at k=100).
  A generator matched at 25k could diverge badly by 10⁹, which is precisely
  why the registered claim is scoped to the measured grid and why the
  scaling-exponent criterion exists.

## How the nulls fail (ratio to real, n=200k, k=100, battery A)

| | ID | rel. contrast | hubness | PCA-256 retention | eff. rank |
|---|--:|--:|--:|--:|--:|
| null_lowrank | 1.91 | 0.98 | **0.15** | **1.57** | 0.68 |
| null_gaussian | 6.67 | 0.87 | **0.09** | **0.04** | 5.60 |
| null_shuffle | 5.73 | 0.88 | 1.14 | **0.12** | 4.47 |

`null_lowrank` is the recipe behind the existing 1B/10B synthetic corpora. It
is much closer to real data than the other nulls — and still fails: nearly
twice the intrinsic dimension, **one-seventh the hubness**, and PCA-256
retaining 1.57× as many neighbours (0.99 absolute vs 0.63), i.e. it is
trivially compressible in a way real embeddings are not. Any systems result
measured on it is a statement about that corpus, not about real retrieval.

## Reported, not fixed: G5 discriminates nothing

Per-gate discrimination (§8 requires reporting this):

| gate | separates |
|---|---|
| G1 ID two-NN, G2 ball-growth, G3 eff-rank, G4 dims90, G6 hubness, G7 local-ID IQR, G8 PCA retention | all three nulls |
| **G5 relative contrast** | **none** |

**Relative contrast — a standard ANN-hardness predictor — has no
discriminative power here.** All three nulls sit within 13% of the target
(ratios 0.87–0.98), because at 1024-d on the unit sphere every corpus is
nearly equidistant regardless of structure.

G5 is **mandatory** under the registered rule, so the effective discriminative
burden falls on G1 and G6. Per §8 the gate is **not removed**: it was
registered, it is a cheap necessary-but-not-sufficient condition, and deleting
gates after seeing null results is the exact adaptive manoeuvre the
pre-registration forbids. It is recorded here as a limitation of the battery,
and it is an argument for RC-2 doing the real work of acceptance.

## What this round does *not* establish

- Nothing about any generator (none exists yet).
- Nothing above n = 2×10⁵; the extrapolation to 10⁹–10¹² is unaddressed and
  the hubness trend above shows why that matters.
- Nothing about semantic relevance — only geometry.

## Next

1. Fit a generator on the train split; select on validation (§7).
2. Hash and seal it, then open the sealed test **once**.
3. RC-2: does matching this geometry predict IVF recall curves, cell
   occupancy, margin distributions, and rerank depth that were never used in
   fitting?
