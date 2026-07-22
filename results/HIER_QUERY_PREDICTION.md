# Pre-registration — the query-modelled family (round 7)

**Registered before the gating run** (the discipline of `PREREG_RC1.md`). Train/validation
only; sealed 25% never loaded; not RC-1 admission. Family:
[`openvector_bench/generator_search.py`](../openvector_bench/generator_search.py)
(`hier_query_corpus`, `HIER_QUERY_PARAMS`).

**Disclosure — this registration follows an extensive diagnosis, all of it reported.**
Round 6 left G2 ball-growth at 0.14×. Seven Atlas screening probes (single seed, n=8000,
all off the round-6 winner) preceded this registration:

1. Per-point radius spectrum: **G2 unmoved** (the exploratory `hier_multiscale_corpus`,
   kept in the package as a probe record).
2. Per-cluster density equalization alone: window 2.14→2.03, G2 unmoved.
3. Near-duplicate injection: window widens, G2 *worse*.
4. Fewer/bigger clusters: window →1.65, G2 0.20×, G6 halves.
5. **Homogeneous substrate** (mild size_tail + equalize + big clusters): window →1.10,
   **G2 →0.58×**, but G6 →0.18× and a global mean-offset knob does nothing.
6. Gentle per-point tilt and in-patch sub-clusters: G6 unmoved on that substrate.
7. **Query concentration: G6 0.19×→2.20× as `query_tail` 0→2.5, window stays ~1.10,
   G2 improves to 0.65×.** The controlling mechanism.

The load-bearing diagnosis (`diag_hubs.json`, real corpus on Atlas, train/val rows):
**real's base→base reverse-NN skew is only ≈1.5 (max count 78, density-driven, hubs' d10
just 8% under population) — the battery-B G6 target of 6.83 lives in the QUERY MARGINAL.**
Real queries concentrate on popular regions; same-distribution synthetic queries make
near-Poisson counts, so corpus-side mechanisms could only fake G6 with wrong-anatomy
super-hubs (round 6's winner: max count 369, extreme centrality) whose density contrast is
exactly what widened the d10 window and pinned G2. G2 and G6 were never in tension — they
live in different layers (metric scale vs query measure) and were bound by a shared
mechanism. The family therefore keeps the corpus homogeneous (G2) and moves the hubness
knob into a Zipf query model (G6), with queries still drawn from the same instance — the
round-3 same-instance fix is preserved; only the cluster *preference* of the query draw is
reweighted, which is precisely the asymmetry real query workloads have.

## Registered predictions

**P1 — the six-gate joint point (make-or-break).** The search finds a single point with
**G1, G2, G3, G6, G7, G8 all within [0.5, 2.0]×** — adding G2, round 6's wall, to the
five-gate joint match. Probe readings (G2 0.65×, G6 tunable through 1×, G1 0.76×, G7
0.55×, G3 1.13×, G8 0.79–0.98×) say the region exists; the registered bet is that it is
*jointly* reachable. *Falsified if* every shard's best point has at least one of the six
outside [0.5, 2.0]×.

**P2 — anatomy, not just the number.** At the best point, the corpus-side (base→base)
reverse-NN skew stays **below 3** (real ≈1.5; round-6 winner ≈7.0 with max count 369) —
i.e. the family reproduces G6 with real's *query-side* mechanism, not corpus super-hubs.
This is the first round where the falsifier looks behind a gate at the structure producing
it. *Falsified if* the best point's base→base skew exceeds 3: that would mean the search
rediscovered corpus hubs to game G6.

**P3 — the honest risk: G8 pays for the query model.** In the probe, G8 fell 0.98×→0.74×
as `query_tail` rose (concentrated queries evaluate PCA retention exactly where the
colouring's dominant modes live). If G8 and G6 bind through `query_tail` the way G6 and G3
bound through the hierarchy, the six-gate point may exclude G8 — reported as a P1 miss,
with the round-8 direction being a popularity-aware colouring (protect the PCA subspace on
popular clusters).

## Protocol

NRP Nautilus swarm, 12-shard Indexed Job (`FAMILY=hier_q`, `N_EVALS=40`/shard, shard 0
anchored at defaults), n = 8000 + 1000 same-instance held-out queries (the family's own
Zipf-weighted query block), battery B, k = 10, target = `target_n8000.json`. Best point
re-measured with the full 8-gate battery on 3 seeds **plus the P2 anatomy check**. Result
to `results/GEN_ROUND7_QUERY.md`.
