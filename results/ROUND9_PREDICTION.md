# Pre-registration — round 9: paraphrase clouds (the graded short-range ladder)

**Registered before the gating run.** Train/validation only; sealed 25% never
loaded. Family: `hier_dupq_corpus` (21 knobs, in-tree) — the round-8 construction
plus the three **active** round-9 mechanisms: graded paraphrase clouds
(`cloud_mass`, `cloud_grade`, `cloud_span`), in-patch query anchoring
(`q_anchor`, `anchor_tail`, `q_jit`), and the two-piece spectrum
(`log2_knee`, `spectrum_decay2`). The falsified probe knobs stay at inert
defaults and are so recorded: fine near-dups (`dup_mass` family — invisible to
the trimmed two-NN estimator, probe A) and cluster-Zipf n-coupling
(`query_tail_n` — saturated, probe A).

**Why this design (the convergent diagnosis, `ROUND9_PROBES.md`):** real
neighbours exist at *graded* fractional distances (r1 1%-quantile 0.375 vs
median 0.86; μ = r2/r1 = 1.024) — a short-range ladder our uniform-sparse
patches lack. Every remaining defect traces to that absence: G1's n-drift, G2's
smooth ball growth, the anchored-query μ-gap (probe D: G6 level+slope matched
but G1 collapsed to 0.06×), and density-driven hub anatomy
(corr(N₁₀, −d10) = +0.67). Zipf-sized clouds around popular rows with power-law
radius grading spanning ~0.1–1× patch scale supply the ladder, the anchor
targets, and the density gradient in one mechanism.

## Disclosures

1. Probes A–D (`ROUND9_PROBES.md`) ran as disclosed single-seed screening; the
   assembled family's knobs derive from them. No gating run has occurred.
2. The battery-A protocol change (uniform holdout sampling; registered in
   `RC1_ROUND2_CANDIDATE.md` finding 3, implemented in `geometry.py`) means
   **real battery-A targets must be re-measured before any candidate is scored**
   — protocol step 1 below; the new targets will be published in the results doc
   before any candidate numbers are read.
3. WP5-lite (`WP5LITE_RESULT.md`) falsified behavioral sufficiency for the
   round-8 candidate, with both divergences attributed to exactly the two
   components this round adds (ladder; spectrum shape). This registration
   therefore carries the campaign's first **behavioral** prediction (P4).
4. Iteration count to date: 8 pre-registered gating rounds, 8 disclosed
   screening probes, 1 formal grid admission (0/24), 1 behavioral experiment.
   The seal has never been opened.

## Registered predictions

**P1 — the ladder pins G1 (make-or-break).** With clouds active, on the §5 grid
(n ∈ {25k, 50k, 100k, 200k}): G1 is in band **and n-flat** — |slope| ≤ 0.05 per
decade (real: +0.01 to +0.04) — **and** remains in band with the query anchor
active (repairing probe D's 0.06× collapse: the cloud ladder provides the
intermediate neighbours between anchor and bulk). *Falsified if* G1 drifts out
of band by 100k as in round 2, or the anchored-G1 collapse persists at the
screened operating point. A P1 falsification kills the paraphrase-cloud account
of real's n-flatness, not just a tuning — the next suspect would have to be
named from data, not this family.

**P2 — anchored illumination carries G6 growth.** Battery-B hubness growth
within the §5 exponent tolerance of real's +0.22/decade (|Δ| ≤ 0.05), with
level in band — the probe-D mechanism (anchoring at graded targets) holding at
scale. *Falsified if* growth stays shallow (≈ +0.13 as round 2): that would
mean anchor-target mass does not compound with n and an explicitly n-coupled
illumination knob is required (a NEW mechanism, to be registered separately —
not silently retuned).

**P3 — the grid: mandatory gates + exponents.** At the screened operating
point: all three mandatory gates (G1/G5/G6) pass their §5 bands in ≥ 20 of 24
cells, and **zero scaling-exponent failures** (round 2: 42 mandatory-cell
failures, 6 exponent failures, all G6). G3/G4 land within ±15% after the
colouring retune (knob proven; fit, don't invent). *Falsified if* the count
rule misses — reported cell-by-cell as in `RC1_ROUND2_CANDIDATE.md`. Full
24/24 admission is the goal but is NOT predicted; G7/G8 at scale are refit
last (round-2 map) and their misses, if any, will be named.

**P4 — behavioral closure (first use of the WP5 endpoint).** At n=16k under
the exact `harness/wp5/wp5lite.py` protocol (fixed grids, same endpoint, fresh
run with rd9 replacing rd8; real + null controls re-run same-day): both
**D_hnsw and D_ivf ≤ max(2·δ_real, log 1.5)** — the prediction that closing
the ladder + spectrum closes the recall–work gap. *Falsified if* either stays
out: then a descriptor component beyond {ladder, spectrum shape} is
behaviorally load-bearing, and the results doc must report which residual
geometric/anatomy component best correlates with the residual divergence.
P4 is evaluated only if P1∧P3 pass (a geometrically failed candidate tells us
nothing new behaviorally — WP5-lite already covers that case).

**Honest risks, declared.** (a) Clouds add mass at short range: G7 (local-ID
IQR) and G5 may shift out of band as a side effect — they are scored, not
assumed. (b) The grading must span the trimmed decile (the exact reason fine
dups failed); if the estimator's trim swallows the ladder at scale, P1 fails
in a diagnosable way (μ-distribution to be reported). (c) Anchor mass +
clouds couple into the d10 window (G2); probe D showed G7 0.94–0.97 and G8
1.04 at n ≤ 100k, but 200k is unprobed. (d) Behavioral P4 inherits WP5-lite's
declared caveats (n=16k scale, per-system work measures).

## Protocol (in order; no step reordered after the fact)

1. **Re-measure real targets** under the uniform battery-A protocol (Atlas,
   PREREG_RC1 v2 machinery, full n×k grid, 5 subsamples). Publish before any
   candidate scoring.
2. **Screening (disclosed):** bounded screen over (`cloud_mass`,
   `cloud_grade`, `cloud_span`, `q_anchor`, `q_jit`, `spectrum_decay`,
   `log2_knee`) at n ∈ {25k, 100k}, single seed, battery-B cell means — picks
   ONE operating point; the screen's best/worst are disclosed in the results.
3. **Gating run:** formal §5 grid admission via `score_rc1` (both batteries,
   5 subsamples, equivalence bands + count rule + exponent criterion), 3 fresh
   seeds at the chosen point. P1–P3 read from this run only.
4. **Behavioral run (P4):** `wp5lite` protocol with rd9; same fixed grids;
   same-day real/null controls; results in `wp5lite_r9.json`.
5. Results doc `ROUND9_RESULT.md`: every prediction's verdict, misses as
   misses; any protocol deviation voids the affected prediction and says so.

The seal remains closed throughout; a sealed one-shot only ever follows a
candidate that passes step 3 in full.
