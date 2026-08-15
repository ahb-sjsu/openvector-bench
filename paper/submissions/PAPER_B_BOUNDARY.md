# Where generation ends: the measured boundary between synthetic corpora and the data

**Submission draft B (boundary), 2026-08-15.** Split from the program
record `paper/profile/PROFILE_PAPER.md`; every number is measured in
the `openvector-bench` repository and its result record is named
inline. Companion submission: *The dimension profile of an embedding
corpus measures how the corpus was assembled* (draft A), which
establishes the corpus-assembly reading of embedding geometry this
paper builds on.

---

## Abstract

Synthetic stand-ins for retrieval-scale embedding corpora are attractive
— a deterministic, byte-reproducible, random-access generator makes a
128 TB benchmark distributable as a signed manifest of kilobytes. This
paper reports what such generation can and cannot reproduce of a real
corpus, measured to a registered conclusion across twenty-two
pre-registered campaigns (~400 configuration evaluations, every arm,
kill, and one-shot disclosed) against Cohere Embed-V3 over Wikipedia.

Corpus-side geometry is essentially achieved: a frozen generator family
passes the registered corpus-side battery nearly everywhere on held-out
data, including the density-response criteria that exclude i.i.d. models
structurally. Three boundaries then emerge, each measured rather than
suspected. **(1) A spectral trade surface**: five pre-registered
architectures, each killed by its own falsifier, move (dims90, PCA
retention, effective rank) along one surface — and the real corpus's
triple is off it. **(2) An ANN-behaviour gap**: a generator matching
eight of ten geometric criteria is 25× easier for an IVF index than the
corpus it imitates (nprobe@95: 2 vs 47–50), because geometric admission
measures nothing about neighbour-vs-partition scatter; the gap is
corpus-relative (real corpora themselves spread np@95 18–51), and a
later untargeted mechanism narrows it to within 2× of a real web-passage
corpus. **(3) A memorization bound**: the query-side battery — the same
statistics measured for real query vectors against the synthetic corpus
— is unpassable for the deterministic generator class at ×2.0–2.6, and
the description-length curve is flat: closure saturates by K≈1024
mixture components, and even contraction toward the literal train rows
reaches only ×2.0 at corpus-preserving doses. The wall is dose-limited,
not bits-limited; the pre-registered admission rule was, unknowingly, a
memorization detector. We also report a methodological finding with
teeth: held-out verdicts against a heterogeneous corpus are a lottery
unless the held-out draw is large enough — a four-block verdict flipped
a passing configuration to failing on band variance alone.

---

## 1. Setting and prior result

This paper's premise is established in the companion submission: the
scale-resolved dimension profile of a retrieval-scale embedding corpus
— its intrinsic-dimension ramp and the response of its geometry to
sampling density — is a property of *corpus assembly* (document-local
neighbour budgets in an ordered row sequence), not of the embedding
model. Structurally, no i.i.d. generator reproduces it at any
parameter setting; sequence-structured generation can. The question
this paper answers is how far that constructive direction goes:
whether a deterministic, byte-reproducible, random-access generator
can stand in for the real corpus, under a pre-registered admission
battery with sealed tests, and — where it cannot — what exactly stops
it. The measurement discipline is uniform: every campaign declares its
mechanisms, expected outcomes, kill criteria, and search budget before
touching held-out data; frozen configurations are identified by byte
hash; verdicts are one-shot.

## 2. Five architectures, one trade surface

The frozen family's residual misses are spectral: real holds
**dims90 = 357 ± 3** (its most stable statistic — sd 3 rows across
fourteen 600k blocks), **PCA-256 neighbour retention = 0.737 ± 0.003**,
and **effective rank ≈ 175** *simultaneously*, while the generator at its
frozen point sits at 417 / 0.742 / 150. Closing dims90 without breaking
the other two became a five-way mechanism hunt across two campaigns, each
mechanism named and given a kill criterion before its first arm ran.

| # | mechanism (rounds) | best dims90 reached | at that point | kill |
|---|---|---|---|---|
| 1 | pool amplitude power law (`R70`, `R73`) | 351 | hub skew 1.95, contrast 1.44 — both far out | concentration on head slots makes hub directions before dims90 arrives |
| 2 | two-scale head + floor (`R75`) | 436–443 (**rose**) | g5/g6 intact | the plateau adds tail dimensions faster than the head removes them |
| 3 | pool-size × α × floor (`R72`, `R76`) | 361 (in band) | retention 0.762 | dims90 needs pool ≲ 2^9.55, retention needs ≳ 2^9.9 — disjoint windows |
| 4 | partitioned pool: fine components on tail slots (`R77`) | — | eff rank 33–81, contrast 1.6–5.0 | the global profile crushes exactly the components the partition protects |
| 5 | dedicated centre subspace, flat then spectrally profiled (`R78`, `R79`) | 385 | retention 0.765, eff rank 79 | the profiled frame re-couples all three statistics onto the same curve |

Architecture 5 is the sharpest evidence, because half of it *worked*:
moving segment centres to their own subspace drove retention down
monotonically (0.742 → 0.698 across the dimension ladder) exactly as its
registered prediction said — the decoupling mechanism is real. But the
moment the centre spectrum was shaped to move dims90, retention and
effective rank re-coupled, tracing the same one-parameter curve as every
pool form. Plotted in (dims90, retention, eff rank), all five
architectures move along **one trade surface, and real's triple is off
it**.

The interpretation: real embeddings keep their neighbour-relevant
variance partly *outside* their top PCA dimensions while still
concentrating total variance. In this family every component — coarse
arrangement, segment centres, within-segment path, per-row ball —
composes directions from a shared vocabulary, so any spectral shaping
applied to the vocabulary reaches the neighbour structure and the bulk
spectrum together. Real plausibly has per-direction variance that is
*coherent across documents in some dimensions and incoherent in others* —
a joint property of direction and component that a shared vocabulary
cannot factor. The same campaign structure killed both G1-vs-n
mechanisms (above-article chapters move the exponent the wrong way;
article-length tails slide along a trend↔exponent trade curve without
shifting it, `R75`–`R77`).

Method note: the frontier configuration was left frozen rather than
retuned after each kill, and no held-out data was spent on either closing
campaign — a one-shot is only earned by a candidate that robustly beats
the standing verdict, and none did. The family's boundary, mapped by five
falsified mechanisms with their kill criteria stated in advance, is
itself the deliverable (`results/RC4_VERDICT.md`,
`results/RC5_VERDICT.md`); a successor family should be designed from the
trade-surface statement, not from further levers on this one.

---

## 3. Matching the geometry does not match the index

The frozen generator's final characterization is the sharpest lesson in
the arc (`results/R80_ANN.md`). Identical IVF-flat pipelines (k-means,
1024 cells, fixed seeds) over three real blocks and two generator seeds:

| | real (3 blocks) | generator (2 seeds) |
|---|---|---|
| recall@10 at nprobe 1 | 0.533–0.536 | 0.914–0.917 |
| **nprobe for 95% recall** | **47–50** | **2** |
| occupancy CV / skew | 0.38–0.40 / 0.61–0.88 | 0.31 / 0.44 |
| median margins (r2−r1)/r1, (r10−r1)/r1 | 0.051 / 0.213–0.219 | 0.054 / 0.212–0.214 |

A generator that matches eight of ten registered geometric criteria on
held-out data — including intrinsic dimension, contrast, hubness, and
both density-response spans — and whose margins and cell-occupancy
statistics are near-indistinguishable from real's, is **25× easier** for
an IVF index. The cause is visible in the construction: the generator's
global cloud is organized by generative clusters that k-means simply
recovers, so 92% of true neighbours share the query's cell; real
Wikipedia's cross-article neighbours (about a third of the k = 10
neighbourhood; companion draft A §5) scatter across every partition. The property that
governs probe depth — the alignment between neighbour structure and any
recoverable partition — is measured by none of the geometric criteria,
none of the s(k) curve, and none of the folklore statistics (margins,
occupancy) that nearly match here.

Three conclusions. First, the thesis of this paper extends to search
behaviour: ANN difficulty is a property of corpus assembly *relative to
the index's partition*, not of local geometry. Second, a geometric
admission gate — however registered and held-out — cannot certify a
synthetic corpus for ANN benchmarking; a partition-scatter criterion
(same-cell neighbour fraction, or probe depth itself) must be part of any
admission battery, and it is the first statistic on which this family
fails catastrophically rather than marginally, making it the most
informative fitness signal a successor search could have. Third, the
pre-registered decision to keep the behavioural test sealed behind
geometric admission was the right order for the wrong-way outcome we
feared: the gate this work never reached is the one that would have
caught what the geometry battery cannot see.

One calibration, added after the cross-corpus replication (§7): the
25× figure is relative to *this* corpus. Real corpora themselves spread
~3× on the same probe-depth scale (np@95 18 for MSMARCO passages to 51
for DBpedia under text-embedding-3-large), with Wikipedia-1024 at the
hard end; and the frozen family's later echo-group mechanism, tuned
only against geometric criteria, lands at np@95 10–11 — inside a
factor of two of a real web-passage corpus. The boundary stands, but it
is a corpus-relative boundary, not a universal constant.

---

## 4. Two more mechanisms, and the verdict lottery

Two further campaigns (RC-6/RC-7, 108 arms plus 16 package runs,
`results/R81`–`R88`) found the two mechanisms the earlier arc lacked,
and then measured — at the cost of a failed one-shot — a property of
held-out verification itself.

**Near-duplicates are the density-response mechanism.** A keyed fraction
of rows becoming near-copies of rows elsewhere (depth-one recursion;
random access preserved) moves the G1-vs-n exponent monotonically and
strongly (−0.113 → −0.453 across the gate rate) *without* dragging the
ratio trend — breaking the trade curve §2's campaigns proved unbreakable
by amplitude levers. The mechanism's sign is diagnostic: additive shared
components (topics, chapters) make resolved neighbours *high*-dimensional
and flatten the exponent; resolved near-parallel pairs are
*low*-dimensional and steepen it. Real corpora contain exactly this
structure (quoted and templated passages). Its measured cost: a
depressed ratio span, and a three-constraint pinch (g1, exponent, G1
span) over two knobs whose algebra is now written down (`R85`).

**A thin continuum sheet is the coarse-rank mechanism.** Adding a weak
band-limited random field over per-article latents — a smooth manifold
layer under the cluster arrangement — gives the corpus the coarse
effective rank the shared-vocabulary spectrum could not reach (§2),
with a clean dial (eff rank 121 → 186 across sheet weight). At full
replacement the same field produces the first honest partition scatter
(probe depth 9, same-article fraction 0.61 — real-like anatomy) at the
price of crowding hubs; thin, it is geometry-safe and scatter-free. The
combined configuration holds **eight of ten registered criteria
seed-robustly** — the coarse rank and the density exponent jointly in
band for the first time anywhere (`R88`).

**Then the one-shot returned five of ten — and the miss was in the
dice, not the generator.** Frozen and evaluated once on four fresh
blocks, the configuration's own statistics moved less than seed noise
from their in-sample values; the *bands* moved. The four fresh blocks
happened to be homogeneous strongly-articulated regions, drawing the
narrowest bands in the project's history on four statistics at once
(G1-span band width 0.076, against 0.19 across ten blocks), and the
mandatory contrast gate missed by 0.007 (`results/RC7_VERDICT.md`).
Given the heterogeneity finding (companion draft A §9) — the corpus's density response varies
2.4× across regions — a four-block verdict is a lottery ticket: an
earlier campaign's 8/10 rode a wide draw, this 5/10 a narrow one. The
methodological consequence is registered and binding on future rounds:
**held-out draws must be at least eight blocks, fixed before the
freeze.** Verification against a heterogeneous corpus needs the same
statistical care as the fitting it polices.



## 5. Where generation ends: the admission bar as a memorization detector

The program's final campaigns (`results/R101`–`R104`,
`RC13_VERDICT.md`, `RC14_VERDICT.md`) ran the original pre-registered
battery — including its query-side battery B, which no corpus-side
measurement in seventeen campaigns had exercised — and closed the arc
with its deepest structural result.

**Battery A — every statistic computable from the corpus alone — is
essentially achieved.** Under the registered bands (wider than this
paper's block-derived ones: the original ±20% admits the dims90 ratio
of 1.18 that our stricter protocol recorded as structural), the frozen
family passes the corpus-side battery nearly everywhere, and two
long-standing anomalies dissolved on contact with the original
protocol: the ball-growth heat was a missing-mean artifact (restoring
the corpus mean fixes G2 12/12), and the deconvolved hubness skew
matches at the level (its cell failures are estimator variance).

**Battery B — the same statistics measured for real query vectors
against the synthetic corpus — is bounded away, and the bound is
measurable.** Real queries land in specific micro-neighbourhoods of
the real cloud. A data-free generator can be brought into real's
coordinate system by train-fitted maps — rotation and mean restoration
recover retention from 0.07 to 0.77 and halve the local-dimension
inflation — but the full licensed hierarchy (linear maps, then
compressed-density placement under a declared memorization guard of no
component finer than 32 rows) bottoms out at an inflation of ×2.0–2.6.
Granularity fine enough to go further is, by the guard's own
definition, storage of the data. **Scoped precisely: within the class
of deterministic, byte-reproducible generators using at most compressed
low-order train statistics — the class this benchmark's distribution
requirements mandate — the query-side battery is unpassable, and the
bound is measured at ×2.0–2.6.** Whether richer data-dependent models
(a generative network trained on the train split, say) could close the
gap without what one would want to call memorization is an open
question this measurement sharpens rather than settles: such a model
lies outside the byte-reproducibility constraint that motivates
procedural generation here, and the continuum between "distributional
parameters" and "the data" is exactly what the description-length curve
of §6 is designed to trace. What is established is that
query-side batteries detect data-dependence that no corpus-side
statistic reveals — the property that makes them, in effect,
memorization-sensitivity probes for synthetic corpora.

This is the honest terminus the pre-registration itself anticipated
("if validation fails, the family stops at the seam and says so") —
reached with the reason measured rather than suspected, and with the
sealed test preserved unopened as a matter of record. Read together
with §3, the two boundaries frame what synthetic benchmark corpora
can and cannot be: corpus-side geometry and its density response are
reproducible to registered tolerances by a bit-exact, random-access
generator; the experience of real queries, and the behaviour of real
indexes, retain an irreducible dependence on the data itself. A
benchmark that needs the former has an artifact ready; a benchmark
that needs the latter needs the corpus.

## 6. The description-length curve: the wall is dose-limited, not bits-limited

Section 5 left one continuum untraced: between "distributional
parameters" and "the data" lies a ladder of artifacts of increasing
description length, and one could imagine the ×2.0–2.6 bound being a
resource frontier — that a large enough compressed model of the train
split would close the query-side battery before reaching literal
storage. The closing measurement (R105) traces that ladder directly:
train k-means skeletons at K ∈ {64, …, 65536} components (artifact
size 256 KB → 268 MB) and, as the endpoint, contraction toward the
*literal nearest train row* — the memorization limit, where the
artifact is the entire 1.2 GB train split — each applied to the
rotated, mean-restored candidate at contraction doses λ ∈ {0.20, 0.35}.

The curve is flat. At λ = 0.20 the battery-B core saturates by
K ≈ 1024 (g1@B ×2.44) and never improves beyond ×2.35 — *including at
the memorization endpoint*: replacing a 4 MB mixture with the whole
train set buys nothing. At λ = 0.35 the ladder descends slowly and the
full train set reaches exactly ×2.00 — the floor §5 registered —
while corpus-side cells visibly degrade. No variant of the fourteen
admits (the registered expectation). Two conclusions sharpen the
terminus. First, the bound is **dose-limited, not bits-limited**: what
caps closure is how much displacement toward the data the corpus-side
battery tolerates, not how many train bits the artifact encodes —
description length is the wrong axis, per-row placement information is
the right one. Second, the memorization detector of §5 is calibrated:
even overtly data-anchored corpora at corpus-side-compatible doses
sit at ×2.0, so the admission rule's rejection region covers the
entire continuum from data-free generation to moderate-dose
memorization, failing them all for the same measured reason.

## 7. Cross-corpus replication: the shape is universal, the signal is structural

Every quantitative claim so far is a claim about one corpus and one
encoder. The replication (R107) reruns the identical measurement
protocol on three corpora that vary the two axes independently:
MSMARCO-v2 passages under the same Embed-V3 encoder (different text,
same model), and DBpedia entity abstracts under both OpenAI ada-002
and text-embedding-3-large (different encoder families, 1536-d).

Three results. **First, the profile's shape replicates.** The density
response — local intrinsic dimension falling as corpus density rises —
appears in all four corpora under all three encoders (wiki 26.9→18.3
across the n-grid; MSMARCO 18.7→14.9; DBpedia 33.2→26.4 and
34.9→26.5), as do rank saturation and the contrast rise. The levels,
however, are jointly corpus- and encoder-determined (dims90: 362 wiki
vs 396 MSMARCO at matched encoder; 457 vs 610 for the same text under
the two OpenAI encoders) — the matched-protocol requirement (companion draft A §7) is
not pedantry but the difference between a statistic and a number. One
directional divergence is on record: PCA retention rises with density
on the passage corpora and falls on the entity corpora.

**Second, the battery-B phenomenon replicates where it should and
vanishes where it should.** MSMARCO's held-out queries — rows from far
past a 10M-row cap of a topically ordered stream — experience ×3.46
the local ID of exchangeable holdout rows, matching wiki's ×3.01. The
1M-row DBpedia sets, which have no "far past the cap," show ×1.29 and
×0.97: no signal. Battery B's detector is therefore **corpus-region
non-exchangeability** — placement drift across regions of a large
ordered corpus — which no exchangeable model reproduces, per §5–§6,
without carrying the data itself.

**Third, ANN difficulty is corpus-relative** (§3's calibration): real
corpora spread np@95 18–51 on the R80 scale, and a geometrically
admitted generator sits at 10–11 — below the entire real range, but
within a factor of two of its soft end, not the 25× of the hardest
corpus. Taken together the replication upgrades the paper's central
claims from properties of Wikipedia-1024 to properties of large
embedded corpora as a class, while marking exactly which numbers
(levels, difficulty multiples) must be re-measured per corpus.

## 8. Conclusion

The distributable-benchmark program that motivated this work ends at a
measured seam. On one side, corpus-side geometry — including the
density response that excludes i.i.d. generation — is reproducible to
registered tolerances by a frozen, bit-exact, random-access family; a
per-tier difficulty audit (probe depth against the real band) now
labels any synthetic tier's position honestly. On the other side, the
experience of real queries and the behaviour of real indexes retain a
per-row dependence on the data that no compressed artifact supplies:
the query-side battery bounds every non-memorizing generator at
×2.0–2.6, the bound is dose-limited rather than bits-limited, and the
signal it detects is the region-to-region non-exchangeability of large
ordered corpora. A benchmark that needs corpus-side geometry has an
artifact ready; a benchmark that needs query realism needs the corpus
— and now has the measurements that say exactly why.
