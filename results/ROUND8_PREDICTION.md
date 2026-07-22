# Pre-registration — round 8: anatomy in the fitness

**Registered before the gating run.** Train/validation only; sealed 25% never loaded;
not RC-1 admission. Same family as round 7 (`hier_query_corpus`); the change is the
**protocol**, adopted from round 7's fired P2: the base→base reverse-NN skew is now a
**scored term** (mandatory weight) in `make_evaluate_fn` (`anatomy_target`), not a
post-hoc check. Target measured on the real corpus with the exact fitness estimator
(2000 sampled corpus queries, self excluded, k=10, n=8000): **bb_skew = 1.143**
(max count 19). An unpriced anatomy proved to be an invitation the optimizer accepts;
this round tests whether pricing it is sufficient.

**Disclosures.** (1) Round 7's full result (`GEN_ROUND7_QUERY.md`): score-best gamed
G6 with super-hubs; anatomy-clean shard 1 read five of six gates in band with G2 =
1.02× and real anatomy, missing only G3 = 2.50×. (2) The registered Jacobian test at
shard 1's point, first seed (full 3-seed result to be reported with this round):
∂G3/∂θ_spectrum = −10.05, two orders of magnitude above every other entry in its row —
the G3 miss needs Δspectrum_decay ≈ +0.15 — and ∂G6/∂θ_query = +0.19 dominant in its
row. (3) Shard 0 is warm-started (`WARM_START`) at shard 1's round-7 knobs with
`spectrum_decay` 0.39 → 0.54, the Jacobian-informed correction; the other 11 shards
search cold, exactly as before.

## Registered predictions

**P1 — the six-gate + anatomy joint point (make-or-break).** The search finds a point
with G1, G2, G3, G6, G7, G8 all within [0.5, 2.0]× **and** fitness-estimator bb_skew
within [0.5, 2.5]× of 1.143 (upper band generous: the sampled-skew statistic is noisy).
*Falsified if* no shard's best point satisfies both.

**P2 — pricing flips the optimizer's preferred mechanism.** With anatomy scored, the
in-band shards concentrate in the query-mechanism region (`query_tail` high,
`size_tail` low): *prediction:* a majority of the top-6 shards by score have
bb_skew < 3 (round 7: 3 of 12 overall, and the top scorer was a super-hub point).
*Falsified if* super-hub points still dominate the score ranking — that would mean the
skew term is too noisy at 2000 queries to steer, or the pathology has a cheaper
neighbour we haven't named.

**P3 — honest risk: the anatomy term is a noisy compass.** Sampled reverse-count skew
at count-mean 2.5 is a heavy-tail statistic; per-eval noise may let lucky draws win
shards (a seed-instability we've already seen G6 exhibit). Mitigation is the 3-seed
re-measure at the best point; if the winner's anatomy fails off-seed, the round-9 fix
is averaging the anatomy term over 2 instance seeds per eval (cost ×2 on the skew
only).

## Protocol

NRP swarm, 12 shards × 40 evals, `FAMILY=hier_q`, `ANATOMY_TARGET=1.1426`,
`WARM_START` on shard 0 as disclosed; n = 8000 + 1000, battery B, k = 10. Best point
re-measured with the full battery + anatomy on 3 seeds. Result to
`results/GEN_ROUND8_ANATOMY.md`.
