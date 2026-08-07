# Raw count targets are convention-bound; the hub-share law survives

*(Filed under the question "is the ladder's n-axis confounded?" — it is, but
not in the way the first reading of this data claimed. See "Finding,
corrected".)*

Measured 2026-08-07 on the real Cohere Embed-V3 corpus (sampled across the
42 parts, sealed rows excluded by the same `blake2b(i) % 4 == 3` rule the
reference build uses, 3 draws per cell). Driver
[`r13_protocol_check.py`](../harness/rc1/r13_protocol_check.py), raw record
[`r13_protocol_check.json`](r13_protocol_check.json). Nothing was scored, no
gate read, no band touched.

## The question

`r11v2_stage1.measure_counts` draws `min(N_QUERY, len(q_pool))` queries at
**every** ladder n while the corpus is subsampled to n. Retrieval slots per
point are therefore `N_QUERY · k / n`, which falls **8×** across the
registered ladder (25,000 → 200,000).

Round 11 read its central diagnosis off exactly that axis: real holds its
count-skew level while its absolute count maxima fall with n (42 → 9.4 at
k = 10), interpreted as *real hub mass being a population law that
re-expresses at every sampling scale, which fixed owners cannot imitate*.
That interpretation drove the round-12 architecture and part of round 13's.

## The measurement

Real, same rows and same seeds, under two protocols:

- **FIXED** — `nq` constant at every n (the current protocol).
- **SCALED** — `nq ∝ n`, holding slots per point constant.

| | k = 10 | k = 30 |
|---|---|---|
| count_max drift/decade, FIXED | **−0.489** | **−0.532** |
| count_max drift/decade, SCALED | **+0.227** | **+0.240** |
| gap | −0.716 | −0.772 |
| S_k drift/decade, FIXED | +0.242 | +0.087 |
| S_k drift/decade, SCALED | +0.039 | +0.080 |
| gap | +0.203 | +0.007 |

Per-n detail at k = 10:

| n | FIXED count_max | FIXED zero-frac | SCALED count_max | SCALED zero-frac |
|---|---|---|---|---|
| 12,500 | 17.3 | 0.28 | 3.7 | 0.82 |
| 25,000 | 13.0 | 0.50 | 5.3 | 0.83 |
| 50,000 | 9.0 | 0.69 | 5.0 | 0.83 |
| 100,000 | 6.3 | 0.83 | 6.3 | 0.83 |

## Finding, corrected

An earlier reading of this table stated that the falling count maxima *are*
a query-budget artefact. That overstated the case, and the correction
matters more than the original claim.

**The raw statistic is protocol-dependent; the underlying corpus property is
not.** `count_max` mixes two terms: the share of retrieval mass the top hub
captures, and the size of the query budget being shared out. Re-expressing
the same measurement in the budget-invariant form — hub **share**,
`count_max / (nq·k)` — separates them:

| | k = 10 | k = 30 |
|---|---|---|
| hub-share slope/decade, FIXED | −0.489 | −0.532 |
| hub-share slope/decade, SCALED | −0.773 | −0.760 |

**Both protocols agree in sign.** Real's top hub captures a steadily smaller
share of retrieval mass as the corpus grows, under either convention. That
is a corpus property, and it is exactly what round 11 asserted: hub mass
re-expresses as a population law rather than sitting with fixed owners.
**Round 11's diagnosis is confirmed, not overturned.**

What *is* artefactual is the raw number and the raw statistic's direction.
Under the current protocol raw maxima fall at −0.489/decade; under a
constant budget they rise at +0.227, because a growing query budget
(+1.0/decade) more than offsets a shrinking share. A generator calibrated to
reproduce "−0.49/decade in raw count_max" is being calibrated to a quantity
that has no meaning without its budget convention attached, and the two
protocols disagree on the share slope by a factor of 1.5 (−0.49 versus
−0.77), so the magnitude of any such target is convention-bound too.

The zero-fraction column shows the budget term directly: 0.28 → 0.83 under
FIXED purely because slots per point fall, pinned at 0.83 under SCALED.

**The rule this licenses.** Define ρ = nq·k/n, retrieval slots per point.
Any statistic compared across a varying n must either hold ρ constant or be
expressed in a ρ-invariant form. Raw counts and raw maxima are neither.
Hub *share* is ρ-invariant by construction and is the form targets should
take.

## Limitation, stated

The SCALED arm at the low-n end runs at 250–500 queries, so its count maxima
(3.7, 5.3) sit near the counting floor. That is precisely where the two
protocols disagree most on the share slope (−0.49 versus −0.77), so the
1.5× magnitude gap is the number least to be trusted here; the agreement in
*sign*, which is what carries the finding, does not depend on those cells.
A confirmation run at a uniformly higher query budget would settle the
magnitude. This run used `nq` ≤ 2,000 against the registered
`N_QUERY = 10,000`, on a ladder topping out at 100,000 rather than 200,000,
to stay inside the thermal budget of a shared box.

## Consequence for round 14

[`PREREG_ROUND14.md`](PREREG_ROUND14.md) §3 made this check a **precondition**
on any further fitting. It is **partly** satisfied: the corpus law round 11
identified is real, so round 14's premise survives, but the targets are
stated in a convention-bound form and must be restated.

Concretely, before round-14 search begins:

1. Re-express count targets as hub **share**, `count_max / (nq·k)`, which is
   ρ-invariant.
2. Record ρ and the query-budget convention in the spec, rather than letting
   it be an emergent property of `min(N_QUERY, len(q_pool))`.
3. Re-read round 11's 17-point infeasibility result in share terms before
   any of its numbers are quoted again. Its qualitative conclusion is
   expected to survive; its magnitudes are convention-bound.

P-14B's threshold (|Δ S_k slope| ≤ 0.05/decade) is unaffected in form — S_k
is already a normalized statistic — but the k = 10 measurement shows S_k
carries a protocol component too (+0.242 versus +0.039), so its target
requires the same treatment.
