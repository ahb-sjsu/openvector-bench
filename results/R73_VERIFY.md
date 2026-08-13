# RC-3 package verification: D12 reaches 8/10, D5's g4 holds, and the residue is one spectral shape

**Exploratory, not a registered round.** Measured 2026-08-13 on Atlas GPU 1
(package generator, seed 41, four candidates from `R71`/`R72`). Record
`results/r73_verify.json`; driver `harness/rc1/r73_verify.py` pattern. The
package gained `pool_alpha` (default 0.0) with the frozen RC-2 hash
verified unchanged — the frozen family is untouched at its defaults.

| candidate | in-band (R68, n=10) | misses |
|---|---|---|
| **D12** α0.22 brk0.126 | **8/10** — g1 g5 g6 g8 trend g1exp rspan gspan | g3 149.4 (−2.7%), g4 416 (+15%) |
| C5 α0.24 brk0.128 | 7/10 | g3, g4, g8 0.746 (+0.003) |
| C1 α0.20 brk0.122 | 7/10 | g3, g4, g1exp −0.107 |
| D5 α0.18 brk0.128 lp9.5 | 7/10 — **g4 361 IN** | g3, g8 0.764, g1exp −0.103 |

The package trend runs higher than the harness predicted (D12 +0.372 →
+0.426; D5 +0.316 → +0.420), so the trend conceded on the harness was not
actually lost — every candidate's trend is in band on the package. Against
the RC-2 frozen configuration (6/10 under these bands), D12 gains g8,
trend, g1exp and rspan at the cost of g3's last 2.7%.

**The remaining structure is a single trade surface.** g3 (eff rank 175
target), g4 (dims90 357), and g8 (PCA retention 0.737) are all functions
of the PCA spectrum's shape, and the α power law moves them along a curve
that never intersects all three bands: α lowers g3 out of band before g4
arrives (D12), lp+α reaches g4 while pushing g8 high (D5). Matching all
three needs a different spectral *form* — plausibly a two-scale profile
(concentrated head for g4/g8, extended plateau for g3) — which is a new
mechanism, not a tuning step.

Knife edges at D12 (g1exp in by 0.002, g8 by 0.001) make its 8/10 a
single-seed claim; `R74` multi-seeds it before any freeze decision, per
the discipline.

## Budget

4 arms; RC-3 total 54.
