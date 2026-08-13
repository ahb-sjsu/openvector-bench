# Real's G1 drift is geometry, and the target is a curve

**Exploratory, not a registered round.** Measurements of the TARGET plus one
candidate family; train/validation only, RC-2 seal untouched, no admission
claim. Measured 2026-08-08 on Atlas (CPU, 20 threads) against
`/archive/tqp_real/wiki1024`. Drivers `scale_probe{,2,3}.py`, records
`/home/claude/ovb_scale/scale_probe{,2,3}.json`.

> **Correction notice.** The first version of this document reported real's
> scale dependence as 3.84x and claimed real is dramatically less scale-free
> than any control. Both came from a 110k **head slice** of a topically-ordered
> corpus — the exact failure mode `geometry.py` warns about. That slice also
> produced G1 = 17.5/16.9/17.4 (flat), which does not reproduce the registered
> anchors at all. Every number below is from the corrected 600k pool. The
> qualitative finding survives; its magnitude does not.

## Method, and the confound it avoids

G1 falling with n is not by itself evidence of scale-dependent geometry: TwoNN
is finite-sample biased, and the bit-address family (`R21_BITMAP_PROBE`)
produced a G1 that moved with n for purely estimator reasons. So dimension is
resolved against **radius** at fixed n:

    s(r) = d log k / d log r(k)

the local slope of the k-NN growth curve, k = 4..500. For a locally
d-dimensional self-similar set, s is constant. Pool: 600k rows (= the
registered `cap`), 10k uniform holdout queries, each rung drawn uniformly.

## 1. The registered ladder reproduces

| n | G1 measured | registered anchor |
|---|---|---|
| 25,000 | 25.97 | 26.64 |
| 50,000 | 22.84 | 22.78 |
| 100,000 | 20.40 | 19.92 |
| 200,000 | 18.28 | 18.42 |

Exponent **-0.168** measured against **-0.179** registered. The anchors are
sound and independently reproducible.

## 2. The drift is geometry, not estimator bias

Interpolated onto the shared log-radius window (r = 0.977..1.063) the four
ladders lie on one curve:

| n | s(r) across the shared window |
|---|---|
| 25,000 | 27.4 → 37.8 |
| 50,000 | 27.5 → 37.6 |
| 100,000 | 28.5 → 38.3 |
| 200,000 | 28.1 → 37.3 |

Mean relative spread across n: **0.0186** (max 0.0373). Dimension is a function
of **scale alone**; larger n simply reaches smaller radii. This is the finding
that matters, and it **retro-validates the premise of R19 and R20** — those
rounds failed on instrumentation and mechanism, but the target they chased is
real.

## 3. Real is scale-dependent — by less than first reported

Per rung, over each ladder's own accessible radius range:

| n | r range | s(r) | ratio |
|---|---|---|---|
| 25,000 | 0.977 → 1.125 | 27.4 → 35.2 | 1.29x |
| 50,000 | 0.953 → 1.103 | 22.9 → 36.9 | 1.61x |
| 100,000 | 0.923 → 1.082 | 18.9 → 35.9 | 1.90x |
| 200,000 | 0.888 → 1.063 | 15.7 → 37.3 | 2.37x |

Across the full band the ladder reaches, s runs from ~15.7 at r = 0.888 to
~37.8 at r = 1.125. The upper end is stable near 36-38 at every n while the
lower end falls with n — the ramp is real and it is what drives G1.

### Controls on the 600k pool: mean beta does NOT separate real from a cascade

Normalized scale dependence `beta = dlog s / dlog r`, all six corpora through
one protocol:

| corpus | beta | s range | G1 |
|---|---|---|---|
| real | **+3.47** | 15.7 → 37.3 | 18–26 |
| bitmap_L90 | **+3.25** | 87.4 → 104.4 | 125–131 |
| bitmap_L60 | +2.90 | 53 → 68 | 71–78 |
| null_lowrank | −2.56 | 63 → 52 | ~98 |
| strat_as_built | −4.88 | 55 → 40 | 81–95 |
| null_gaussian | −10.18 | falling | — |

**This refutes the first version's central claim.** Real and a deep cascade sit
7% apart on beta. Deepening the cascade L60 → L90 moved it *toward* real
(+2.90 → +3.25), the opposite of the prediction that its residual slope was
truncation. "Real is not scale-free" is **not** supported by beta.

What does separate them is **beta's trend with n**:

| corpus | 25k | 50k | 100k | 200k | trend/ln n |
|---|---|---|---|---|---|
| real | +1.80 | +3.25 | +4.03 | +4.80 | **+1.41** |
| bitmap_L60 | +3.09 | +3.29 | +2.99 | +2.22 | −0.42 |
| bitmap_L90 | +2.56 | +3.60 | +3.62 | +3.23 | +0.29 |

Real's scale dependence **strengthens** as n probes deeper; the cascades' does
not. Combined with the level gap (real s 15.7→37.3 and G1 18–26 against the
cascades' 87–104 and ~125), real is distinguished on **trend and level**, not on
mean beta. That is a narrower claim than the original and it is the one the data
carries.

Note also that a *falling* profile is the spherical default: on S^1023 cap
measure saturates toward r = sqrt(2), which is why `null_gaussian` (−10.18) and
`null_lowrank` (−2.56) fall. A rising profile requires structure fighting that,
which real and the cascades both have and the other families do not.

## 4. The stratified family inverts the profile

`stratified_corpus` was the indicated candidate: rounds 3-5 recorded it matching
G1, G3, G7, G8 and failing only G6. Measured against real through an identical
protocol (n = 100k, head-slice pool, so levels are provisional — but the SIGN is
protocol-independent, since real rises on both pools):

| arm (top→bottom dim) | s(r) | ratio | G1 |
|---|---|---|---|
| real | 9.5 → 36.4 | 3.84x | 17.4 |
| as_built 88→38 | 55.2 → 34.4 | 0.62x | 91.2 |
| bracket 38→9 | 86.6 → 40.5 | 0.47x | 139.4 |
| bracket 50→15 | 71.6 → 38.5 | 0.54x | 115.4 |
| wide 36→6 | 93.2 → 43.8 | 0.47x | 147.8 |

Every arm's dimension **falls** with radius where real's rises, and narrowing
the flag toward real's measured spectrum made it *worse* (G1 139 vs 91). Inside
a cone the point sits in a high-dimensional stratum; widening the radius reaches
the lower-dimensional inter-cone layout. That is the reverse of real.

The lesson generalizes past this family: a Whitney flag produces a dimension
**spectrum across points** — which is what G7 measures and what round 4
correctly matched — not a dimension **ramp across scales**. Those are different
objects and matching one does not deliver the other.

## What this changes

1. **The target is a curve.** Admission scores G1 at a few rungs; the object is
   `s(r)` over the resolvable band. A family matching three G1 numbers while
   inverting the profile is matching a projection.
2. **Families excluded by mechanism, not tuning** — but note the grounds have
   changed. Whitney flags are out because they **invert** the profile. Cascades
   are out on **level** (G1 ~125 against real's ~20) and on the finite-depth
   artifact (`R21_BITMAP_PROBE`), *not* on profile shape: the claim that
   self-similarity forces a flat profile was an argument of mine and the
   measurement contradicts it (beta +3.25). The **filament** family
   (`filament_gen.py`, `R21C_FILAMENT_CALIBRATION.md`) is excluded for a third
   and sharper reason: it carries exactly one thread scale, so `s_lo` RISES as
   n resolves the thread (4.2 → 14.6) where real's FALLS (27.4 → 15.7). A single
   characteristic scale saturates once resolved.
3. **The indicated structure is multi-scale with dimension decreasing toward
   finer scales** — hierarchy, not one scale and not scale-free. That was the
   bitmap family's original `dim_decay` intent, and
   [`R21D_DIMDECAY_REFUTED.md`](R21D_DIMDECAY_REFUTED.md) has since closed that
   route too: amplitude decay is simultaneously what makes a level dominate the
   local dimension and what collapses the neighbour distance, so the two
   cascade regimes are exhaustive and both fail.
4. **Conformal maps cannot fix the dimension axis** — they are local
   similarities, so they preserve local dimension exactly, and Liouville's
   theorem restricts them to Mobius transformations in dim >= 3. That same
   inertness makes them the safe way to add a *density* gradient: round 1's
   Poincare `exp_0` conformal factor reached hubness 0.85x where every
   cluster-structured family capped near 0.2x (`generator_search.py:182`).

## Status of the sampling caveat — CLOSED

An earlier version of this document ended by requiring the controls and the
stratified arms to be re-run on the 600k pool before the "not scale-free" claim
could stand. **That has been done** (`scale_probe4.py`, table in §"Controls on
the 600k pool" above, record [`scale_probe4.json`](scale_probe4.json)). All six
corpora — real, `null_gaussian`, `null_lowrank`, `bitmap_L60`, `bitmap_L90`,
`strat_as_built` — went through one protocol on the 600k pool with uniform
per-rung draws.

The re-run **changed the conclusion**: mean beta does not separate real from a
deep cascade (+3.47 vs +3.25), so "real is not scale-free" is not supported by
beta level. What survives is the n-trend plus the level gap, as recorded above.

The stratified table in §4 below is the only part still carried from the
discredited head-slice pool. Its levels are provisional; its **sign is not** —
`strat_as_built` measured on the 600k pool gives beta **-4.88** (s 55.4 -> 39.8
at n=200k), confirming the inversion under matched sampling.

## Next

The profile is not registered anywhere in `spec/`. Using `s(r)` as a *fitting
signal* is fine; publishing a profile-match **claim** requires pre-registering
the statistic and its bands first.
