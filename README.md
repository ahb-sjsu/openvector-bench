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

## Repository layout

```
spec/       registered specifications (prereg, distribution, family design)
harness/    measurement code: geometry battery, distribution/verification
results/    measured outputs, committed as produced
```

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
