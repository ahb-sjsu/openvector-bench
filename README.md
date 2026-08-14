# OpenVector Bench

[![CI](https://github.com/ahb-sjsu/openvector-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/ahb-sjsu/openvector-bench/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey.svg)](LICENSE-DATA)
[![status: validation stage](https://img.shields.io/badge/status-validation%20stage-orange.svg)](#status-and-results)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A **nested, content-addressed benchmark family** for vector search at
**10⁶–10¹² rows**, with three independent notions of a correct answer.

> **Status: design & validation stage — no tier is published yet.** The specs are
> registered and the geometry battery runs; nothing above the real/procedural seam
> ships until the registered validations (RC-1, RC-2) pass — and if they fail, the
> family stops at the seam and says so. **[→ Status and results](#status-and-results)**

## The idea in one picture

A 10¹² corpus is ~128 TB — too big to host or hand out. So the corpus *is* a
signed manifest of kilobytes: you rebuild the bytes yourself, and every one is
hash-verified against the manifest either way.

```mermaid
flowchart LR
    A["Signed Merkle manifest<br/>(kilobytes)"] --> B{"per shard:<br/>first source<br/>that verifies"}
    B -->|deterministic| R["Regenerate<br/>from seed · no network"]
    B -->|or| F["Fetch a mirror<br/>only the shards you need"]
    R --> V{"hash ==<br/>manifest root?"}
    F --> V
    V -->|yes| S["Byte-identical shard"]
    V -->|"no — cache miss"| B
    S --> GT["Exact ground truth<br/>computed once · a few MB"]
    classDef ok fill:#d1f0d1,stroke:#2e7d32,color:#14320f;
    class S,GT ok;
```

Every tier is a **strict subset** of the next, so a recall change is about *N*,
not the data; ground truth and per-query difficulty strata are published per tier.

## Quickstart

```bash
pip install -e ".[dev]"      # numpy + scipy (+ ruff/black/pytest for dev)
pytest -q                    # manifest, generator determinism, geometry battery

# Rebuild a corpus end to end, credential-free (publish → delete → regenerate → verify):
jupyter notebook notebooks/reproduce.ipynb
# …or the registered §6 reconstruction experiment with machine-readable pass criteria:
python harness/distribution/reconstruct_experiment.py --help
```

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

## Status and results

Design-and-validation stage: the instrument is built and the seam is being
tested. **No tier is published** — nothing above the real/procedural seam ships
until RC-1 and RC-2 hold. Where each piece stands, with every artifact committed
as produced:

| Milestone | What it proves | Status | Evidence |
|---|---|:---:|---|
| **Geometry battery** (RC-1 instrument) | the battery tells real embeddings from wrong ones | ✅ **passed** | 3/3 frozen nulls rejected · [`RC1_ROUND1.md`](results/RC1_ROUND1.md) |
| **§6 reconstruction** | a corpus regenerates **byte-identically** from a kB manifest | ✅ **passed** | 4/4 criteria · [experiment](harness/distribution/reconstruct_experiment.py) · [notebook](notebooks/reproduce.ipynb) |
| **Distribution at scale** | regenerate-from-seed works at **10¹¹**, zero data movement | 🟡 **in progress** | sibling [turboquant-pro](https://github.com/ahb-sjsu/turboquant-pro) fleet build (systems evidence) |
| **Frozen generator** | a bit-exact, random-access, chunk-invariant family exists and is hashed | ✅ **shipped** | [`openvector_bench/segment_gen.py`](openvector_bench/segment_gen.py) — identity `e8423665…` (RC-3), prior `80d94f61…` recoverable · [`spec/RC3_FREEZE.md`](spec/RC3_FREEZE.md) |
| **RC-2** — one-shot held-out geometry | the frozen family judged **once** on real blocks no round touched | ⛔ **excluded, as pre-stated** | mandatory trio failed on g6; the negative is registered and held-out · [`results/RC2_VERDICT.md`](results/RC2_VERDICT.md) · [`spec/RC2_FREEZE.md`](spec/RC2_FREEZE.md) |
| **RC-3** — second campaign + one-shot | one new mechanism (pool spectrum) against honest 10-block bands | 🟡 **8/10 held-out — the mandatory trio passes** | first family ever to hold g1/g5/g6 on unseen data; misses g4 (+15%) and the G1-vs-n exponent, both pre-declared · [`results/RC3_VERDICT.md`](results/RC3_VERDICT.md) |
| **RC-4 / RC-5** — five mechanisms | can the residual misses be fixed inside this family? | ⛔ **all refuted; frontier stands** | 80 arms, five registered kills, one trade surface; no freeze, no one-shot spent · [`results/RC4_VERDICT.md`](results/RC4_VERDICT.md) · [`results/RC5_VERDICT.md`](results/RC5_VERDICT.md) |
| **ANN-behaviour characterization** | does geometric admission predict index behaviour? | ⛔ **no — 25× probe-depth divergence** | open (non-sealed) IVF study: real needs nprobe 47–50 for 95% recall, the generator needs 2 — margins and occupancy nearly match while the operational curve diverges; the Goodhart concern is now *measured* · [`results/R80_ANN.md`](results/R80_ANN.md) |
| **RC-2 (sealed ANN prediction)** | geometry **predicts** ANN behaviour it never fit | 🔒 **sealed, and now demonstrably necessary** | R80 shows geometry alone cannot certify it; opens once, after an admission battery that includes partition scatter |
| **Published tier** (T6–T12) | a usable benchmark above the real/procedural seam | ⛔ **gated** | requires full admission **and** the sealed prediction test |

```mermaid
flowchart LR
    B["Geometry battery<br/>✅ discriminates"] --> R1{"RC-1<br/>generator matches<br/>real geometry?"}
    R1 -->|"🟡 frontier: 8/10 held-out,<br/>mandatory trio passes (RC-3);<br/>residuals proven family-level (RC-4)"| FIT["Architecture change<br/>(RC-5, if attempted)"]
    FIT --> R1
    R1 -->|pass| SEAL["Hash + seal<br/>the generator"]
    SEAL --> R2{"RC-2 (sealed,<br/>one shot):<br/>predicts ANN<br/>behaviour?"}
    R2 -->|pass| PUB["Publish tier<br/>T6 … T12"]
    R2 -->|fail| STOP["Stop at the seam,<br/>say so"]
    classDef done fill:#d1f0d1,stroke:#2e7d32,color:#14320f;
    classDef block fill:#ffe0b2,stroke:#e65100,color:#4a2600;
    class B done;
    class R1,R2 block;
```

### Where the seam stands after four campaigns

The generator search ran four pre-registered campaigns in 2026 (every arm,
miss, and kill committed in [`results/`](results/); ~340 configuration
evaluations disclosed across [`spec/RC2_FREEZE.md`](spec/RC2_FREEZE.md) §4
and [`spec/RC3_FREEZE.md`](spec/RC3_FREEZE.md) §4):

- **The deliverable exists**: a deterministic, bit-exact, chunk-invariant,
  **random-access** generator ([`segment_gen.py`](openvector_bench/segment_gen.py))
  whose geometry was judged on held-out real blocks under freeze-first
  discipline — byte identity, expected outcome, and search budget declared
  before any unseen data was touched, twice.
- **RC-3's verdict is the frontier**: 8/10 registered criteria in band on
  four untouched blocks, including the mandatory intrinsic-dimension /
  contrast / hubness trio — the admission-critical result no prior family
  reached on unseen data ([`results/RC3_VERDICT.md`](results/RC3_VERDICT.md)).
- **The two residuals are precisely mapped, and RC-4 proved them
  family-level** ([`results/RC4_VERDICT.md`](results/RC4_VERDICT.md)):
  dims90 and PCA retention cannot jointly reach real under *any* reshaping
  of the shared direction pool (four spectral forms refuted) — real keeps
  neighbour-relevant variance partly outside its top PCA dimensions, which
  a shared pool cannot express; and every g1exp lever tried slides along a
  trend↔exponent trade curve instead of shifting it.
- **A methodology finding with reach beyond this project**: real's own
  block-to-block drift is comparable to several admission windows (its
  density response varies 2.4× across corpus regions), so bands registered
  from few blocks systematically over-exclude
  ([`results/R68_REBAND10.md`](results/R68_REBAND10.md)).

**The sealed ANN-prediction test remains sealed.** Full geometric admission
has not been reached; opening the seal early would burn the one shot.
Successor work (RC-5, if attempted) requires an architecture change, not
tuning: a generator whose fine-scale components have full amplitude in
directions its global spectrum suppresses.

### Attacking the blocker: adversarial generator discovery

Finding that generator is itself a search problem with a *registered* fitness —
so we attack it with a **searcher, an adversary, and the registered judge**. A
discovery engine ([Theory Radar](https://github.com/ahb-sjsu/theory-radar))
proposes generators that minimise geometry mismatch;
[`structural-fuzzing`](https://github.com/ahb-sjsu/structural-fuzzing) then
**mutates each candidate's parameters to find where its geometry breaks** — the
anti-Goodhart step, since a generator that only *games* the eight gates fails
under perturbation while one with the right mechanism survives; and RC-1
admission + the sealed RC-2 stay the judges, never optimised against. Both
engines share **one contract**, which reuses this repo's own geometry battery so
the objective *is* RC-1, not a proxy:

```python
from openvector_bench import make_evaluate_fn, measure_corpus

target = measure_corpus(real_base, real_queries)     # RC-1 battery on real embeddings
evaluate_fn = make_evaluate_fn(target, dim=1024)      # structural-fuzzing signature
score, per_gate_errors = evaluate_fn(params)          # searcher minimises; fuzzer attacks
```

Method, rationale, and the **binding integrity guardrails** (the seal stays
sealed; search on train/validation only; report the budget):
**[`spec/GENERATOR_SEARCH.md`](spec/GENERATOR_SEARCH.md)**. *Status: four
campaigns closed (rounds through `R77` in [`results/`](results/), each
pre-registered, misses included). The method delivered what it promised:
mechanisms found by structured search, wrong mechanisms killed by
registered falsifiers, and two one-shot held-out verdicts — one negative
(RC-2), one 8/10 with the mandatory trio passing (RC-3). Full admission
remains open; the residuals are proven family-level, not tuning gaps.*

### Why the 10¹¹ recall numbers aren't a tier

The 10¹¹ fleet build above validates **distribution** (regenerate-from-seed at
scale, zero corpus movement, resumable preemptible workers). Its **retrieval**
numbers, though, are measured on that same low-rank synthetic corpus — the
`null_lowrank` class **RC-1 rejects** — so they are a *systems* result and live
with the systems tool, **not** as an OpenVector Bench tier. Distribution scales
now; a real-retrieval benchmark tier at that scale waits on RC-2.

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
