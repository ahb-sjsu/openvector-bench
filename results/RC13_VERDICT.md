# RC-13: alignment's limit is the boundary of data-free generation

**Registered close.** Phases A/B (`R102`/`R103`): principal-frame
rotation, mean restoration, and partial spectral matching (gamma 0.25-
1.0), all train-fitted, all measured under the registered battery
against the r101 real cells. Records `results/r102_*`, `r103_*`.

## What alignment achieved

* Rotation: exactly battery-A-invariant (verified digit for digit);
  g8@B 0.07 -> 0.77; g1@B x6 -> x2.8.
* Mean restoration: fixes G2@A (3/12 -> 11/12) - the corpus-side
  ball-growth heat was a missing-mean artifact all along - and squeezes
  g2@B to x1.7-2.1. Best count: rot+mean 12/24 (raw: 9/24).
* Spectral matching: REFUTED as formed - every gamma dose loses more on
  A than it gains on B (12 -> 8 -> 6 -> 2 -> 0 across the ladder);
  battery-B's core (g1@B >= x2.6, g8@B <= 0.77) is invariant across all
  six linear-map variants.
* G6-deconvolution: the LEVEL matches (diagnostic at n=100k/k=10:
  deconv 1.91 vs real 1.97) - the cell failures are estimator variance
  at 3-5 subsamples, a protocol question, not a generator defect.

## The boundary, stated

Train-fittable linear maps close battery B from x6 to x2.6 and no
further. The residual is local, not global: real query vectors land in
specific micro-neighbourhoods of the real cloud, and a data-free
generator can align its coordinates but cannot place its fine structure
at the particular locations real queries expect - doing so would be
fitting the data, not generating it. **Batteries A and B measure
different things: the geometry of a cloud, and geometry as experienced
by real queries. The first is essentially achieved; the second is
bounded away from any generator that does not memorize.** Formal
admission under the registered all-cells rule inherits that bound.

This retroactively vindicates the prereg's design - battery B did work
that no corpus-side measurement in seventeen campaigns could do - and
gives the project's remaining distance its final characterization: not
a mechanism yet unfound, but a definitional boundary between generation
and memorization, now measured at x2.6.

## Standing

rot+mean (12/24 validation) is RC-13's operating point over S1; the
seal stays closed; the sealed section-6 battery continues to wait on
scatter. The open scientific questions in rank order: whether the x2.6
boundary can be tightened by any declared-and-hashed use of train data
short of memorization (e.g., fitting local mixture density, an explicit
research question about where generation ends); G6 protocol variance;
scatter 10 -> 50.

## Budget

RC-13: 7 battery variants x full grid. Validation-stage throughout;
nothing sealed touched.
