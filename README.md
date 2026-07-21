# OpenVector Bench

A **nested, content-addressed benchmark family** for vector search at
10⁶–10¹² rows, with three independent notions of a correct answer.

> **Status: design and validation stage.** The specifications are registered
> and the geometry battery runs; no tier is published yet. Nothing above the
> real/procedural seam (§ *Tiers*) will be released as a benchmark until the
> registered validations pass. If they fail, the family stops at the seam and
> says so.

---

## Why

Three problems with how vector search is currently benchmarked:

**1. Scale and distribution are confounded.** Results at 10⁶ and 10⁹ are
reported on *different corpora*, so when recall falls between them, nobody can
separate "search got harder with N" from "the data changed". Here every tier
is a strict subset of the next — the distribution is fixed and only N varies.

**2. Billion-scale corpora cannot be distributed, so few people evaluate at
scale.** A 10¹² corpus is ~128 TB. This benchmark distributes a *signed Merkle
manifest* instead: fetch kilobytes, then either regenerate shards
deterministically or fetch only the shards you need, every byte hash-verified.
The expensive artifact — exact ground truth for a fixed query set — is
computed once and published as a few MB.

**3. One metric is reported where three differ.** A system can reproduce its
own ranking almost perfectly while diverging from true nearest neighbours, and
preserve true neighbours while degrading actual relevance. Measurements
motivating this benchmark found recall **0.999** against an index's own exact
ranking and **0.592** against fp32 truth *for the same queries at the same
instant*. A benchmark that reports one number cannot see that.

## Three truth layers

| layer | what it is | scale | cost |
|---|---|---|---|
| **L1** geometric | exact k-NN under the frozen metric | every tier | one exhaustive pass per tier |
| **L2** structural | relevance from links, citations, Q→A, cross-language pairs | corpus-scale | free, but *biased* — bias statistics ship with the labels |
| **L3** human | independent relevance judgments | 10³–10⁴ queries | reuse existing judged sets where licensing permits |

Queries carry **difficulty strata** (local intrinsic dimension, neighbour
margin, hubness exposure, neighbour dispersion, L1/L2 disagreement) so results
are reported by stratum — average recall conceals exactly the failures worth
studying.

## Tiers

`T6 … T12` (10⁶ … 10¹² rows), each a strict subset of the next. Membership is
a published content-addressed permutation, **not a prefix** — sources arrive
ordered by language, dump, or crawl date, and a prefix would make the small
tiers monolingual and poison every cross-scale comparison.

**The real/procedural seam is labelled per tier.** No public corpus of real
neural embeddings exists much beyond 10⁹. Tiers above the seam are
procedurally generated and are legitimate only insofar as the registered
validations hold:

- **RC-1** — is the generated corpus geometrically equivalent to real
  embeddings on the properties that govern ANN search, over a prespecified
  grid of sample size and neighbourhood scale? (`spec/PREREG_RC1.md`)
- **RC-2** — does matching that geometry *predict ANN behaviour never used in
  fitting* (IVF recall curves, cell occupancy, margin distributions, rerank
  depth)? Sealed; opened once against one hashed generator.

Ground truth is **not** nested — a query's true neighbours change as the
corpus grows — so GT is computed and published per tier.

## Validation status & results

Design-and-validation stage: the instrument is built and the seam is being
tested. **No tier is published** — nothing above the real/procedural seam ships
until RC-1 and RC-2 hold. What has been measured so far, with every artifact
committed as produced:

**RC-1 round 1 — the battery is an instrument, not a formality.**
Target: Cohere Wikipedia Embed-V3 (en), 1024-d, over a 300-cell grid
(n ∈ {25k…200k} × k ∈ {10,30,100} × 5 subsamples) under the registered angular
metric. All three frozen nulls are **rejected** (0/12 cells admitted each); the
measured target's intrinsic dimension is stable in n (≈52.2 → 52.1 over 8×) while
hubness grows with n — structure invisible at a single operating point. Crucially,
**`null_lowrank` — the recipe behind the existing 1B/10B synthetic corpora — is
rejected too** (≈1/7 the hubness of real embeddings; PCA-256 retains 1.57× the
neighbours, i.e. trivially compressible in a way real embeddings are not). So a
systems/recall result measured on that corpus *"is a statement about that corpus,
not about real retrieval"* — which is exactly why retrieval tiers wait for a
fitted, RC-validated generator.
→ [`results/RC1_ROUND1.md`](results/RC1_ROUND1.md) ·
[`results/rc1_scores.json`](results/rc1_scores.json) ·
[`results/rc1_cells.json`](results/rc1_cells.json) · prereg
[`spec/PREREG_RC1.md`](spec/PREREG_RC1.md).

**§6 reconstruction — the corpus-as-object regenerates byte-identically.** The
registered experiment (publish → delete every byte source → reconstruct on a
fresh worker from whatever resolves) passes its four machine-checkable criteria:
reconstructed shards are byte-identical to the originals, with the event log
(regeneration rate, per-source latency, bytes moved) as the reportable output.
Reconstruction is **resumable** (`resume=True`, DISTRIBUTION §3) — a preempted
worker skips every finished, content-addressed block and re-materializes only the
missing/torn ones.
→ [`harness/distribution/reconstruct_experiment.py`](harness/distribution/reconstruct_experiment.py)
· reproduce credential-free with
[`notebooks/reproduce.ipynb`](notebooks/reproduce.ipynb).

**Scale — distribution vs. retrieval, kept separate.** The regenerate-from-seed
distribution model is being exercised at **10¹¹ rows** in the sibling systems tool
([turboquant-pro](https://github.com/ahb-sjsu/turboquant-pro)'s fleet build): a
kilobyte manifest, each worker regenerating only its own seeded range with **zero
corpus movement**, over resumable, preemptible workers. That validates the
*distribution* claim at scale. Its *retrieval* numbers, however, are a **systems
measurement on a low-rank synthetic corpus** (the `null_lowrank` class rejected by
RC-1 above), so they live with the systems tool — **not** as an OpenVector Bench
tier. This separation is the point: distribution scales now; a real-retrieval
*benchmark* tier at that scale waits on RC-2.

## Repository layout

```
spec/       registered specifications (prereg, distribution, family design)
harness/    measurement code: geometry battery, distribution/verification
notebooks/  reproduce.ipynb — publish → delete → reconstruct → verify, end to end
results/    measured outputs, committed as produced
```

## Reproducing a corpus

A corpus is a signed Merkle manifest; the bytes come from deterministic
regeneration or any mirror, verified chunk-by-chunk either way. Run
`notebooks/reproduce.ipynb` top to bottom with **no credentials** for the
whole cycle in miniature, or
`harness/distribution/reconstruct_experiment.py` for the registered §6
experiment with machine-readable pass criteria. Credentials, when you point
at real mirrors, are ambient only: boto3's standard chain for `s3://` (with
`OVB_S3_ENDPOINT` for non-AWS endpoints such as NRP Ceph) — never pasted
into a cell.

## Design commitments

- **Registered before measured.** Thresholds, nulls, and pass rules are fixed
  in advance; deviations are recorded with dates and reasons rather than
  silently applied. Misses are published as misses.
- **Exact, never approximate, where it gates.** Admission filters computed
  with approximate neighbours would be circular.
- **Verification over trust.** Regeneration is an optimization checked against
  a hash; a mismatch is a cache miss that falls through to a byte source, not
  an error. Correctness comes from the manifest either way.
- **No single point of failure.** A durable copy independent of any one
  provider; caches are replaceable by construction.

## Licence

Code: MIT (`LICENSE`). Specifications, manifests, ground truth, and labels:
CC-BY-4.0 (`LICENSE-DATA`). Third-party corpora are referenced by manifest and
hash under their own terms — this project distributes *pointers and hashes*,
not other people's data.

## Citation

`CITATION.cff` (populated on first release).
