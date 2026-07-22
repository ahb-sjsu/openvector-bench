# The query-coupling artifact: the G1 "wall" was substantially a measurement protocol effect

**Discovered 2026-07-22 (screening, n=8–16k, dim=1024); the motivating anomaly for
[`spec/NORMAL_FORMS.md`](../spec/NORMAL_FORMS.md) and the origin of the same-instance
query convention used by every family from round 7 on.** Driver scripts were session
scratch; the decisive numbers are reproduced below. Companion measurement:
[`diag_target.json`](diag_target.json) (Atlas, real Cohere wiki1024 vs Gaussian null —
the file cited by `RC1_ROUND2_CANDIDATE.md` and the round-9 family comments).

## The observation

Rounds 1–4 all died on G1 ≈ 300–420 (~5× real's 61) and the campaign briefly concluded
the wall might be fundamental (three falsified families: EC, stratified flags, sharded
codebooks). It is not. On the real fitness harness, the *same* `concentration_corpus`
reads:

| query protocol | G1 (two-NN) |
|---|---:|
| queries from an **independent generator seed** (fresh structural realization) | **339.9** |
| queries sharing the **same structural realization** (fixed backbone, independent content seed) | **71.9** |
| real embeddings, real held-out queries | 59.4 |

Independent-seed queries land on a *different* random manifold realization: every
query's nearest base points are essentially arbitrary, `r2/r1 → 1`, and the two-NN
estimator reads ambient. Real queries read low because they lie on the one real
manifold. **A synthetic workload's query process must share the corpus's structural
realization** — the corpus-only view of a benchmark is not merely incomplete, it is
*wrong* about measured difficulty. This is `spec/NORMAL_FORMS.md`'s failure to
preserve the shared support `𝓜`, observed in the wild.

## The companion diagnosis (why real reads ~60 at all)

[`diag_target.json`](diag_target.json), real vs Gaussian null at identical n=16k:

| metric | real | gaussian null |
|---|---:|---:|
| id_twonn (trimmed) | 59.4 | 309.2 |
| id_twonn (untrimmed) | 42.2 | 236.8 |
| **local participation ratio** (K=100) | **50.5** | **90.4** |
| base→base NN distance, 1% quantile | 0.375 | 1.304 |
| base→base NN distance, median | 0.860 | — |

Two mechanisms, ranked: (1) **genuine low-dimensional local structure** — real
neighbourhoods concentrate near ~50-dim subspaces (the bulk effect; the null has no
counterpart at any query protocol, so *its* G1 ≈ 309 is real); (2) a **fine-scale
near-duplicate tail** (1% of NN pairs at cosine ≈ 0.93) — secondary for the trimmed
level, but the short-range μ-ladder later shown (round 9, three independent probe
falsifications) to be what pins G1 *flat in n* and shapes hub anatomy.

## Consequences, as adopted

1. **Same-instance queries** — the `QUERY_FRAC` tail-block convention
   (`hier_query_corpus` and descendants): base and query rows are drawn in one call
   from one structural realization, with separate marginals. The query generator is
   part of the candidate and registered as such (`RC1_ROUND2_CANDIDATE.md`).
2. **Fitness battery-A holdout fixed** (`measure_corpus`): battery-A queries were
   sampled from the searched base itself — self-match at distance 0 collapsed every
   neighbour diagnostic (id ≈ 0.1). Queries are now excluded from the searched rows.
3. **Harness battery-A uniform sampling** — the registered decision of
   `RC1_ROUND2_CANDIDATE.md` finding 3 (first-rows holdout inherits topical row
   ordering) is now implemented in `geometry.py` (this commit; the round-9 note's
   `corpus_geometry.py` reference was to Atlas session scratch).
4. **Caveat on prior verdicts:** the G1 ratios in `EC_FALSIFICATION.md`,
   the stratified screen, and `CODEBOOK_PROBE.md` were measured under
   independent-seed queries. Their *mechanism* falsifications stand (each failed on
   its own registered terms; ec_ff's duplicate collapse and the codebook's flat
   G1-vs-`d_latent` response are protocol-independent), but their G1-vs-real ratios
   overstate the gap and should not be quoted as evidence about those constructions'
   intrinsic geometry under a shared-realization protocol.

## Status

Superseded as a *problem* — G1/local geometry matched from round 7 on; the campaign's
open fronts moved to hubness growth and the graded short-range ladder
([`ROUND9_PROBES.md`](ROUND9_PROBES.md)). Kept as the record of why the query process
is a first-class part of every workload object in this repository.
