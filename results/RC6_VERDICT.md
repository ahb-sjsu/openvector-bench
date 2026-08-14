# RC-6: one kill, one discovery — and the geometric frontier moves

**Registered close, no freeze, no one-shot spent.** Four harness sweeps
(64 arms, `R81`–`R84`, drivers `harness/rc1/fam2a-d.py`, raw
`results/r81-84.txt`) against `RC6_PLAN.md`'s pre-registered predictions.
Every arm carried the full geometric panel AND the R80 IVF panel — the
first campaign judged on both.

## P1 (partition scatter): the kill fires, in three forms

The Zipf topic ladder moves nprobe@95 — the first mechanism in any family
to move it at all: 2 → 8 → 69 → 221 monotone in dose (`R81`), straddling
real's 47–50. But every composition that reaches scatter breaks geometry,
and every composition that preserves geometry loses scatter:

1. **Boosted-rare** (IDF-weighted rare directions, `R81`/`R83`): np95
   44–150 achievable only with g1 11.6–13.7, g8 0.65–0.70, g4 508–536,
   trend ~1.0 — loud outlier components, nothing like real.
2. **Energy-conserved** (fine amplitude traded down, `R82`/`R83`): the
   damage is structural, not variance-budget; unchanged.
3. **Ambient-weak** (K = 16–64 small flat topics, denser sharing,
   weakened segment dominance, `R84`): np95 = 2 in all 16 arms, same-
   article fraction pinned at 0.87 — weak distributed bonds never enter
   the top-10 — while g1exp still flattens.

Registered kill condition met: nowhere in 64 arms does np95 exceed 3
with the mandatory trio intact. **Additive topic components cannot
scatter partitions at geometry-compatible amplitudes.** The diagnosis
for any RC-7: the family's coarse structure is discrete generative
clusters, which k-means recovers by construction; real's slow ~50-cell
recall climb is the signature of neighbourhoods straddling the arbitrary
boundaries a partitioner draws on an **unclustered continuum**. Scatter
plausibly requires replacing the nested-cluster arrangement with a
smooth coarse manifold — no cells to recover — not adding components to
a clustered one.

## P2 (density response): confirmed, and it beats the frontier

The **near-duplicate ladder** (`R82`) — a gated row becomes a keyed
near-copy of a row elsewhere (depth-1 recursion, random-access clean) —
does what every RC-4 lever could not: g1exp responds monotonically
(−0.113 → −0.453 across p_dup 0–0.30) **without dragging the trend**,
because resolved near-parallel pairs are low-dimensional structure,
where additive bonds (and `R81`'s topics) raise the TwoNN reading.
The trend↔g1exp trade curve is broken.

**B1 (frozen D12 + p_dup 0.05, α 0.95) is the best geometric
configuration ever measured**: 9 of 10 harness flags — g1 15.53, g5
1.381, g6 1.782, g8 0.739, trend +0.401, g1exp −0.157, rspan +1.12,
gspan −0.301 all IN — with only g3 (harness-noisy; package runs ~+30)
and g4 out. It exceeds the RC-3 frontier (which had g1exp robustly out).
Recorded as the standing candidate; **not frozen**, because `RC6_PLAN`
Phase D's registered bar required the ANN panel in band as well, and
np95 remains 2. The bar is not lowered after the fact.

## Standing

* Frozen deliverable: unchanged (RC-3 D12, `e8423665…`).
* Standing candidate for a future geometric-only round: D12 + near-dup
  ladder (p 0.05, α 0.95), pending package port, fidelity, multi-seed.
* Open problems, now ranked: (1) partition scatter — architecture-level,
  the continuum-arrangement hypothesis above; (2) g4 — unchanged from
  RC-5; (3) the dup dose's g1 cost curve bounds p below ~0.08.
* Fresh blocks and the sealed set: untouched.

## Budget

64 arms (A/B/C/D 16 each); the NRP watchdog killed the D-sweep twice
(long low-utilization hashing kernels) — it completed on Atlas GPU 1;
no real blocks consumed.
