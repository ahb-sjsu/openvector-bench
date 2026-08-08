# P-17cG — the battery run that corrected its own reference

Measured 2026-08-08 on Atlas. Driver
[`r17g_battery.py`](../harness/rc1/r17g_battery.py), cells
[`r17g_battery_cells.json`](r17g_battery_cells.json), scores
[`r17g_scores.json`](r17g_scores.json). Battery A only, 120 cells, capacity
family at α = 0.38 against real re-measured under identical code.

**The candidate is not admitted: 0 of 12 cells meet the count rule, with 22
mandatory-gate failures and 0 unscoreable.**

That headline is close to meaningless, and the run's real output is something
else. Both are below.

## The run is invalid as an admission test, and the fault is the driver's

The candidate's query count was set by `min(N_QUERY*2, max(1000, n//10))`
while real always draws 10,000. The occupancies that produced:

| n | ρ real | ρ candidate |
|---|---|---|
| 25,000 | 4.0 | 1.0 |
| 50,000 | 2.0 | 1.0 |
| 100,000 | 1.0 | 1.0 |
| 200,000 | 0.5 | 0.5 |

Six of twelve cells compared corpora at different query budgets. G5, G6 and G8
are query-dependent, so those comparisons measure the budget difference as
much as the family. This is exactly the failure mode
[`spec/QUERY_BUDGET.md`](../spec/QUERY_BUDGET.md) exists to prevent, committed
by the driver that cites it.

The top two rungs are matched and remain readable.

## What the run actually produced

Re-measuring real under the registered uniform-holdout protocol was
book-keeping, expected to shift the reference slightly. It did not.

| gate | stored, 2026-07-20 | re-measured | change |
|---|---|---|---|
| G1 intrinsic dimension | 51.82 | **19.92** | **2.6× lower** |
| G3 effective rank | 178.98 | 179.81 | 0.5% |
| G5 relative contrast | 1.27 | 1.29 | 1.6% |
| G7 local ID IQR | 27.02 | 22.54 | 17% lower |

The corpus-side gates are unchanged. G3 and G5 agree to within noise, which
establishes that the corpus loading, normalisation and measurement path are
sound and that the G1 change is not a broken pipeline.

What moved is the **query-dependent local geometry**, exactly as PREREG_RC1
predicted when it mandated this re-measurement. Wikipedia arrives topically
ordered, so taking the holdout from the first rows gives a topically
concentrated query marginal, and the two-NN estimator reads the local
dimension of that concentrated neighbourhood rather than the corpus. Uniform
queries give about 20.

**Real corpora's intrinsic dimension is about 20, not about 52.**

## Why that invalidates more than this round

The frozen round-8 family carries `local_dim ≈ 94` and was fitted to reproduce
G1 ≈ 58, because that is what the reference said at the time. The capacity
family inherits it and reads 62 to 67 here, against a corrected target of 20.

At the two matched-ρ rungs, where the driver's bug does not apply, G1 is off
by a factor of 3.3 and fails as a mandatory gate. That failure is real, and it
is **not a property of the capacity variant**. Any member of this lineage
would fail it, including the frozen point itself.

So the correct reading is not that round 18's conclusion was wrong or that the
capacity process is a bad family. It is that **the family was fitted to a
reference that has since been corrected on a mandatory gate**, and the fit
needs redoing against the corrected targets.

## What survives

**Round 18 stands.** It is a within-family contrast measured under a single
consistent protocol at matched ρ, so a shift in the real reference does not
touch it. Cluster count growth lowers hub scaling and its rate does not.

**Round 17c's hub scaling survives, and this was checked rather than
assumed.** Its +0.51 real target comes from
[`r14_real_targets.py`](../harness/rc1/r14_real_targets.py), which samples its
pool across corpus parts with a uniform draw and says why in its own
docstring: "Across parts rather than from the head, because the corpus's row
order is topically clustered and a head slice is a different query marginal."
Base and query pools are disjoint slices of that uniform draw. So the hub
target was never measured under the flawed head-slice protocol, and round
17c's +0.514 ± 0.065 agreement stands against a correctly sampled number.

That the same trap was avoided in one harness and fallen into in another is
worth noting on its own. The corrected sampling was already written down and
reasoned about in July; the battery path simply never adopted it.

**One prediction held.** Before the run I derived that G6 would remain
scoreable at ρ = 0.5 rather than returning NaN, because `Var(c) = ρ + ρ²Var(w)`
stays above the Poisson floor at real's `Var(w) ≈ 0.45`. The scorer reports
**0 unscoreable cells**, so the structural blocker I raised does not bite and
the low-ρ cells carry their gates with a low-signal flag rather than an
exemption.

## What follows, in order

1. **Fix the driver** so the candidate's query budget is drawn by the same
   rule as real's, then re-run. The fix is one line and the run is four hours.
2. **Re-fit the family against corrected targets.** This is the large one.
   The parameter search that produced the round-8 point optimised against
   G1 ≈ 58 and would now be optimising against ≈ 20, which changes
   `local_dim` and probably much else.
3. **Audit every other harness for the same sampling defect.** One harness
   avoided it and one did not, so which of the campaign's targets were
   measured under which protocol is now an open question rather than an
   assumption.

Nothing here is an argument for abandoning the family. It is an argument that
the target moved and the search has to be redone against where it actually is.

## Addendum — the correction is confined to intrinsic dimension

Measured after the fact from the same cells, at n = 100,000, k = 10.

| gate | stored | re-measured | ratio | in band? |
|---|---|---|---|---|
| G1 two-NN intrinsic dim | 51.82 | 19.92 | 0.384 | **moved** |
| G2 ball-growth intrinsic dim | 13.88 | 8.75 | 0.630 | **moved** |
| G3 effective rank | 178.98 | 179.81 | 1.005 | in |
| G4 dims90 | 362.00 | 362.00 | 1.000 | in |
| G5 relative contrast | 1.27 | 1.29 | 1.017 | in |
| G7 local ID IQR | 27.02 | 22.54 | 0.834 | in |
| G8 PCA retention | 0.61 | 0.67 | 1.099 | in |

**Only the two intrinsic-dimension estimators moved.** G1 and G2 both read
local intrinsic dimension off query-to-base distances, and both fell by
roughly the same mechanism. Every other gate is inside its own equivalence
band, with G4 identical to the digit.

This is a coherent signature rather than a scattered one, and it matches the
mechanism PREREG_RC1 described when it mandated the re-measurement. A
topically concentrated query marginal makes neighbourhoods look
higher-dimensional than the corpus is. It does not touch the corpus spectrum,
which is why G3 and G4 do not move, and it barely touches contrast and
retention.

**This makes the re-fit tractable.** The scope is not "re-run the round-8
search". The spectral, contrast, IQR and retention targets are unchanged, so
the parameters governing them do not need to move. What needs re-fitting is
whatever sets local intrinsic dimension, principally `local_dim`, currently
94 and producing G1 of 62 to 67 against a corrected target near 20.

A linear first guess puts `local_dim` near 94 x 20/65, about 29. The
relationship is not guaranteed linear, so this is a one-dimensional search
rather than an arithmetic substitution, but a one-dimensional search is cheap
and can be run before anything larger is contemplated.

The battery re-run should wait for that. Re-running now would spend four hours
confirming a G1 failure the matched-rho cells have already established.
