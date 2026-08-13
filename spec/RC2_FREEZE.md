# RC-2 freeze declaration and search-budget disclosure

**Status: FROZEN as of 2026-08-13, before any held-out evaluation.** This
document is written under `GENERATOR_SEARCH.md` §5 (binding guardrails): it
declares the one generator RC-2 will judge, its byte identity, the full
search budget that produced it, and the expected outcome — stated in advance
so the verdict cannot be quietly reframed after the fact.

## 1. The frozen artifact

* **Family**: `openvector_bench.segment_gen.segment_corpus` — segmented
  articles in a nested arrangement with per-level frames, path decay + ball
  mixture, and rho direction-sharing. Deterministic, bit-exact,
  chunk-invariant, random-access (row 10¹² verified; tests
  `tests/test_hashrng.py`).
* **Parameters**: the `SEGMENT_PARAMS` defaults, exactly as committed —
  art_break 0.045, seg_break 0.116, branch 64, arr_levels 3, d_glob 24,
  d_loc 64, w_loc 0.60, fil_dim 48, fil_scale 1.0, nlev 6, log2_pool 10,
  path_decay 0.50, path_mix 0.60, rho 0.30, level_frames 1. This is cycle
  b's V1 (`R66`), chosen for seed-robustness of the §3 trend.
* **Generation seed: 1009** — never used anywhere in the campaign (tuning
  and confirmation used 41, 89, 137, 271; protocol seeds 2, 7, 31, 61). The
  RC-2 draw is therefore itself held out.
* **Byte identity**: `sha256(segment_corpus(defaults, 6000, 1024, 1009))`
  = `80d94f61cdc304d886ed97cc55805b966ac31ec8f529ea41977f7174065c5f57`
  (amended once — see §6). Any evaluation must reproduce this hash before
  its numbers count.

## 2. The evaluation, declared before it runs

* **Generator side**: ONE evaluation of the frozen configuration at seed
  1009, 600k rows, under the registered measurement protocol (the same
  panel, splits and protocol seeds as `R65`/`R66`). Run as `R67`; its first
  numbers stand. A reproducible *bug* in the port may be fixed and re-run;
  a disliked *number* may not — the distinction is whether the fix changes
  the family's definition or restores it.
* **Real side**: four contiguous 600k-row blocks of the Cohere Embed-V3
  Wikipedia corpus at offsets **5,000,000 / 15,000,000 / 25,000,000 /
  39,000,000** — none previously used (consumed by prior rounds: 0;
  1,067,268; 7,228,966; 34,414,820). Held-out bands are mean ± 2 sd across
  the four blocks, mirroring how the registered bands were derived. This
  services `PROFILE.md` falsifier P1.
* **Verdict rule**: the PREREG_RC1 admission structure applied to the
  held-out bands — mandatory g1/g5/g6, "all but two" across the eight
  gates, plus the §3 and §3b ladders reported criterion by criterion. The
  verdict is reported whatever it is; there is no second shot.

## 3. Expected outcome, stated in advance (`R66`)

Mandatory g5 passes; g1 and g6 sit 4–6% off and may fall either side of
held-out bands; g8 close (0.72 vs 0.730); g3/g4 out at this operating point
(g3 ~150 vs ~182, g4 ~447 vs ~359); §3 trend IN if the port is faithful;
G1-vs-n exponent a near-miss (~0.01 shallow); **§3b excluded** — the
five-pool absolute levels and both spans fail, and `R66` showed the spans'
generation-seed spread is 4× their admission window, a family-level
property. The purpose of RC-2 is to make exactly this statement held-out
and registered rather than in-sample.

## 4. Search budget (GENERATOR_SEARCH.md §5.3 / PREREG §7)

The multiple-comparisons load behind the frozen configuration:

* **RC1_PLAN campaign (Phases A–D + cycle b, `R62`–`R66`)**: 116 arms —
  Phase A 28, Phase B 12, Phase C 24, Phase D 12, cycle b 40 — every arm a
  full-panel evaluation on NRP A10s, all recorded in `results/`.
* **Prior arc (`R21`–`R61`)**: ~45 measurement rounds and on the order of
  200+ distinct configuration evaluations across the density ladder,
  adjacency-mechanism, segmentation and composition studies, including nine
  parameters eliminated as "invariant to everything" and later found to be
  operating-point-conditional. The registered bands themselves (`R24`/`R29`)
  consumed four corpus blocks, disclosed above.
* **Port fidelity (`R67`)**: 2 arms (one corpus, two measurement halves).
* **What was never touched**: the four held-out block offsets, seed 1009,
  and the RC-2 comparison itself. No search, fuzzing, or tuning ran against
  any of them.

## 5. Known misses carried into the freeze, deliberately

* Throughput: 3.06 MB/s/core single-thread against DISTRIBUTION's ~10
  MB/s/core target (Phase E, compiled kernel, deferred — a distribution
  property, not a geometry property).
* The s(k) curve targets remain single-block (`R33`); re-banding was
  deferred for Atlas headroom. They are unregistered and do not enter the
  verdict.
* §3b and the G1 exponent, per §3 above — expected exclusions, frozen
  anyway. Freezing the best *robust* configuration and taking the verdict
  is the close the campaign's history demands: a single-seed point estimate
  near a band edge is not a result, and neither is a retune after a peek.

## 6. Amendment (2026-08-13, same day, before any held-out comparison)

The first evaluation of the frozen port (hash `9a42de6f…`) did not
reproduce the audited family: s(14) 38.3 vs ~16, g6 2.43 vs ~1.79, g8
0.593 vs ~0.72 — structural, not seed noise. Its full panel is recorded in
the RC-2 round document. Root causes, both definition-level port errors:

1. **Article law**: the port used hierarchical-geometric blocks (runs of
   2^k, 69% of rows in 256-runs) where the audited family draws lognormal
   lengths, mean 23. Restored via a frozen 256-quantile table of the exact
   audited law (no libm in the byte path), drawn per 4096-row superblock.
2. **Cluster assignment**: the port assigned arrangement clusters by
   article *index* (`art // per`), putting contiguous ~7,000-row runs in
   one cluster; the audited family assigns randomly. Restored as
   keyed-random assignment within a declared 600k `arr_window`.

Under §2's pre-stated rule this is the fixable case — the fix restores the
family the campaign audited rather than changing it; no parameter moved.
The amended identity above supersedes `9a42de6f…`; the §3 expected-outcome
statement is unchanged.
