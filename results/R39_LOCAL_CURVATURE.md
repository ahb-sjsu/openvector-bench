# Real is curved, the generator already is too, and the difference is alignment

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-10. Driver `harness/rc1/curvature_probe.py`; record
`results/curvature.json`. Follows `R38`.

## The conjecture under test

`R38` closed with a question that would have decided the family outright:
whether real's effective rank of 182 alongside an intrinsic dimension of ~36
requires curvature that **no union of linear patches can supply**.

The discriminator is local PCA against intrinsic dimension. TwoNN and `s(k)`
measure dimension from distance ratios; PCA measures linear extent. For a union
of linear patches of intrinsic dimension d, local PCA rank is ~d. For a curved
manifold the patch bends out of any single subspace and local PCA rank exceeds
d, even locally.

Measured on 200 neighbourhoods of 500 points each:

| | local eff_rank | local dims90 | variance in top 36 | mean subspace angle |
|---|---|---|---|---|
| **real** | **168.4** | **184** | **0.496** | **68.1°** |
| generator, d_glob 90 | 175.9 | 217 | 0.530 | 80.3° |
| generator, d_glob 250 | 175.5 | 217 | 0.531 | 80.3° |

## Real is curved — and so is the generator

Real's local PCA rank is 168, essentially its global 182, while its intrinsic
dimension is 16–36. **Half its local variance lies outside the top 36
directions.** Real neighbourhoods are emphatically not low-dimensional linear
patches.

But the generator matches that closely — 175.9 against 168.4 on local eff_rank,
0.530 against 0.496 on top-36 variance. Because each article draws `fil_dim`
directions from a shared pool of 8192, its neighbourhoods span many directions
too.

**So the conjecture is refuted.** A union of patches drawn from a direction pool
already reproduces real's local spectral structure. Curvature is not the
obstacle, and `R38`'s proposed reason for closing the family does not hold.

## The difference is how patches align

The one column that separates them is the mean principal angle between the
36-dimensional local subspaces of *different* neighbourhoods: **68.1° for real
against 80.3° for the generator**, where 90° is orthogonal.

Real's neighbourhoods **share structure**. The generator's article directions are
drawn independently from the pool, so distinct articles land nearly orthogonal.

This is consistent with the global-versus-local rank pattern, which is the more
telling comparison:

| | local eff_rank | global eff_rank |
|---|---|---|
| real | 168.4 | 182.3 |
| generator, d_glob 90 | 175.9 | 111.1 |

Real's local and global effective ranks nearly coincide — the same directions
are in use everywhere, so aggregating neighbourhoods adds little. The
generator's diverge sharply in the *opposite* sense: locally rich, globally
concentrated, because the global `d_glob` subspace carries the between-article
variance while the per-article directions average out.

That is a specific, measured defect with an obvious construction consequence:
article direction sets should be **correlated** — drawn with overlap, e.g.
shared within a super-cluster — rather than independently.

## Consequences for `R38`

`R38`'s tension result stands as measured: `d_glob` moves rank and ramp in
opposing directions, and g5 responds to nothing. But its closing conjecture —
that this reflects an unbridgeable geometric limitation — is now refuted, and
the tension should instead be read as a limitation of *this parameterisation*.
`d_glob` is the wrong knob for rank, because rank should come from alignment
between patches rather than from the size of a shared global subspace. Nothing
in `R38` varied alignment; it was not a knob the construction had.

## What is not established

* That correlating article directions closes the rank gap without disturbing the
  ramp. It is the indicated next step and is untested; `R38` is a standing
  warning that quantities in this family move together.
* What drives g5. It remained at 2.67 through every variation in `R38` and was
  not measured here.
* Whether the 68.1° figure is stable — it comes from 20 subspace pairs on one
  600k block, with no variance estimate, and `R29` established that block-to-block
  variation in this corpus is not negligible.
