# Round 16 gate — growing the codebook changes nothing, which falsifies round 15's diagnosis

Measured 2026-08-07 on NRP. Driver
[`r16_py_gate.py`](../harness/rc1/r16_py_gate.py), raw record
[`r16_py_gate.json`](r16_py_gate.json). Ladder n ∈ {12.5k, 25k, 50k} at
constant ρ = 4.0, dim 1024, 3 seeds, α swept over the declared range.
Predictions registered in the driver docstring before the run.

**P-16A fails. The family is closed, as registered. P-16B and P-16C were
never run.**

## The measurement

| `py_alpha` | slope | per seed | spread |
|---|---|---|---|
| 0.20 | +2.940 | +2.95, +3.62, +2.25 | 1.363 |
| 0.35 | +2.534 | +2.74, +2.29, +2.57 | 0.453 |
| 0.50 | +2.860 | +2.68, +2.84, +3.06 | 0.378 |
| 0.65 | +3.825 | +4.76, +3.19, +3.52 | 1.567 |
| 0.80 | +3.188 | +2.60, +5.43, +1.54 | 3.883 |

Target +0.51 ± 0.15. The nearest arm is **5× the target**, and the fixed
codebook of round 15 measured +2.93 — inside the same range. **Growing the
codebook did not move the hub-scaling behaviour at all.**

The gate reports P-16A as failing on both clauses. Only one of them is
decisive. Existence fails unambiguously, since no α comes within a factor of
five. Monotonicity should not be read as evidence here, because the per-seed
spreads reach 3.9 and a non-monotone ordering of noisy means is not a claim
about a controller. The honest statement is that the family has no solution
in the declared range, and whether α orders the slope at all is unresolved.

## What this falsifies

Round 15 concluded that its fixed codebook failed because a fixed set of
atoms is a fixed set of owners, and predicted that letting the codebook grow
would slow the concentration growth. That prediction is now measured and
wrong. The α knob demonstrably controls atom-count growth — nominal 0.3, 0.5
and 0.7 produce measured growth exponents of 0.329, 0.509 and 0.730 — and it
has no effect on the attractiveness-skew slope.

**The number of attractors is not the operative variable.** The operative
variable is the *shape* of the popularity law, and both families hold that
shape fixed. Pitman-Yor stick-breaking produces a power-law tail whose
exponent does not depend on the corpus size. Sampling a fixed heavy tail more
deeply reveals more of its extreme, so the observed skewness rises with n at
a rate set by the tail exponent rather than by how many atoms have been
discovered. Discovering atoms faster adds more atoms in the same
proportions, which changes the count and not the shape.

Real rises at +0.51 per decade against these families' +2.5 to +3.8. A corpus
whose attractiveness distribution were a fixed power law would rise the way
these do. Real does not, so real's attractiveness law is not scale-invariant
in shape. Something flattens it as the corpus grows.

## Consequence for the paper

[`paper/bond_metric/main.tex`](../paper/bond_metric/main.tex) §
"Fixed owners fail at every level of abstraction" stated as an operative
lesson that *any construction whose attractor count does not grow with the
corpus will fail subsample covariance, and the direction of the failure is
predictable from whether the attractors are enumerable*. This measurement
falsifies it. A construction whose attractor count does grow, verifiably,
fails identically and in the same direction. The section has been corrected
to state what survives, which is narrower and about shape rather than count.

## What would be worth testing next, and why it is not this round

A popularity law whose tail exponent itself drifts with scale would produce a
slower-rising skew. So would a mechanism in which attractiveness saturates,
so that a popular atom stops accruing rows past some occupancy. Both are
different objects rather than different parameters of this one, and either
would need its own registration with α-style knobs declared in advance.

Neither is attempted here. The registered clause closes the family, and the
value of this round is the falsification, not a successor.

## Status

- P-16A — **failed** (no solution within 5× of target; monotonicity
  inconclusive at the measured noise).
- P-16B (fix not paid for in G1/G3) — **not run**, gated.
- P-16C (seed stability) — **not run**, gated. Worth noting the spreads
  reached 3.9 at α = 0.8, so it would likely have failed too.

## Ops note

The first attempt OOMed a 2Gi worker. Two causes, one substantive. The submit
script inherited a four-point ladder from a stale copy, and the generator
materialised a `(block, s, dim)` gather that is eight times the working set
it needs at s = 8 and dim = 1024. The generator was fixed rather than the run
shrunk, since the inefficiency would have recurred at any larger scale.
