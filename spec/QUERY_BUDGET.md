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
5. **Flag cells whose `hub_excess` is below 2.0** as low-signal. They are
   dominated by the null ceiling and should not carry a gate on their own.

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
