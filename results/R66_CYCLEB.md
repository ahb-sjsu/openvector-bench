# Cycle b: per-level frames make the §3 trend seed-robust; §3b joint satisfaction is refuted

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-13 on NRP A10s (three indexed jobs, 40 arms total: 8-variant
screening × 2 halves, 8-arm refinement × 2 halves, 8-arm confirmation).
Drivers `harness/rc1/cycleb*.py`; raw confirmation record `results/r66.txt`.
This is the mechanism cycle chosen at the `R65` fork ("b then a"): one
arrangement/hyperbolic cycle before the freeze.

## Screening: the mild form works, the radical forms explode

The queued hyperbolic mechanism was implemented as a spectrum, from mild
(per-level arrangement frames — each nested-cluster level gets its own QR
frame instead of sharing one `d_glob` basis) to radical (deep trees,
`arr_levels` 6–8; a radial-warp layer approximating exponential volume
growth).

* **Per-level frames (V1 dg24, V2 dg48): the §3 trend enters its band for the
  first time in the family's history** — +0.423 and +0.277 against
  [+0.254, +0.649], where every Phase D arm sat at +0.81 to +1.11. G1@600k
  entered its band for the first time. At dg48, g3 reached 187.6 (real 182.3)
  and s(14) hit 16.2 (real 16.08).
* **Deep trees and the radial layer (V3–V7): refuted** — trend collapses to ~0
  or swings wildly, rspan +4.7 to +8.0, s(53) 35–57. The radical hyperbolic
  forms destroy the ladder; only the mild form preserves it.

The diagnosis: the single shared `d_glob` frame was a coarse-dimension
ceiling. Freeing each arrangement level onto its own frame supplies the
independent structure the density response was missing — without the volume
pathology of a genuinely hyperbolic embedding.

## Refinement: the brk knife edge

With per-level frames, `brk` 0.135–0.160 (W1–W8) overshot everything the
other way: rspan +0.683 → −0.28, trend +0.160 → −0.26. Against the
screening's brk 0.116 (rspan +3.96, trend +0.42), the implied rspan slope is
**≈ −172 per brk unit** — the in-band window [+2.227, +2.567] is ~0.002 of
brk wide. Positives: g1exp IN at all eight W arms, gspan IN at five, W5 lands
g5 at 1.369 exactly, g3 ≈ 188–198 holds at dg48, r100k/r200k rungs IN at
W1/W5.

## Confirmation: V1's trend is robust; V2's is not; §3b cannot be

Four generation seeds (41/89/137/271) at brk 0.116, protocol seeds fixed:

| statistic | band | V1 (dg24) | V2 (dg48) |
|---|---|---|---|
| §3 trend | [+0.254, +0.649] | **+0.410…+0.535 — 4/4 IN** | +0.171…+0.499 — 3/4, spread ±0.15 |
| G1 exponent | [−0.227, −0.112] | −0.091…−0.106 (out by 0.006–0.021) | −0.072…−0.090 (out) |
| rspan | [+2.227, +2.567] | +3.04…+4.31 (out) | +2.85…+4.06 (out) |
| gspan | [−0.602, −0.386] | −0.242…−0.324 (out) | −0.183…−0.289 (out) |
| g1 (real 17.23) | | 16.18–16.45 | 16.11–16.53 |
| g3 (real 182.3) | | 128–152 | **184–204** |
| g5 * (real 1.369) | | **1.374–1.390** | 1.377–1.384 |
| g6 * (real 1.696) | | 1.777–1.806 | 1.765–1.795 |
| g8 (real 0.730) | | **0.721–0.725** | 0.712–0.717 |

Two verdicts follow:

1. **V1's §3 trend is the first density-response criterion the family holds
   robustly** — four of four seeds in band, mid-band, spread ~0.05 (one seed
   at +0.535). V2's single-seed +0.277 near the band edge does not survive
   seeds — the exact R65 failure mode, caught by the same protocol.
2. **§3b joint satisfaction is refuted at the family level, not the tuning
   level.** rspan's seed spread at fixed brk is 1.27 (3.04 → 4.31) against a
   band 0.34 wide. No brk setting can make it robust: the criterion's
   generation variance exceeds its admission window by 4×. This sharpens
   R65's "spans not seed-robust" from an observation about two operating
   points into a structural property of the family.

## Cycle b verdict, and the freeze

The mechanism cycle did what it was queued to do: it found the coarse-
dimension ceiling and removed it. What remains out — §3b absolute levels and
spans, g1exp by ~0.01, g3 at dg24 — is out for structural reasons the cycle
has now mapped, not for want of tuning.

**Frozen configuration (for RC-2): V1** — `log2_pool 10, rho 0.3, brk 0.116,
w_loc 0.6, d_glob 24, decay 0.50, mix 0.6, branch 64, per-level arrangement
frames, arr_decay 0.72` — chosen for seed-robustness of the trend, g5
near-exact, g8 at 0.72, over V2's better g3. Expected RC-2 outcome, stated
before the one-shot: mandatory g5 passes, g1/g6 marginal, §3 trend and G1
exponent near their bands, §3b excluded. The point of RC-2 is to make that
statement held-out and registered rather than in-sample.

## Budget

40 arms this cycle; 116 across Phases A–D plus cycle b.
