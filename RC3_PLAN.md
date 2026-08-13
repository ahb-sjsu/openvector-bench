# RC-3: the rank-level campaign

**Status: plan, 2026-08-13.** Successor to `RC1_PLAN.md` after the RC-2
verdict (`results/RC2_VERDICT.md`): excluded on g6 (+1.4%) and the density
response, with g1 and g5 mandatory-IN held-out for the first time. This
plan targets what the RC-2 evidence says is left, under bands that fix what
RC-2 showed was broken about the old ones.

## 1. What RC-2 changed about the problem

1. **The family under study is now the frozen package generator** —
   lognormal-table articles, keyed-random clusters in a 600k window,
   per-level frames (`openvector_bench/segment_gen.py`, hash `80d94f61…`).
   Its failure signature differs from the harness family the R65/R66 audits
   measured, and every RC-3 baseline must be re-established against it:
   at the frozen point, §3b G1 levels are now *high* at sparse pools
   (19.9/21.5/23.7 vs bands ≈[14.4,18.2]/[15.7,18.1]/[18.2,20.4]) and IN at
   400k/600k — the old audit's "levels 15–20% low" inverted when the
   article law was corrected. rspan overshoots (4.39 vs [1.94, 2.65]).
2. **Bands must come from ≥10 blocks.** The P1 falsifier fired: four-block
   bands underestimate real's own block drift for g6 and the §3 trend.
   Re-banding from 10 blocks (4 held-out + 6 fresh) is Phase 0, running.
3. **The residual misses, held out**: g6 +1.4%, g8 −1.1%, g3 −3%, g4 +23%,
   g1exp shallow (−0.090 vs ≤ −0.127), §3 trend below the fresh-block band,
   §3b rspan/gspan and sparse-pool levels out.

## 2. The central hypothesis

`R64` isolated a **rank-level deficit**: local eff_rank ~75 and global
~92–102 against real's 168/182 — the local/global *pattern* is real-like,
the *level* is half — and no lever the campaign swept touches it
(`d_loc`/`fil_dim` were held fixed throughout). The hypothesis: this one
deficit underlies several residual misses at once —

* **g4** (dims90 448 vs 358): too few independent directions forces the
  variance into a flatter tail;
* **g1exp** (−0.090 vs −0.185 real): dimension cannot climb as sampling
  thins because there is nothing higher-rank to climb into;
* **§3b sparse-pool G1** overshoot and **rspan** overshoot: the ladder's
  low end is dominated by article-local structure whose effective rank is
  wrong.

**Falsifier, registered now:** if local eff_rank reaches ~168 (via
`d_loc`/`fil_dim`/pool composition) and g1exp + rspan do not move toward
band, the rank-level hypothesis is dead as the density-response driver and
RC-3 stops rather than tunes.

## 3. Phases

* **Phase 0 — re-band (running).** 10-block bands for every registered
  statistic; recorded to `results/reband10.json`; RC-3 targets are these
  bands, declared before any generator arm runs.
* **Phase A — baseline error bars.** The frozen configuration at 4
  generation seeds against the 10-block bands: which residual misses are
  robust, which are seed-fortune. (The RC-2 evaluation is one seed.)
* **Phase B — the rank sweep.** `d_loc` × `fil_dim` × `log2_pool` with
  local/global eff_rank, g4, g1exp, rspan, and the mandatory gates on every
  arm. The instrumented question is §2's falsifier. Envelope: ≤3 sweeps of
  ≤16 arms (NRP indexed jobs, harness generator — it now mirrors the
  package family; winners verified with the package generator on Atlas).
* **Phase C — above-article structure (contingent on B).** The family's
  clusters are index-random; real Wikipedia's ordering carries weak
  above-article adjacency (gap-128 cosine 0.236 vs 0.228 baseline). If B
  moves rank but leaves the §3 trend short of the fresh-block band, test
  index-correlated cluster assignment (nearby articles share clusters with
  probability decaying in index gap — random-access preserved by keying on
  article index blocks).
* **Phase D — freeze + RC-3 one-shot.** Same protocol as RC-2: freeze,
  hash, disclose budget, evaluate once on never-touched blocks (free
  offsets include 2M, 4M, 6M, 8M, 12–14M, 16–17M, 19–20M, 22–24M, 26–27M,
  29–31M, 33M, 36–38M, 40M), report either way.

## 4. Discipline carried forward

Multi-seed before any band claim; registered criteria only (no convenience
statistics in verdicts); anatomy measured alongside summaries; per-phase
kill criteria; the freeze declares expected outcome and budget before the
one-shot; a port-fidelity check precedes any frozen evaluation; "restore
vs retune" adjudicates any post-freeze fix. Budget so far this arc: 0
arms; RC-2's disclosure stands at `spec/RC2_FREEZE.md` §4.
