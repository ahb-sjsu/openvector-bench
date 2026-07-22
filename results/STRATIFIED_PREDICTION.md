# Pre-registration — the stratified (Whitney) family

**Registered before the gating run** (the discipline of `PREREG_RC1.md`: predictions
posited, falsifiers named, risks stated, misses reported as misses). This is a
*fitting* experiment on train/validation only; the sealed 25% is never loaded and
this is not RC-1 admission. Family + falsifier:
[`openvector_bench/generator_search.py`](../openvector_bench/generator_search.py)
(`stratified_corpus`, `whitney_b_defect`).

## Why this family

The round-3 concentration family fixes **one** local dimension per cluster, so the
per-point local-ID distribution is a spike: it can chase the G1 median but the
spread (G7, real local-ID IQR ≈ 21 at n=8k, ≈ 26 at n=16k) collapses toward 0.
Every prior family misses **G1 and G7 together** because both are dragged up by an
ambient-dominated local dimension.

A **Whitney-stratified space** is the principled generalisation: within each cone
the points lie on a *flag* of nested subspaces `V_0 ⊃ V_1 ⊃ …` (strata of
decreasing dimension `s_0 > s_1 > … > s_L`, meeting along closures), so the
per-point local dimension is a genuine **spectrum**, not a spike.

## Registered predictions

**P1 — the dimension spectrum sets G1 *and* G7 by construction.** With the strata
dimensions `s_0…s_L` (knobs `top_dim`, `bottom_dim`, `n_strata`) set to the target
local-ID distribution, the measured two-NN distribution's **centre matches G1** and
its **spread matches G7** *simultaneously* — the first family to hit both.
*Falsified if* the search cannot bring G1 and G7 within their bands together (G1
`[0.85,1.15]`, G7 `[0.80,1.20]`) while holding G5/G6, at matched effective rank.

**P2 — frontier accumulation gives hubness.** `frontier_conc` shrinks the shell
coordinates separating each stratum from the next-deeper one (points pile onto the
frontier — the Whitney (b) secant condition) and tilts population toward the
low-dimensional strata, so the dense hubs are the low-dim strata. *Prediction:* G6
hubness reaches its band from this mechanism plus heavy-tailed cone sizes and the
hyperbolic (Ch. 3 `exp_0`) centre layout, without a separate hubness knob.

**P3 — deep strata rescue an undersampled top stratum (the honest risk).** A top
stratum of dimension `s_0 ≈ 80` is still undersampled at n = 8–16k, so its two-NN
reading may **overshoot** `s_0` exactly as the flat 52-torus overshot 52
(`EC_FALSIFICATION.md`). The **bet** is that the well-sampled, heavily populated
*deep* strata pull the ID *distribution* toward target even when the tail is
undersampled. This is **tested, not assumed** — if the top stratum dominates the
two-NN readout, G1 overshoots and P1 fails, and that will be reported.

**P4 — Whitney (b)-regularity is second-order for the gates.** `whitney_b_defect`
measures the numerical (b)-condition defect (mean fraction of a shallow→deep secant
lying outside the shallow stratum's subspace; 0 = regular). *Registered claim:* the
RC-1 gates track the **dimension spectrum + cone count** and are **insensitive** to
this defect at matched spectrum — i.e. (b)-regularity is second-order for what the
battery measures. *Falsified if* two parameter settings with matched G1/G3/G6/G7 but
materially different `whitney_b_defect` produce materially different gate vectors.

## Guardrails

Train/validation only; sealed 25% (hash of row index) never loaded; battery-B
queries held out from the **same instance** (the corrected harness — see commit
"battery-B queries must be held out from the SAME instance"). Not RC-1 admission.
Result and the falsifier readout go to `results/GEN_ROUND4_STRATIFIED.md`.
