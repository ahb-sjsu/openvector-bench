# R85: the near-dup ladder on the package — g1exp robustly in band, and a dose interpolation

**Exploratory, not a registered round.** Measured 2026-08-13/14 on Atlas
GPU 1. The RC-6 standing candidate (frozen D12 + near-duplicate ladder)
ported into `openvector_bench.segment_corpus` — parameters `p_dup`,
`alpha_dup`, defaults inert (RC-3 identity `e8423665…` verified
unchanged), dup mode random-access and chunk-invariant (the port
initially broke batch invariance by renormalizing plain rows alongside
blended ones — a last-bit drift caught by the invariance test and fixed
by normalizing only blended rows). Candidate identity at p 0.05, seed 41:
`2556ee1b…`. Records `results/r85_b1.json`, driver
`harness/rc1/r85_b1.py` pattern.

## Four seeds at p_dup 0.05 against the 14-block bands

| statistic | band | 4 seeds | verdict |
|---|---|---|---|
| **§3 G1 exponent** | [−0.228, −0.122] | **−0.139…−0.150** | **IN 4/4 — first package config ever** |
| g1 * | [14.82, 20.86] | 15.74–15.91 | IN 4/4 |
| g5 * | [1.348, 1.424] | 1.369–1.370 | IN 4/4 |
| g6 * | [1.663, 1.840] | 1.767–1.785 | IN 4/4 |
| g8 | [0.730, 0.743] | 0.737–0.739 | IN 4/4 |
| §3 trend | [0.357, 0.657] | 0.432–0.477 | IN 4/4 |
| rspan | [0.951, 2.963] | 1.14–1.23 | IN 4/4 |
| g3 | [151.0, 200.4] | 149.9–151.2 | straddles (2/4) |
| gspan | [−0.624, −0.245] | −0.218…−0.241 | out 4/4 (by 0.004–0.027) |
| g4 | [351.2, 363.1] | 417–418 | out 4/4 |

The RC-4 frontier statement — every g1exp lever slides along a
trend↔g1exp trade curve — is broken on the package: trend sits mid-band
while g1exp is in at every seed. The cost is dose-linear gspan
compression (measured slopes: gspan +2.3 per unit p, g1exp −0.6 per
unit p), which makes the joint window computable rather than searchable:
**p_dup ≈ 0.038** predicts gspan ≈ −0.257 and g1exp ≈ −0.136, both in
with ~0.012 margins, with g3 lifting off its edge. The four-seed
verification at the interpolated dose is `R85b`; if it holds, the
standing frontier becomes robust 9-of-10 (all but g4) — judged, as
always, before any claim.

np95 remains 2 at all seeds: the candidate makes no scatter claim
(`RC6_VERDICT`); that problem belongs to RC-7's continuum arrangement.
