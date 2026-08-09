# Structural near-duplicates produce the ramp, but not the dimension level

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-09. Driver
[`harness/rc1/duplicate_structure.py`](../harness/rc1/duplicate_structure.py),
record [`duplicate_structure.json`](duplicate_structure.json). Targets are real's
measured ratios at matched rungs (`small_rung_targets.json`, identical protocol).

## The hypothesis under test

`R26_LEARNED_EMITTER.md` found that a per-row map of hash noise cannot produce
a rising profile even when 262k parameters are optimised directly against the
geometry, and argued a mechanism: rows are iid draws from one pushforward, and a
smooth map is locally linear at small radii, so local dimension tends to the
Jacobian rank — **high** at small r, falling as curvature bites. Real's *rising*
profile needs the opposite: neighbourhoods that are **low**-dimensional at small
radius, i.e. nearby rows constrained to a low-dimensional set — same article,
paraphrase, near-duplicate. With iid rows those arise only by coincidence; in a
real corpus they are structural.

That was reasoning. This measures it.

## Result 1: duplication produces the ramp, and multi-scale beats single-scale

Base is an isotropic Gaussian — measured *falling* — so any rise is attributable
to duplication alone.

| construction | trend |
|---|---|
| isotropic Gaussian base | +0.086 |
| **flat** duplication (one level), f = 0.6 | +0.527 |
| **recursive** duplication (tree), f = 0.6 | **+1.102** |
| *target (real)* | *+0.978* |

Two things follow. Structural duplication takes a flat corpus from +0.086 to
+1.10, so **R26's mechanism holds**. And recursive duplication beats flat by 2x
at matched fraction — exactly what `R21C` predicted, since one duplicate scale
saturates once resolved while a recursive tree has no single scale to exhaust.

## Result 2: with a low-dimensional base, the trend matches exactly

Duplication alone crushes G1 to ~1 (near-duplicates drive `r1` toward zero)
while the isotropic base sits at G1 ~300 against real's ~17 — wrong in both
directions. Real is low-dimensional at base **and** carries duplicates, so both
were combined.

| arm | ratios @ 5k / 10k / 20k | trend | G1 |
|---|---|---|---|
| **target (real)** | 1.576 / 2.151 / 2.932 | **+0.978** | 18.8 / 17.4 / 17.0 |
| lowdim20 rec f=0.6 s=0.15 | 0.920 / 1.247 / 2.299 | **+0.995** | 9.5 / 5.6 / 3.5 |
| lowdim40 rec f=0.6 s=0.3 | 0.931 / 1.171 / 2.278 | **+0.972** | 11.2 / 6.0 / 3.5 |
| lowdim20 rec f=0.4 s=0.3 | 0.592 / 0.677 / 0.938 | +0.249 | 33.9 / 14.0 / 6.1 |

**Two arms hit the trend essentially exactly.** No construction in twenty-two
rounds has matched it before; every registered family produces a *falling*
profile at every rung, and the learned emitter converged at +0.057.

## The remaining gap, precisely stated

**G1 falls far too steeply.** Real's G1 is nearly flat across these rungs —
exponent **−0.073**. The duplicate constructions run **−0.72 to −1.24**, ten to
seventeen times steeper. And the two properties trade off: the arm whose *mean*
G1 is almost perfect (18.0 against 17.7) has trend +0.249, while the arms with
the right trend collapse to G1 3.5.

The cause is diagnosable rather than mysterious. In this recursive process the
duplicate *fraction* is fixed, so as n grows the tree deepens and near-duplicate
pairs accumulate at ever-smaller separations, crushing `r1`. In a real corpus,
adding documents adds *more* near-duplicates without making existing ones
closer — the duplicate density per unit n is roughly invariant. **The duplication
process must be scale-free in n, and this one is not.**

## Follow-up: the G1 gap does not close, and the tension is structural

Three further sweeps (2026-08-09, `dup_heavytail.json`, `dup_cosine.json`) tried
to fix the G1 slope. None did, and together they locate the problem.

**Heavy-tailed separations — refuted.** Drawing sigma from a lognormal was
predicted to leave most points without an ultra-close neighbour. It does the
opposite: the *small*-sigma tail creates more extremely-close pairs while large
-sigma duplicates simply become ordinary points. Raising tau increases the trend
(+1.17 -> +1.63) and *steepens* the G1 exponent (-0.66 -> -0.93).

**A parameterisation defect found on the way.** `sigma` is not a relative scale:
a base_dim-20 source row has norm ~4.5 while a sigma-perturbation in 1024 dims
has norm 32*sigma, so sigma=0.15 already exceeds the signal (parent-child cosine
~0.68) and means something different at every base_dim. Re-parameterising by the
**parent-child cosine** makes the knob comparable to the data — real's 4-NN sits
at r = 0.93, i.e. cosine ~0.57.

**Cosine sweep — the tension made explicit.**

| duplicate tightness | G1 exponent (target −0.073) | G1 level (target 17.7) |
|---|---|---|
| cos 0.95 (tight) | **−0.17 to −0.20** | 2.3–3.6 |
| cos 0.57 (loose) | −0.70 to −0.91 | **9.1–10.1** |

Tight duplicates fix the slope and destroy the level; loose duplicates do the
reverse. Meanwhile the trend *overshoots* nearly everywhere (+0.74 to +8.07) —
it is the easy quantity here, not the hard one.

**Across roughly forty arms in three parameterisations, no configuration exceeds
G1 ~10.3 against a target of 17.7.** The base alone sits near 20 and every
duplicate pulls G1 down, so hitting 17.7 requires few duplicates — and few
duplicates means no ramp. That is a structural trade-off, not a tuning problem.

So the honest status of this family: it matches **one** of the three registered
quantities, does so easily to the point of overshooting, and cannot reach the
other two at the same time. The ramp mechanism is confirmed; the family built
around it is not sufficient.

## Where that leaves the eighth family

Three constraints must now hold simultaneously, and each is measured rather than
assumed:

1. **Low-dimensional base** — an isotropic base gives G1 ~300 against ~17.
2. **Multi-scale recursive duplication** — single-scale saturates (`R21C`), and
   recursive beats flat 2x here.
3. **n-invariant duplicate density** — otherwise G1 falls 10-17x too fast.

All three are cheap and compose with `bitmap_gen`: a low-dimensional base is a
fixed random projection, and duplication needs only a hash from row index to a
source row plus more hash noise. No training, no transcendentals.

**The open engineering question is random access.** Recursive duplication is
exactly the row-to-row dependence that makes O(1) emission non-trivial: row *i*'s
source must be derivable from *i* alone. A hash to an earlier index works, but
the resulting ancestry chain has depth, so emitting one row means walking it —
O(depth) rather than O(1). Whether depth stays bounded at 10¹² is unresolved and
is the thing to settle before this family is worth registering.

## Process note

The first version of this run ranked arms by *maximum trend* and duly crowned a
degenerate arm — `recursive f=0.85`, whose ratios of 1057 and 301 come from
near-zero radii. Ranking now scores distance to target on trend **and** level
jointly and rejects arms with ratios above 20 as numerically degenerate. This
was the sixth time in one session that a convenient summary statistic produced a
confident wrong answer; the fix, each time, was to score what the spec scores.
