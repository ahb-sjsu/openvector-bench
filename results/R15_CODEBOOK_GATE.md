# Round 15 gate — the Dirichlet codebook fails subsample covariance, upward

Measured 2026-08-07 on NRP. Driver
[`r15_codebook_gate.py`](../harness/rc1/r15_codebook_gate.py), raw record
[`r15_codebook_gate.json`](r15_codebook_gate.json). Ladder n ∈ {12.5k, 25k,
50k} at **constant ρ = 4.0**, dim 1024, 3 seeds. Predictions registered in
the driver's docstring before the run; nothing here reads a band.

**P-15A fails. The family is closed, per its own registration — no tuning,
no second parameterization, and P-15B/P-15C were never run.**

## The measurement

| seed | n=12,500 | 25,000 | 50,000 | slope/decade |
|---|---|---|---|---|
| 0 | 7.76 | 8.93 | 9.49 | +2.88 |
| 1 | 7.06 | 8.22 | 11.38 | +7.18 |
| 2 | 8.56 | 7.75 | 7.80 | −1.26 |

(`attractiveness_skew`; registered threshold |slope| ≤ 0.05.)

`tail_excess`, the other invariant readout, on the same cells:

| seed | 12,500 | 25,000 | 50,000 |
|---|---|---|---|
| 0 | 5.12 | 6.04 | 6.66 |
| 1 | 4.82 | 5.78 | 6.75 |
| 2 | 5.15 | 5.77 | 6.64 |

## Finding: the failure runs the wrong way, and that is the useful part

Hub concentration **rises** with corpus size. `tail_excess` is consistent
across all three seeds (within 5% at every cell) and climbs steadily at
about **+0.19/decade**. Real declines at −0.33/decade by the maximum route
and −0.44/decade by the skew route
([`spec/QUERY_BUDGET.md`](../spec/QUERY_BUDGET.md) §3, §3b). The family is
not merely uncovariant; it moves opposite to the target.

The mechanism is plain in hindsight. The codebook is **fixed at r atoms**.
Adding rows at constant ρ piles more of them onto the same attractors, so
popular atoms' neighbourhoods densify and their dominance grows. Real
behaves as though new attractors keep appearing as the corpus grows, diluting
the old ones.

**This refutes the prediction made before the run.** The argument for the
family was that atom popularity is a population law and therefore
subsample-covariant, with the anticipated weakness that it would be *too*
invariant — flat where real declines. Measured, it is not flat: it rises. The
population-law intuition was right that popularity does not sit with owner
rows, and wrong that a fixed codebook is therefore scale-free. A fixed
codebook is itself a fixed set of owners, one level up.

## Second finding: `attractiveness_skew` is unstable on heavy-tailed families

The per-seed slopes span −1.26 to +7.18 while `tail_excess` agrees across
seeds to within 5%. The deconvolution divides by `Var(w)^1.5`, and under a
Zipf popularity law the third moment is carried by a handful of atoms, so the
estimator inherits their draw noise. This is the same ordering the
signal-to-noise measurement already found (tail s.d. 0.005 versus max s.d.
0.163) and it now has a second, independent confirmation on real generated
data.

Consequence for the spec: `attractiveness_skew` remains the correct
*budget-invariant* form of G6 and its ρ-invariance is unaffected, but for
**heavy-tailed corpora it should be reported with a seed spread, and
`tail_excess` preferred as the primary readout**. Rule 6 of
`spec/QUERY_BUDGET.md` already prefers the tail statistic for gates; this
strengthens the case and extends it to diagnostics.

## What this does not license

The obvious repair — let the codebook grow with n, so new atoms appear and
dilute the old, as a Pitman-Yor or Chinese-restaurant process where the atom
count grows as n^α — was named as the likely fix **before** this run, when
the anticipated failure was flatness. It addresses the observed failure too.

It is nonetheless **a new registered prediction, not a continuation of this
one**. The target slope would now be taken from data this round produced,
which is exactly the calibration circularity the campaign keeps paying for.
If it is built, α is registered in advance and the family faces the same gate
first.

## Addendum 2026-08-07: the verdict stands, the reason changes

This gate tested |slope| ≤ 0.05, a flatness criterion, against a target then
believed flat. Real is not flat. Measured in the invariant form it rises at
+0.47 to +0.54 per decade at k = 10, so the correct comparison for this
family is against a rising target rather than against zero.

The verdict is unchanged. The family's slope is +2.93/decade against a real
+0.5, roughly six times too steep, with a per-seed spread from −1.26 to
+7.18 that is itself disqualifying. **What changes is the diagnosis.** The
family was reported above as failing in the wrong *direction*. It does not.
It moves the same way real moves and by far too much, which is a different
statement about the mechanism and a more useful one.

The reading that "a fixed codebook is a fixed set of owners one level up"
survives, but its consequence is not that concentration should fall. It is
that concentration should grow *slowly*, and a fixed codebook grows it fast
because every added row crowds the same attractors. A codebook whose atom
count grows with the corpus would slow that growth, and the growth exponent
is now a fitted quantity with a measured target rather than a matter of
taste.

The gate is not reopened and the family is not retried under this
registration. This addendum records that a successor family has a
quantitative target where none existed before.

## Status

- P-15A — **failed** (+2.93/decade mean against ≤ 0.05).
- P-15B (r/μ decouple G1/G3) — **not run**, gated.
- P-15C (tail buys hubness free) — **not run**, gated.

The G1/G3 decoupling this family was built for remains untested. It may well
hold; the gate closed before it could be measured, which is the gate working
as designed rather than a loss.

## Ops note

Both this job and the round-14 freeze were killed repeatedly by the transient
>2Gi clamp at cpu=4/16Gi. Resubmitting inside the **enforcement-exempt
envelope** (cpu=1, mem=2Gi, ladder top trimmed to 50k) ran to completion in
**3m35s** on the first attempt. The lesson the 1T fleet paid for transfers
directly: fit the exempt envelope rather than fight the clamp with retries.
