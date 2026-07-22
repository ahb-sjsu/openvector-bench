# Pre-registration — WP5-lite: does matched geometry+anatomy transfer to matched ANN behavior?

**Registered before any run.** No index has been built on any of these corpora at the
time of writing; no screening smokes exist for this experiment. Train/validation rows
only; the sealed 25% is never loaded; this is not RC-1/RC-2 and touches neither. This
is the first experiment in the campaign that runs an actual ANN system rather than
exact-kNN geometry — the opening test of `spec/NORMAL_FORMS.md` Objective B (decision
ladder Level 2 → 3) at the candidate's fitting scale.

**The question.** The Bond Metric paper establishes that scalar gates underdetermine
anatomy. The Normal Forms programme claims the converse direction has force: that
gates *plus anatomy* are (approximately) behaviorally sufficient — two workloads
matching on them should present the same operational problem to an ANN index. This
experiment tests that claim where the round-8 candidate actually matched
(n = 8k–16k), with a discrimination control (null) and an anatomy-mismatch control
(the round-6 winner: same scalar G6, super-hub anatomy).

## Corpora (all n = 16,000 base + 1,000 queries, dim 1024, unit-normed)

| tag | source | role |
|---|---|---|
| `real` | wiki1024 non-sealed rows, 3 subsamples; queries.npy | target (subsample spread = noise floor) |
| `rd8` | `hier_query_corpus` at the round-8 registered point (winning-shard knobs, `gen_round8_anatomy.json`), 3 instance seeds; its registered query block | matched gates + matched anatomy |
| `rd6` | `hier_coloured_corpus` at the round-6 winner (`gen_round6_coloured.json`), 3 instance seeds; held-out same-instance rows as queries | anatomy-mismatch control (G6 via super-hubs) |
| `null` | `null_gaussian` on the real rows' scale, 3 seeds; held-out null rows as queries | discrimination control |

## Systems and fixed grids (declared here; no per-corpus tuning permitted)

- **HNSW** (hnswlib): M=16, efConstruction=200, k=10;
  efSearch ∈ {10, 16, 24, 32, 48, 64, 96, 128, 192, 256}. 3 build seeds per corpus.
- **IVF-Flat** (faiss): nlist=128, k=10; nprobe ∈ {1, 2, 4, 8, 16, 32, 64, 128}.
- Ground truth: exact brute-force top-10 per corpus (trivial at 16k).
- Work measure: primary = **distance computations per query** (faiss `ndis`; for
  HNSW, hops×degree-equivalent as reported by the library where exposed, else
  measured mean per-query latency as the declared fallback — whichever is used, the
  SAME measure is used for every corpus and stated in the results doc).

## Endpoint

For each system, the normalized recall–work curve C(r) (work to reach recall@10 = r,
log-interpolated), compared over the registered interval **r ∈ [0.80, 0.99]** by

    D(W1, W2) = sup_r | log C_W1(r) − log C_W2(r) |.

Noise floor δ_real = max pairwise D among real's 3 subsamples (declared in results
before any synthetic comparison is read).

## Registered predictions

**P1 — behavioral sufficiency at matched scale (make-or-break).** For BOTH systems,
`rd8`'s median curve satisfies D(rd8, real) ≤ max(2·δ_real, log 1.5).
*Falsified if* either system exceeds the band. A falsification here means gates +
anatomy are NOT a behaviorally sufficient descriptor even at the fitting scale — a
major negative for Objective B, to be reported with the gate/anatomy component that
best correlates with the divergence.

**P2 — discrimination (validity of the endpoint).** D(null, real) ≥ 2 × D(rd8, real)
on at least one system, and D(null, real) > log 2 on both. *Falsified if* the null
tracks real — which would mean recall–work curves at this scale are insensitive to
the geometry entirely, the experiment cannot distinguish the hypotheses, and no
conclusion about P1 may be drawn either way (test void, said so).

**P3 — anatomy is operational, not cosmetic (the differential-testing claim).**
`rd6` (same scalar G6, super-hub anatomy) diverges from real specifically in the
tail: at the operating point nearest recall 0.95, its p95 per-query work ratio to
real exceeds 2×, and/or its hub-rank structure under the approximate index diverges
(Spearman between exact and HNSW-retrieved reverse-count ranks lower than real's by
≥ 0.2). *Falsified if* rd6 tracks real as closely as rd8 everywhere measured — which
would mean anatomy does not matter behaviorally at this scale and the anatomy
falsifier defends measurement hygiene only; the Bond Metric paper's differential
claim (§Implications) would need that caveat.

**Honest risks, declared.** (a) n=16k is small for HNSW regime differences — curves
may compress toward brute force; the nprobe/efSearch grids bottom out at very high
recall. Mitigation: the interval starts at r=0.80 and the null control calibrates
sensitivity (P2). (b) The work measure differs between libraries; cross-SYSTEM
comparison is out of scope — every comparison is within-system, across corpora.
(c) rd8 missed G3 by ~1.9× at this scale's upper end (RC1 round 2); if P1 fails and
the divergence correlates with spectral work terms, that is the expected suspect and
will be stated as such rather than discovered post hoc.

## Protocol

Atlas, CPU (hnswlib + faiss-cpu in `/home/claude/env`, installed if absent);
driver `harness/wp5/wp5lite.py` (to be committed with the run); all raw curves,
per-query work distributions, and D values to `results/wp5lite.json`; results doc
`results/WP5LITE_RESULT.md` reports every prediction's verdict, misses as misses.
Iteration duty: this document is the only registration for this experiment; any
re-run after protocol changes gets a new numbered registration disclosing this one.
