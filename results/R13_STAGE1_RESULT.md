# Round 13 stages 0b and 1 — the codebook closes; the taxonomy survives half

Measured 2026-08-07 on the real Cohere Embed-V3 corpus
(`/archive/tqp_real/wiki1024`, sampled across the 42 parts, 1,000 committed
real queries, dim 1024, train/val only, seal untouched). Drivers
`harness/rc1/r13_stage0b.py` and `harness/rc1/r13_stage1.py`, raw records
[`r13_stage0b.json`](r13_stage0b.json), [`r13_stage1.json`](r13_stage1.json).
Predictions registered in [`PREREG_ROUND13.md`](PREREG_ROUND13.md) v2.

**Three of four registered predictions fail. The codebook programme closes
on the merits. One instrument finding survives and one is refuted.**

## P-13D fails — there is no joint structure to carry

A supervised partition using all eight latent features was compared against
the same procedure restricted to `query_mass` alone: same leaf budget, same
training rows, same held-out rows.

| leaves | joint / query-mass-only MI (k10 / k30 / k100 / rank) | ARI |
|---|---|---|
| 2 | 1.01 / 1.00 / 1.04 / 1.01 | 0.82 |
| 6 | 1.09 / 1.02 / 1.08 / 1.00 | 0.69 |
| 12 | **1.20 / 1.13 / 1.13 / 1.11** | 0.40 |
| 32 (diagnostic) | 1.30 / 1.23 / 1.20 / 1.24 | 0.54 |

Registered threshold was ≥ 1.25× on at least three of four response
variables at K = 12. Measured: **zero of four**, with the best at 1.20.
Seven features of local geometry — density, three neighbour radii, radius
slope, local intrinsic dimension, anisotropy — together add **at most 20%**
to what a single scalar of query exposure already tells you about who gets
retrieved, and only 30% even at a 32-leaf budget well past the ceiling.

Per the registered failure clause: **retrieval response depends on the
latent code essentially through one axis, query exposure.** No quantizer can
rescue a codebook when there is no joint structure for it to carry, and no
third quantizer will be tried. P-13E is moot and also fails on its own terms
(saturation 0.84–0.90 against a 0.90 threshold, ARI 0.40 against 0.70).

**This sharpens round 7 into a stronger claim than it previously made.**
Round 7 established that the G6 number lives in the query marginal. This
measures the complement directly: corpus-side local geometry is very nearly
*irrelevant* to which points get retrieved, once query exposure is known.
Hubness is not mostly-a-query-property; on this corpus it is almost
entirely one.

## P-13B half 1 holds — the five anti-hub categories are real

Points never retrieved at k = 10 were assigned a mechanism of invisibility
by latent rule, then recovered from latent features *without* those rules by
a deliberately weak nearest-centroid classifier on held-out points.

| n_base | slots/point | never retrieved | balanced accuracy | never_asked | low_density | boundary | metric_misfit | legit_antihub |
|---|---|---|---|---|---|---|---|---|
| 2,993 | 3.34 | 26.5 % | 0.611 | **0.499** | 0.029 | 0.091 | 0.072 | 0.309 |
| 7,995 | 1.25 | 55.2 % | **0.718** | 0.327 | 0.066 | 0.125 | 0.072 | 0.409 |
| 19,967 | 0.50 | 75.9 % | 0.684 | 0.257 | 0.091 | 0.133 | 0.085 | 0.434 |

Balanced accuracy clears the registered 0.6 at every corpus size and reaches
**0.718** at the harness convention (n = 8,000 base, 1,000 queries), with
every category recovered above chance (per-category 0.57–0.82 at that
point). The categories are not an arbitrary partition of the lower tail;
they are recoverable from geometry and query exposure alone.

**The sweep is itself a result.** When queries cover the corpus generously
(3.3 slots per point), **half** of all invisible points are invisible
because *nothing asked for them* — `never_asked` is the single largest
category at 0.499. As coverage falls the category deflates monotonically
(0.499 → 0.327 → 0.257) while `legit_antihub` inflates (0.309 → 0.409 →
0.434), because with too few queries the pigeonhole floor manufactures
"anti-hubs" that are nothing of the kind. A generator matched on lower-tail
statistics measured at one query budget would be matched on an artefact of
that budget.

## P-13B half 2 fails — G6 is not blind to the categories

Subsample pairs matched by rejection on both G6 and base-to-base skew differ
in category proportions by at most **1.28×** (n = 3,000), 1.08× at the
harness convention, against a registered ≥ 2× threshold. Corpora that agree
on G6 agree on the anti-hub mix.

Per the registered clause this is reported as good news for the battery and
the independent instrument claim is **withdrawn**: G6 is not blind to the
lower tail, so a lower-tail discriminator is not a missing axis of the
battery. It remains a *descriptive* tool — the categories are real and
measurable — but it is not evidence that the battery underdetermines
anti-hub structure.

One caveat on this half, stated because it bounds the strength of the
negative: matching was by rejection over six random subsamples of one
corpus, so the matched pairs are similar in many ways beyond G6. A stronger
test would match G6 across *structurally different* corpora, which is what
the candidate families were built for. That test is not run here and the
withdrawal is scoped accordingly.

## Status of round 13

- **P-13A** (unsupervised quantization) — failed, [`R13_STAGE0_RESULT.md`](R13_STAGE0_RESULT.md).
- **P-13D** (joint structure) — failed. Codebook programme closes.
- **P-13E** (saturation) — failed, and moot given P-13D.
- **P-13B half 1** (categories separable) — **holds**, 0.718 balanced accuracy.
- **P-13B half 2** (G6 blind) — failed; instrument claim withdrawn.
- **P-13C** (orthogonal control) — gated on P-13A, does not run.

The surviving positive contributions are the sharpened round-7 claim
(corpus-side geometry is nearly irrelevant to retrieval once query exposure
is known) and the anti-hub taxonomy as a descriptive instrument with a
measured query-budget dependence. Neither requires a generator, and both are
reportable as they stand.

## Ops record

Ran on Atlas CPU at 3 threads under concurrent Erebus load; package 0 held
80–81 °C against its 82 °C mark. An earlier attempt at n = 50,000 died
silently with no traceback and no OOM — the identical code exits 0 at
n = 8,000, so the failure was environmental at that scale. A thermal
watchdog written for that attempt was discovered to have been dead from its
first iteration (its `pgrep` returned non-zero before the worker existed,
and `set -e` killed the subshell); it was removed rather than left in place
as decoration.
