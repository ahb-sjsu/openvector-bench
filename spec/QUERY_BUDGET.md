# Query budget and hubness statistics (normative)

Retrieval-count statistics are not properties of a corpus. They are
properties of a corpus **measured under a query budget**. This document
fixes the convention so that a target quoted in one place means the same
thing in another, and so that comparisons across corpus size measure the
corpus rather than the measurement.

It exists because they did not. See
[`../results/R13_PROTOCOL_CHECK.md`](../results/R13_PROTOCOL_CHECK.md).

## 1. The budget parameter

For a cell measured with `n_query` queries at depth `k` over `n_base`
points, define retrieval slots per point

    rho = n_query * k / n_base

`rho` is exactly the mean retrieval count per point. Any statistic compared
across a varying `n_base` **must** either hold `rho` constant or be
expressed in a `rho`-invariant form. Raw counts and raw count maxima are
neither.

`rho` is reported on every measured cell. A number quoted without it is not
a target.

## 2. Three forms, and which claim each supports

| form | definition | invariant to budget | isolates structure | use for |
|---|---|---|---|---|
| `count_max` | busiest point's count | no | no | continuity with prior results only |
| `hub_share` | `count_max / (n_query * k)` | yes | no | comparing across budgets |
| `hub_excess` | `count_max / null_max` | yes | **yes** | any claim about the corpus |

`null_max` is the largest count reachable with **no hub structure at all**:
the largest `c` such that at least one of `n_base` independent
Poisson(`rho`) points is expected to reach it. It is a ceiling that moves on
its own as the ladder moves, and it moves a lot.

`hub_excess = 1.0` means the busiest point is no busier than chance makes
it. Values above 1 are structure.

## 3. Why the raw form fails, measured

On the committed round-11 real reference (`n_query` = 10,000 fixed across
the ladder), the raw ladder slope decomposes as

| k | raw slope | of which null ceiling | genuine hub structure |
|---|---|---|---|
| 10 | −0.728 | −0.399 | **−0.329** |
| 30 | −0.729 | −0.538 | **−0.191** |
| 100 | −0.746 | −0.635 | **−0.112** |

**Roughly half the apparent thinning at k = 10, and 85% of it at k = 100, is
the null ceiling falling rather than the corpus changing.** A generator
fitted to reproduce the raw slope is being asked to reproduce the
measurement's own arithmetic.

The measured hub excess itself:

| k | n=25,000 | 50,000 | 100,000 | 200,000 |
|---|---|---|---|---|
| 10 | 3.00× | 2.48× | 1.77× | **1.57×** |
| 30 | 3.82× | 3.58× | 2.88× | 2.64× |
| 100 | 4.45× | 4.60× | 4.36× | 3.50× |

At the top of the registered ladder at k = 10, real's busiest point is only
**1.57×** what pure chance produces. That cell carries very little hub
signal, and any gate reading it is mostly reading noise. This is a property
of the ladder's fixed budget, not of real data: at `n_base` = 200,000 with
10,000 queries, `rho` = 0.5, so most points are never retrieved at all.

## 3a. The maximum is the wrong reduction at low occupancy

`count_max` is a single draw, so its variance does not shrink with corpus
size. `tail_share` — the mass captured by the busiest one percent — sums
thousands of points instead. Against an identical planted 1% hub population
(measured 2026-08-07, 5 seeds, n = 200,000):

| rho | tail excess | max excess | tail s.d. | max s.d. | tail SNR gain |
|---|---|---|---|---|---|
| 0.5 | 1.29 | 1.87 | 0.005 | 0.163 | ~11× |
| 1.0 | 1.61 | 2.15 | 0.007 | 0.094 | ~9× |
| 2.0 | 2.06 | 2.60 | 0.008 | 0.045 | ~8× |
| 4.0 | 2.63 | 2.95 | 0.012 | 0.121 | ~9× |

The maximum reports the *larger* excess — it is sensitive to exactly the
extreme tail where hubs land — but its seed-to-seed spread is 10–30× wider.
Per unit of noise the tail wins by roughly an order of magnitude, and a gate
is a statement about signal per unit of noise.

**A better statistic does not rescue a starved budget.** Both statistics
lose power as `rho` falls: the same relative structure reads 2.63× at
`rho` = 4 and 1.29× at `rho` = 0.5, because Poisson's own tail is
proportionally fat when occupancy is low. The registered ladder's top cell
at k = 10 runs at `rho` = 0.5. It needs more queries, not a cleverer
reduction.

## 3b. G6 needs the same treatment, and the correction runs the other way

G6 is the skewness of the count vector, and it must pass in **every** cell
under the admission rule. A Poisson(`rho`) count vector has skewness exactly
`1/sqrt(rho)`, so G6's null term **rises** as occupancy falls — the opposite
direction to `count_max`'s ceiling. On the round-11 real reference:

| k | n=25,000 | 50,000 | 100,000 | 200,000 |
|---|---|---|---|---|
| 10 | 3.19× | 2.14× | 1.58× | **1.27×** |
| 30 | 6.05× | 4.01× | 2.66× | 1.85× |
| 100 | 11.07× | 7.95× | 5.34× | 3.54× |

At k = 10, n = 200,000, real's hubness is **1.27×** the structureless
expectation: the measured `s_k` of 1.79 sits against a null of 1.41, so
that cell is 79% null. Because the gate is a ratio and the null term depends
only on `rho` — identical for candidate and reference — both sides are
pinned near the same floor and **R → 1 regardless of hub structure.** The
gate does not merely lose power there; it approaches a free pass.

**This unifies both of round 11's observations.** Raw `s_k` looked
n-stable (+0.056/decade at k = 10) while raw `count_max` fell sharply. In
null-corrected terms they are one fact: hub structure declines with n, at
−0.443/decade by the skew route and −0.329/decade by the maximum route. The
apparent difference between the two statistics was two null terms moving in
opposite directions.

**The invariant form.** Model a point's count as Poisson(`rho`·w) with w its
attractiveness under the query measure. Then `Var(c) = rho + rho² Var(w)`
and `mu3(c) = rho + 3 rho² Var(w) + rho³ mu3(w)`, so skew(w) is recoverable
and is a property of the corpus and query measure alone.
`attractiveness_skew` does this deconvolution. Verified on a fixed corpus
measured at `rho` ∈ {0.5, 1, 2, 4}: raw `s_k` moves 2.46 → 5.59 while the
estimator holds 10.02 → 9.84 against a true 9.85.

An intermediate attempt, `s_k * sqrt(rho)`, is **not** invariant — it
over-corrects, moving 1.74 → 11.19 on that same data — and was removed
rather than shipped.

## 4. Rules

1. **Report `rho` on every cell.** A count statistic without its budget is
   not interpretable.
2. **State corpus claims in `hub_excess`.** Claims about how hub mass
   behaves with corpus size are corpus claims.
3. **State workload claims in `hub_share` or raw counts,** and say so. "How
   concentrated does retrieval get when a fixed query load meets a growing
   corpus" is a legitimate and different question.
4. **Do not compare cells whose `rho` differs** unless the statistic is
   `rho`-invariant.
5. **Flag cells whose excess is below 2.0** as low-signal. They are
   dominated by the null ceiling and should not carry a gate on their own.
6. **Prefer `tail_excess` to `hub_excess` for gates.** Same null discipline,
   roughly 10x the signal-to-noise.
6a. **State G6 as `attractiveness_skew`.** Raw `s_k` mixes structure with
   occupancy and its null term rises as the budget falls, which makes the
   per-cell gate approach a free pass at the top of the ladder.
7. **Keep `rho` >= 2 on any cell that carries a gate.** Below that no count
   statistic has usable power, whatever its form. For the registered ladder
   at k = 10 this means `n_query` >= 0.2 * `n_base` — the current fixed
   10,000 does not meet it above n = 50,000.

## 5. Implementation

`openvector_bench.hubness` provides `rho`, `hub_share`, `poisson_null_max`,
`hub_excess`, and a `count_stats` that returns all forms together so a
caller cannot select one by accident. Tested in `tests/test_hubness.py`,
including that a structureless Poisson corpus reads `hub_excess` ≈ 1.

Re-derived targets for the existing real reference:
[`../results/r14_hub_targets.json`](../results/r14_hub_targets.json). That
file is a re-expression of the committed round-11 measurement, not a new
measurement — the budget was recoverable from `count_mean` exactly, since
`count_mean = rho` by construction.
