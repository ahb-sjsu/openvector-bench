# What synthetic embedding corpora can and cannot reproduce: results from a 22-campaign pre-registered study

*Draft for LinkedIn — Andrew Bond*

I'm sharing results from a research program on a question with direct
consequences for how we benchmark vector search systems: **to what
extent can a deterministic generator substitute for a real embedding
corpus?**

The motivation is practical. Evaluating ANN indexes and vector
databases at realistic scale requires corpora of 10⁹–10¹² embeddings —
hundreds of terabytes that are effectively undistributable. A
deterministic, byte-reproducible, random-access generator would reduce
such a benchmark to a signed manifest of kilobytes: any party could
regenerate any shard on demand and verify it cryptographically. Whether
the generated data actually *behaves* like real data is the question
the program set out to answer, across 22 pre-registered campaigns
(~400 configuration evaluations against Cohere Embed-V3 over English
Wikipedia, 41M rows), with all results — positive, negative, and
boundary — in a public repository.

Three findings.

**1. The intrinsic-dimension profile of an embedding corpus is a
property of corpus assembly, not of the embedding model.**

Retrieval-scale corpora exhibit a well-known scale-resolved dimension
profile: the local growth dimension rises steeply with neighborhood
radius. The tempting interpretation — nested semantic manifolds, or
model-specific geometry — is wrong. The profile is a two-population
mixture created by document structure: a row has roughly 23
index-local neighbors (same-article passages), after which neighbors
are drawn from the global cloud, and the profile's ramp is the
crossover. The controls are decisive: the profile responds to sampling
density and clumpiness at fixed row count, a single adjacent row moves
the TwoNN estimate from 26.1 to 14.1, and permuting row order —
altering no vector — collapses the registered density-response spans
to zero. The result replicates across MSMARCO-v2 (same encoder,
different corpus) and DBpedia under two OpenAI encoders: the shape is
universal, the levels are jointly corpus- and encoder-determined.
Practical implication: intrinsic-dimension comparisons across corpora
are not well-defined without matched sampling density and ordering,
and any i.i.d. generative model is structurally excluded from
reproducing the density response at any parameter setting.

**2. Matching geometry does not match index behavior.**

Our strongest generator passed 8 of 10 registered geometric criteria
on held-out data — intrinsic dimension, distance contrast, hubness,
and both density-response summaries — with margins and cell-occupancy
statistics nearly indistinguishable from real. Under identical
IVF-flat pipelines, it was nevertheless **25× easier** to search:
nprobe for 95% recall@10 of 2, versus 47–50 for the real corpus. The
mechanism is identifiable: generated neighborhoods align with the
partition k-means recovers, while real cross-document neighbors
scatter across every cell. No standard geometric statistic measures
this partition-scatter property, which implies that ANN benchmarks
built on geometrically-validated synthetic data can systematically
overstate system performance. We have since packaged the measurement
as a per-corpus difficulty audit and calibrated it across four real
corpora — which themselves spread 3× in probe depth (np@95 18–51), a
caution against treating any single corpus as "realistic."

**3. Query-side batteries are memorization detectors, and the bound is
dose-limited.**

The deepest result concerns what generation cannot do in principle.
Real query vectors carry per-row placement information about the
corpus they were embedded against. Across the full licensed mechanism
hierarchy — train-fitted rotation, mean restoration, spectral
matching, and mixture-based density placement under a declared
memorization guard — the query-side battery's core statistic remains
inflated at ×2.0–2.6 for every deterministic, byte-reproducible
generator using compressed train statistics. The closing measurement
traced the full description-length curve, from 64 mixture components
to contraction toward literal nearest train rows: the curve is flat.
Closure saturates by K≈1024 components, and even the full train set —
1.2 GB of stored data — reaches only ×2.0 at doses that preserve
corpus-side geometry. The binding constraint is displacement toward
the data, not bits of train data encoded. In consequence, the
pre-registered admission rule functions as a memorization detector:
it separates generation from storage along the entire continuum, and
the replication identifies the signal it detects as region-to-region
non-exchangeability of large ordered corpora — present at full
strength in Wikipedia and MSMARCO, absent in small exchangeable sets.

**Methodology**

The program was run under strict pre-registration: every campaign
declared its mechanisms, predicted outcomes, kill criteria, and search
budget before touching held-out data; frozen candidates were
identified by byte hash and judged in one-shot evaluations with no
retries; adverse verdicts stood. Eleven mechanisms were eliminated by
their own pre-stated falsifiers, and the map of those eliminations —
a single spectral trade surface that the real corpus's statistics lie
off of — is itself a central result. The verification process was
also measured: held-out verdicts against a heterogeneous corpus
proved sensitive to draw size (a four-block draw flipped a verdict on
band variance alone), and the corrected protocol — minimum eight-block
draws, fixed before freezing — is now registered and binding.

The complete record — specifications, per-campaign verdicts, the
frozen generator, audit tooling, and both papers in draft — is public
at **github.com/ahb-sjsu/openvector-bench**. Two submissions are in
preparation: the corpus-assembly result with its cross-corpus
replication, and the generation boundary with the memorization bound.
I welcome discussion from colleagues working on vector search,
embedding geometry, benchmark design, or pre-registered evaluation
methodology.
