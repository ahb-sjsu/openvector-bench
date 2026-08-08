# The bit-address cascade: G1 falls, but the fall is a depth artifact

**Exploratory, not a registered round.** No prereg, no gate, seal untouched;
`R20_CONVERGENCE.md` advised against a round 21 on the round-8 family and this
probes a different construction to decide whether registering anything is
justified. Measured 2026-08-08. Family
[`openvector_bench/bitmap_gen.py`](../openvector_bench/bitmap_gen.py), driver
[`harness/rc1/r21_bitmap_probe.py`](../harness/rc1/r21_bitmap_probe.py), record
[`r21_bitmap_probe.json`](r21_bitmap_probe.json).

## The claim under test

R19 and R20 closed the round-8 lineage because its knobs are **level**
parameters: they shift G1 without bending its trend in n, while real's falls by
a third across the ladder. `bitmap_gen` addresses that in the *construction*
rather than the parameters. Each row carries a bit address; its vector is the
sum of one sparse displacement per address prefix at geometrically shrinking
scale. Neighbours share a prefix of length `l* ~ log_B n`, so as n grows the
local geometry is dominated by deeper levels — and if the support size `m_l`
shrinks with depth, intrinsic dimension should fall with an exponent fixed by
the level plan rather than fitted:

    G1 ~ m0 * n**(-dim_decay / ln B)

`dim_decay = 0` is carried as the null that must reproduce the old flat/rising
failure.

## Preconditions

All passed: bit-exact on repeat, random access confirmed
(`emit_rows(p,[7,11,63,5])` equals those rows of a full generation), seeds
separate, and the estimator domain check clean across every arm — the
precondition `R20_CONVERGENCE.md` named as missing.

## Result: the drift is finite-depth truncation

Three seeds per arm, rungs 25k/50k/100k, 10k queries.

| depth L | dim_decay | G1 across rungs | exponent | truncation pred | c |
|---|---|---|---|---|---|
| 30 | 0.00 | 24.31 / 22.53 / 20.42 | −0.126 ± 0.005 | −0.100 | 1.47 |
| 30 | 0.25 | 22.90 / 21.39 / 19.38 | −0.121 ± 0.006 | −0.100 | 1.47 |
| 45 | 0.00 | 51.30 / 49.25 / 47.13 | −0.061 ± 0.001 | −0.049 | 1.67 |
| 45 | 0.25 | 49.93 / 49.59 / 47.05 | −0.043 ± 0.003 | −0.049 | 1.66 |
| 60 | 0.00 | 77.66 / 76.08 / 73.22 | −0.042 ± 0.011 | −0.033 | 1.70 |

*(real exponent over these rungs: −0.210)*

**G1 ≈ c·(L − log₂ n) with c ≈ 1.5–1.7 throughout**, and the exponent collapses
monotonically as the depth budget grows: −0.126 → −0.061 → −0.042. That is the
signature of an artifact. A construction constant does not weaken as L rises.

Two consequences kill it:

1. To hold G1 near real's level you need L ≈ 30, which *fixes* the exponent at
   ≈ −0.126. It is not a design choice.
2. `log₂(10¹²) ≈ 39.9 > 30`, so at trillion scale the corpus runs off the bottom
   of the tree. The drift does not merely fail to extrapolate — it inverts.

**`dim_decay` is not the driver.** At L = 30 the null and the decayed arm are
within noise (−0.126 ± 0.005 vs −0.121 ± 0.006). At L = 45 the knob has a small
effect in the *wrong* direction (−0.061 → −0.043, less negative where the design
says more).

## What this cost, and what it bought

Four design constants were wrong on the first pass and each was caught by
measurement, not by reasoning: support size (`m0` off by ~10x), the amplitude
schedule (`scale_decay` 2.0 drove the structured signal three orders under the
noise floor, pinning G1 near 220 in every arm), the noise floor itself, and the
level-plan form (power law had far too short a lever arm; geometric replaced
it). The theory supplied the right functional *form* for the exponent and
nothing about the regime in which it is observable.

What survives is the module. `bitmap_gen` is the only generator in the repo
whose regeneration is a **guarantee** rather than best-effort: splitmix64
integers for address, branch, support and signs, with no RNG stream, no BLAS and
no libm in the structural path, plus O(1) random access to any row. Every family
in `generator_search.py` emits through `default_rng().standard_normal`, `np.cos`,
`@` and `np.linalg.qr` — all four hazards `DISTRIBUTION.md` §3 names, which is
why regeneration there can only ever be a cache hit with a byte fallback.

## Sequel

`R21B_SCALE_DEPENDENCE.md` re-measured the target and found this family is
*not* excluded on profile shape — its normalized scale dependence (β +3.25 at
L = 90) sits within 7% of real's +3.47, closer than any other control. The
exclusion stands on **level** (G1 ~125 against real's ~20) and on the truncation
artifact above. `R21D_DIMDECAY_REFUTED.md` then closed the wider hierarchical
direction: amplitude decay is what makes a level dominate the local dimension
and is simultaneously what collapses the neighbour distance, so the two regimes
are exhaustive and both fail.
