# Round 9 — result: NOT ADMITTED (0/24); the growth mechanism lands, the sampling operator was wrong

**Gating run per the registered protocol** (`ROUND9_PREDICTION.md`): step 1 v3 targets
published (`3c8163f`, md5 `4139cf04…`) **before** any candidate value was read (step-3
measurement ran concurrently; its log prints counts only; first read followed the
publication commit — timestamps in git). Candidate: `hier_dupq_corpus` at the committed
step-2 point; 5 fresh instances; full grid; both batteries; uniform battery-A holdout;
all three §5 criteria. Cells md5 `ebabe552…`. Verdict: **NOT ADMITTED — 0/24 count
rule, 53 mandatory cell failures, 9 exponent failures.** §8 re-check under v3: no
frozen null admitted (battery sufficient).

## Prediction verdicts, one by one

**P1 (ladder pins G1) — FALSIFIED**, with the cause diagnosed rather than guessed.
Battery B G1: median 0.77× [0.71, 0.85], slope −0.070 (real +0.017) — *below* band and
over-pinned. Battery A G1: 2.49× — and real's A-side G1 **falls at −0.190/decade**
(26.9 → 19.7 across the grid; corpus-side near-duplicate densification, a strong
newly-measured constraint) while the candidate falls at only −0.065. Attribution: the
step-2 fit and verification generated instances *at* size n; the registered grid
**subsamples n from a large pool**. For a family whose ladders live per-instance,
subsampling a 470k-row instance to 25k thins every cloud — the μ distribution the fit
tuned does not survive the grid's sampling operator (real's ladder thins the same way;
that is precisely what its falling A-side G1 measures). The paraphrase-cloud *account*
is not killed — the fitted *point* was tuned under the wrong operator. Registered
consequence honored: this is reported as a P1 falsification of the operating point,
and the account survives only as round-10 hypothesis with the corrected protocol.

**P2 (anchored illumination carries G6 growth) — the registered falsifier did NOT
fire; full P2 not met.** Battery-B G6 growth: **+0.213 (k=10) and +0.252 (k=30) per
decade against real's +0.249/+0.242 — within |Δ| ≤ 0.05, the first G6 exponent passes
of the campaign** and the round-8 killer resolved at those scales. The named
falsification condition ("growth stays shallow ≈ +0.13") did not occur. Remaining
misses: k=100 growth (+0.102 vs +0.355 — real's growth accelerates with k, anchoring
flattens) and cell-level equivalence (2/12; median 0.90 with CI widths over the band).
Battery-A G6 overshoots (1.54×): cloud density is corpus-side hub mass — consistent
with the verification's bb_skew drift (1.96→2.95) — the anatomy warned first.

**P3 (mandatory + exponents + G3/G4) — FALSIFIED** (53 mandatory fails; 9 exponent
fails; G4 = 1.52×). Its G3 clause was met in full: **G3 = 1.00 median, 24/24 cells** —
likewise G8 battery-B 12/12 and G5 battery-B 12/12.

**P4 (behavioral) — NOT EVALUATED**, per the registration's P1∧P3 gate.

## What round 9 established

1. **The G6 growth mechanism is real**: owner-anchored illumination compounds with n
   at real's rate (k ≤ 30). One mechanism, predicted, registered, measured.
2. **The sampling operator is part of the geometry.** Generate-at-n and
   subsample-from-pool are different experiments for any family with per-instance
   fine structure — and for the real corpus itself (A-side G1 falls −0.19/decade under
   subsampling). Round-10 protocol: fit under the grid's own operator (pool + subsample),
   despite the cost.
3. **The spectrum is solved** (G3 1.00 everywhere) and G4 remains a shape problem
   (1.52×, flat) — the two-piece knee is insufficient; the target needs the measured
   real spectrum, not a parametric family (fit the tail nonparametrically).
4. **Anatomy again led the gates**: the bb_skew drift at verification anticipated the
   battery-A G6 overshoot. The anatomy-inside-the-fitness lesson extends: score the
   battery-A hub level, not only the b→b skew.

## Round-10 targets (falsification order)

1. Refit under the pool+subsample operator (the step-3 pipeline as the fitness).
2. Cloud/anchor mass rebalance against battery-A: A-side G1 slope −0.19 and G6 level
   1.0× are now *joint* constraints on cloud density.
3. k-dependent illumination (k=100 growth gap).
4. Nonparametric spectral target for G4.

Iteration count to date: 9 gating rounds, 9+ disclosed probes/screens, 2 formal grid
admissions, 1 behavioral experiment; the seal has never been opened. Artifacts:
[`rc1_targets_v3.json`](rc1_targets_v3.json), [`rc1_v9_cells.json`](rc1_v9_cells.json),
[`rc1_v9_scores.json`](rc1_v9_scores.json), screen-vs-v3 target comparison in this
commit's message thread.
