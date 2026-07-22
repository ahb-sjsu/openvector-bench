# Generator search — round 7: the anatomy falsifier catches the optimizer; the query model is the right mechanism

**Run:** 2026-07-22, NRP Nautilus, 12-shard swarm (indexed Job, cpu=1; 480 evals +
anchored defaults). n=8000 base + 1000 same-instance Zipf-query-block queries, battery
B, k=10, train/val only, seal untouched. Family: `hier_query_corpus`.
Pre-registration (7 probes + hub-anatomy diagnosis disclosed):
[`HIER_QUERY_PREDICTION.md`](HIER_QUERY_PREDICTION.md).

## The headline: P2 fired exactly as designed

**The score-best point (shard 6, 0.227 — best score of the campaign) satisfies P1
numerically and is disqualified by P2.** All six registered gates sit in [0.5, 2.0]×
on three fresh seeds (seed 0: G1 0.96, G2 0.70, G3 1.52, G6 1.29, G7 1.29, G8 0.75) —
but its base→base anatomy reads **skew 6.8–7.8, max reverse-count ~350** (registered
bound: skew < 3; real: 1.5 / 78). Offered a genuine query-measure knob, the optimizer
still found it cheaper to game G6 with corpus super-hubs (`size_tail = 1.39`,
`query_tail = 0.48`). Without P2 this would have shipped as the campaign's six-gate
joint match. **The first registered look behind a gate caught a scalar-gaming
optimizer in the wild** — the non-identifiability of one-number hubness, demonstrated
by the search itself. (Worst offender: shard 8, 6/6 in band with skew 22.9, max 1730.)

## The anatomy-filtered result: the query mechanism works, and G2 is solved by it

Anatomy-screening all 12 shards (full battery + base→base skew, seed 0;
[`gen_round7_query.json`](gen_round7_query.json) `anatomy_all`):

| | P2 | six gates | mechanism |
|---|---|---|---|
| shards 1, 10, 7 | **PASS** (skew 0.6–1.7) | 5/6 in band | high `query_tail` (1.2–2.4), low `size_tail` |
| shards 6, 8, + 7 others | FAIL (skew 3.5–27) | up to 6/6 | corpus super-hubs |

Best P2-passing point — **shard 1** (score 0.243, `query_tail = 2.35`,
`size_tail = 0.16`):

| gate | ratio | |
|---|---:|---|
| G1 intrinsic dim | 1.07× | ✓ |
| **G2 ball-growth** | **1.02×** | ✓ **the round-6 wall, fully matched** |
| G3 effective rank | 2.50× | ✗ (band top 2.0) |
| G6 hubness | 1.36× | ✓ |
| G7 local-ID IQR | 0.77× | ✓ |
| G8 PCA retention | 0.79× | ✓ |
| base→base skew / max | **1.73 / 99** | real: 1.50 / 78 — anatomy matched |

Five of six in band **with real's anatomy**, and G2 — pinned at 0.14× through six
corpus-side mechanisms — reads **1.02×** under the query model. The single miss is
G3 (2.50×), a gate round 6 held at 0.55× with the same `spectrum_decay` knob at hand.

## Verdicts

- **P1 — NOT achieved as registered** (six gates jointly, at the round's designated
  solution): the score-best point fails P2; the anatomy-clean point misses G3. Both
  halves of the miss are informative and reported as the miss they are.
- **P2 — FIRED, its purpose.** The falsifier did precisely what it was registered to
  do. Methodological consequence (round-8 protocol): **anatomy belongs inside the
  fitness** — a base→base-skew band as a scored term, not a post-hoc check — because
  an unpriced anatomy is an invitation the optimizer accepts.
- **P3 — did not fire as feared.** G8 held 0.75–0.79 at both key points; the G8×G6
  binding through `query_tail` did not materialize at matched scores.

## Jacobian controllability at the anatomy-clean point (registered §, in flight)

The registered local-controllability test — central differences of (G3, G6, G2) w.r.t.
(`spectrum_decay`, `query_tail`, `equalize`) × 3 seeds at shard 1's point — decides
whether the G3 miss is a search-budget artifact (J nonsingular, `spectrum_decay`
dominant in the G3 column ⟹ the six-gate + anatomy point exists in a neighbourhood)
or a real coupling. Results land in `r7_jacobian.json` / this file's next commit.

Nothing here passes RC-1; the seal is untouched. Numbers:
[`gen_round7_query.json`](gen_round7_query.json) (12 shards, full battery × 3 seeds at
score-best, anatomy screen × 12, and the real-corpus hub-anatomy diagnosis).
