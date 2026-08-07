# Pre-registration — Round 14: freeze the corpus, search the query model (DRAFT v1)

**Status: DRAFT ⚪ — not frozen.** Drafted 2026-08-07 after round 13 closed
([`R13_STAGE1_RESULT.md`](R13_STAGE1_RESULT.md), `19b5233`). Naming and
freezing are the author's calls. Bands are those of RC-1 §5, untouched here
and not adjustable by anything downstream of this draft.

## 1. What round 13 licenses

Round 13 measured, on the real corpus, that **corpus-side local geometry is
nearly irrelevant to which points get retrieved once query exposure is
known**. A supervised partition over eight latent features beats the same
procedure on `query_mass` alone by at most 1.20× at K = 12 and 1.30× at a
32-leaf budget (registered threshold 1.25× on ≥ 3 of 4 response variables;
measured 0 of 4). Density, three neighbour radii, radius slope, local
intrinsic dimension and anisotropy together add almost nothing.

This retro-explains rounds 9, 11 and 12. Each hunted a **corpus-side**
mechanism for hub mass — near-duplicate cloud ladders, planted
`local_centers`, Zipf branch heads, a multiplicative cascade — and each
failed. They were asking the corpus to produce from geometry a phenotype
that real data does not produce from geometry. The mechanism was not
mistuned; it was in the wrong layer.

It also relocates, rather than answers, the campaign's deepest problem. The
sampling-operator finding (rounds 9 and 11: real hub mass re-expresses at
every scale, fixed owners cannot) is untouched by round 13 and now applies
to the query model instead of the corpus. **A query model that is not
subsample-covariant will fail exactly as the corpus mechanisms did**, and
nothing yet shows that any query model has that property. §4 registers it as
a first-class prediction rather than an assumption.

## 2. The change

Split the generator along the **corpus/query** seam rather than the
corpus-mechanism seam rounds 11 and 12 tried:

- **Corpus family: frozen.** Take round 8's winning point — the campaign's
  best measured operating point, six gates in [0.5, 2.0]× with anatomy in
  band on three fresh seeds — and freeze its corpus parameters. The corpus
  is responsible for the geometry gates only: G1 intrinsic dimension, G3
  effective rank, G4 spectrum, G7 local-dimension spread, G8 PCA retention.
  Round 13 says nothing about these and they remain corpus-side properties
  that must be matched the hard way.
- **Query model: the whole search budget.** The retrieval gates (G2 ball
  growth, G6 hubness) and the anatomy guard are the query model's
  responsibility. It is fitted as an object in its own right, against the
  measured relationship between query mass and corpus position, not as a
  Zipf exponent over corpus rows.

The anatomy falsifier (`bb_skew` band, round 8) stays in force throughout.
Round 7 caught an optimizer gaming G6 with corpus super-hubs; nothing here
relaxes that guard.

## 3. Precondition — the ladder's n-axis must be clean

`measure_counts` draws a **fixed** query count at every ladder n while the
corpus is subsampled to n, so retrieval slots per point fall 8× from
n = 25,000 to n = 200,000. Round 11's diagnosis was read off that axis.
[`r13_protocol_check.py`](../harness/rc1/r13_protocol_check.py) measures real
under the current protocol and under a constant-slots-per-point protocol.

**No round-14 fitting begins until that result is in.** If the two protocols
disagree materially, the count targets themselves are partly a protocol
artefact, and re-registering targets comes before any search. This is a
precondition, not a prediction.

**Result (2026-08-07): the precondition is NOT satisfied.** See
[`R13_PROTOCOL_CHECK.md`](R13_PROTOCOL_CHECK.md). The count-maximum drift
*reverses sign* between protocols — −0.49/decade under the current fixed
query count, +0.23/decade at constant slots per point, consistently at
k = 10 and k = 30. Round 11's falling count maxima are, over the measured
ladder, a consequence of spending a fixed query budget over a growing
corpus. The S_k level claim survives at k = 30 (+0.087 versus +0.080) but
not at k = 10 (+0.242 versus +0.039).

Therefore round 14 acquires a stage 0 before anything else: **re-derive the
count targets under an explicitly chosen, documented query-budget
convention, and record that convention in the spec rather than inheriting it
from the harness.** Until that is done, P-14B's subsample-covariance
threshold has no trustworthy target to be measured against, and it is P-14B
that this round exists to test.

## 4. Registered predictions

- **P-14A (query-model sufficiency).** With the corpus family frozen at
  round 8's point, a fitted query model brings **G2 and G6 both into
  [0.85, 1.15]×** on ≥ 3 fresh seeds while the geometry gates G1, G3, G4,
  G7, G8 stay within the band they held at freeze, and `bb_skew` stays in
  its anatomy band. Claim under test: the corpus/query split is sufficient
  to reach admission on the retrieval gates without further corpus surgery.
- **P-14B (query-model subsample covariance).** The fitted query model's
  count statistics hold their **level** under the grid's own sampling
  operator: |Δ S_k slope| ≤ 0.05/decade at every k across the full ladder,
  with the level in band at every cell. Claim under test: the query model
  carries hub mass as a population law rather than as fixed interrogation
  targets. **This is the prediction most likely to fail**, because it is the
  same property that defeated every corpus-side mechanism, and it is
  registered separately so that a P-14A pass cannot disguise a P-14B fail.
- **P-14C (geometry is not silently paid for).** Freezing the corpus and
  searching only the query model leaves the geometry gates unmoved beyond
  draw noise: each of G1, G3, G4, G7, G8 changes by ≤ 0.05× from its frozen
  value across the whole query-model search. Claim under test: the two
  layers are as independent in the generator as round 13 measured them to be
  in real data.

## 5. Failure clauses

- **P-14A fails** → the retrieval gates are not reachable from the query
  model alone at this corpus point. Report which gate resists and at which
  k; that localizes whether the residue is ball growth or hubness, which are
  different mechanisms. Do not unfreeze the corpus inside the round.
- **P-14B fails** → the sampling-operator problem is a property of the
  *object*, not of any one layer: it defeated corpus mechanisms in rounds 9
  and 11 and defeats query mechanisms here. That is the strongest available
  evidence for the capacity conjecture and it is the finding, not a setback.
  Report and stop; no third layer is invented to carry hub mass.
- **P-14C fails** → the layers interact in the generator despite being
  nearly independent in real data. The interaction surface is then the
  object; measure and report it rather than tuning through it.
- Bands are not adjusted under any clause. The corpus does not unfreeze
  under any clause.

## 6. Ordering

0. **Precondition:** protocol check result read and, if needed, targets
   re-registered. No fitting before this.
1. Freeze the round-8 corpus point; measure and record all five geometry
   gates plus `bb_skew` at freeze, on three seeds. These are the P-14C
   reference values.
2. Query-model search against G2, G6 and the anatomy guard only.
3. Ladder-scale subsample-covariance measurement of the winner (P-14B),
   under the grid's own operator, ≥ 2 draws per cell and 5 for a freeze
   candidate.

## 7. What is deliberately not attempted

The multiplicative-cascade proposal from the round-12 close is **not** part
of this round. It is a corpus-side mechanism, and round 13 measured that
corpus-side mechanisms are the wrong layer for hub mass. If it is built
later, its natural role is as a subsample-covariant *density field* for the
geometry gates, and it must clear a presence gate at ladder scale before any
claim rests on it — the r12 cascade failed exactly that check.

The round-13 anti-hub taxonomy is likewise not an admission gate. It failed
its blindness half (G6 is not blind to it), so it stands as a descriptive
diagnostic — useful for explaining *why* a candidate's lower tail is wrong,
with the measured caveat that lower-tail statistics depend on query budget.
