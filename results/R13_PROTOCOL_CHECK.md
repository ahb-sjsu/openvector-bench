# The ladder's n-axis is confounded: falling count maxima are a query-budget artefact

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

## Finding

**The direction reverses.** Under the current protocol real's count maxima
*fall* with n; under a constant query budget they *rise*, consistently at
both k. The falling maxima that round 11 attributed to real's hub mass
re-expressing under subsampling are, in the measured part of the ladder,
a consequence of spending a fixed number of queries over a growing corpus.
The zero-fraction column makes the mechanism plain: under FIXED it climbs
from 0.28 to 0.83 purely because slots per point fall, while under SCALED it
is pinned at 0.83 throughout.

**The skew claim splits by k.** At k = 30 the S_k drift is essentially
protocol-independent (+0.087 versus +0.080), so round 11's level-stability
observation survives there. At k = 10 most of the apparent growth is
protocol (+0.242 versus +0.039).

## What this does and does not overturn

**Does not overturn:** the *structural* argument that a generator planting a
fixed set of hub rows behaves differently under subsampling than a
population law does. That is an argument about mechanisms, independent of
this measurement, and it stands.

**Does overturn:** the *empirical* claim that real exhibits falling count
maxima as a corpus property, and any calibration target derived from it. A
candidate penalised for failing to reproduce a −0.49/decade fall was
penalised for failing to reproduce the measurement protocol. Round 11's
17-point infeasibility result and the trade-off curve it reported were
measured against targets carrying this component.

**Neither protocol is wrong, but they answer different questions.** FIXED
models a realistic deployment — a fixed query workload against a growing
corpus — and is a legitimate thing to benchmark. SCALED isolates corpus
structure from workload size. The error was reading a FIXED-protocol
measurement as a statement about corpus structure.

## Limitation, stated

The SCALED arm at the low-n end runs at 250–500 queries, so its count maxima
(3.7, 5.3) sit near the counting floor and its drift estimate is
correspondingly weak. The sign reversal is large and consistent across both
k, which is hard to attribute to that noise, but a confirmation run at
higher query budget throughout would settle it. This run used `nq` ≤ 2,000
against the registered `N_QUERY = 10,000`, on a ladder topping out at
100,000 rather than 200,000, to stay inside the thermal budget of a shared
box.

## Consequence for round 14

[`PREREG_ROUND14.md`](PREREG_ROUND14.md) §3 made this check a **precondition**
on any further fitting. The precondition is not satisfied: the count targets
carry a protocol component. Before round-14 search begins, the count targets
should be re-derived under an explicitly chosen and documented protocol, and
the choice recorded in the spec rather than inherited from the harness. Any
claim about n-dependence of hub mass — in either direction — must state its
query-budget convention alongside it.
