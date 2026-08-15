# R105: the description-length curve — battery-B closure saturates almost immediately in train bits

**Status: measured, 2026-08-15** (validation rows only; sealed set
untouched; real cells reused from r101 at n=100k, 3 subsamples, point
ratios of medians as in RC-13/14). Candidate: S1 rotated + mean-restored
(the RC-13 operating point), contracted toward train k-means centroids
at K ∈ {64 … 65536} and λ ∈ {0.20, 0.35}, plus the **ROW anchor** —
contraction toward the literal nearest train row, i.e. the memorization
endpoint where the "artifact" is the entire 310k-row train split
(1.2 GB). Artifact description length grows as K × 4 KB (256 KB at
K=64 → 268 MB at K=65536 → 1.2 GB at ROW).

## The curve

| variant | g1@B | g8@B | g1@A | g5@A |
|---|---|---|---|---|
| K=64 λ.20 | 2.722 | 0.610 | 0.973 | 1.003 |
| K=256 λ.20 | 2.484 | 0.642 | 0.973 | 1.006 |
| K=1024 λ.20 | 2.437 | 0.669 | 0.975 | 1.006 |
| K=4096 λ.20 | 2.367 | 0.669 | 0.974 | 1.006 |
| K=16384 λ.20 | 2.345 | 0.660 | 0.984 | 1.004 |
| K=65536 λ.20 | 2.441 | 0.649 | 0.985 | 1.001 |
| ROW λ.20 | 2.350 | 0.636 | 1.002 | 0.991 |
| K=64 λ.35 | 2.687 | 0.659 | 1.013 | 1.067 |
| K=256 λ.35 | 2.495 | 0.723 | 1.018 | 1.074 |
| K=1024 λ.35 | 2.332 | 0.785 | 1.018 | 1.074 |
| K=4096 λ.35 | 2.163 | 0.792 | 1.006 | 1.070 |
| K=16384 λ.35 | 2.081 | 0.781 | 1.025 | 1.062 |
| K=65536 λ.35 | 2.067 | 0.757 | 1.043 | 1.051 |
| **ROW λ.35** | **2.004** | 0.756 | 1.072 | 1.009 |

(g@B/g@A = candidate/real ratio at k=10, n=100k; raw cells
`results/r105_cells.json`, scorer summary `results/r105_scores.json`.)

## Reading

1. **The curve is flat.** At λ=0.20 the g1@B ratio saturates by
   K≈1024 (2.44) and never improves past 2.35 — *including at the
   memorization endpoint*. Going from a 4 MB mixture artifact to the
   entire 1.2 GB train set buys nothing at this dose. At λ=0.35 the
   ladder gains slowly (2.69 → 2.07) and the full train set reaches
   exactly ×2.0 — the floor RC-14 registered — while battery A visibly
   degrades (g1@A 1.07, count-rule 1–3/6 vs 3/6 at λ.20).
2. **The wall is dose-limited, not bits-limited.** More train bits do
   not close battery B at A-compatible contraction doses; only a
   larger λ would, and RC-14 already measured that the A-destroying
   dose still stops at ×1.8. The ×2.0–2.6 bound is therefore not a
   resource frontier that a bigger artifact could push through — it is
   a property of *how much displacement toward the data the corpus-side
   battery tolerates*.
3. **Description length is the wrong axis for closure — placement
   information density is.** Real queries resolve micro-local placement
   that global contraction (at any K, even K = n_train) cannot supply
   without moving rows far enough to break corpus-side geometry. This
   sharpens §15's statement: query-side batteries detect
   data-dependence *per row*, not aggregate density fidelity.
4. Registered expectation from the plan (no variant admits under the
   frozen null) — **MET**: 0 of 14 variants admitted.

This is the program's closing measurement: the successor paragraph for
paper §15 and the final entry in the RC-1 record.
