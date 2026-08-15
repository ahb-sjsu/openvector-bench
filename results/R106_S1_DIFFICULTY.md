# R106: ANN difficulty audit of the S1 candidate — echo groups move np@95 from 2 to 10–11

**Status: measured, 2026-08-15.** First application of the packaged
difficulty audit (`openvector_bench/difficulty_audit.py`, the R80
protocol verbatim: K=1024 IVF cells, 20 k-means iterations seed 7, 10k
exchangeable queries seed 31, exact top-10 ground truth, 590k base).
Corpus: **S1** = R1 + `fil_scale 0.99` (the RC-14 frozen candidate:
F8 defaults + `p_dup 0, p_echo 0.11, echo_k 3, echo_win 100000,
echo_alpha 0.96, pool_alpha 0.23, seg_break 0.138`), 600k rows, seeds
41 and 5001, generated fork-parallel on Atlas, audited on GPU 1.

## Result

| corpus | np@95 | occ CV | occ skew | top-10 share | m1 | m10 | r@p1 |
|---|---|---|---|---|---|---|---|
| real wiki-1024 (R80, 3 blocks) | **47–50** | 0.384–0.402 | 0.61–0.88 | 0.023–0.026 | 0.051–0.052 | 0.213–0.219 | 0.533–0.536 |
| RC-3 gen (R80, 2 seeds) | **2** | 0.313–0.318 | 0.44–0.45 | 0.019 | 0.054 | 0.212–0.214 | 0.914–0.917 |
| **S1 seed 41** | **11** | 0.305 | 0.56 | 0.019 | 0.047 | 0.250 | 0.836 |
| **S1 seed 5001** | **10** | 0.315 | 0.56 | 0.019 | 0.046 | 0.252 | 0.837 |

Raw panels: `results/r106_audit.json`.

## Reading

* **The R1 mechanism family is 5× harder for IVF than the RC-3
  generator** (np@95 10–11 vs 2), while still 4–5× easier than real
  (47–50). The gap to real closed from 25× to ~4.5× without ever
  optimizing for ANN behaviour — the echo groups (window-local
  near-parallel micro-clusters) and the D12-pocket retunes were tuned
  against the *geometric* admission panel only.
* The mechanism is visible in the margins: S1's nn margin dropped to
  0.046–0.047 (real 0.051, RC-3 gen 0.054) and its r10 margin *rose*
  to 0.250 — echo groups put true neighbours at near-parallel offsets
  that straddle IVF cell boundaries, which is exactly what makes real
  corpora need deep probing.
* Occupancy shape is basically unchanged from RC-3 (CV ~0.31, top-10
  share 0.019): the remaining 4–5× difficulty gap is *not* an
  occupancy-imbalance story; it lives in where queries' true
  neighbours sit relative to cell boundaries.
* **10T implication:** tiers built from the S1 family are
  "intermediate" difficulty out of the box; the audit's np@95 number
  is the per-tier difficulty label, and the R80 real band is the
  calibration target. The RC-2-era sealed-battery deltas remain the
  labels for how far synthetic-vs-real difficulty diverges at matched
  geometry.

## Protocol note

Numbers are comparable to R80 only at the 600k cap (np@95 is mildly
cap-dependent: real part_000 at a 120k cap reads 46). The audit CLI
defaults to the 600k cap.
