# Round-12 v2 pre-freeze audit — feasibility of P-A′ before it is frozen

**Status: ANALYSIS ONLY. Nothing here is a measurement.** No sweep was run and
no registered content is decided. Filed 2026-07-28 against
[`PREREG_ROUND12.md`](PREREG_ROUND12.md) v2 (DRAFT, `0eed599`) and the cascade
implementation in `hier_r12_corpus`. The purpose is narrow: r11 v1 and r12 v1
were each drafted with a precondition that had no solution in the declared
family, and both were discovered *after* the fact. This checks P-A′'s
arithmetic against the committed stage-1 numbers **before** the freeze, since
after the freeze the failure clauses bind.

Everything below is derived from numbers already in the repo
([`R12_STAGE1_RESULT.md`](R12_STAGE1_RESULT.md), the declared parameter ranges,
and the code) plus the definition of the TwoNN estimator. Where a claim needs
measurement to settle, it is labelled as such.

---

## 1. The mixture arithmetic: P-A′ likely needs `cascade_frac ≳ 0.8`

The maximum-likelihood TwoNN estimator is `d̂ = N / Σᵢ log μᵢ`, so

    1/d̂ = mean over rows of log μᵢ

is a **linear average over rows**. The cascade re-draws a fraction `f =
cascade_frac` of each patch's seed rows by attachment; the remaining `1 − f`
are untouched `_graded` draws whose n-drift stage 1 measured at **+0.24/decade
and showed to be mechanism-invariant** across the entire gradient sweep.

If cascaded rows are perfectly n-flat and fresh rows keep their measured drift,
then in `1/d̂` space the surviving drift is `(1 − f) × drift_fresh`. Setting
that against P-A′'s own bound:

    (1 − f) · 0.24 ≤ 0.05   ⇒   f ≳ 0.79

**Consequence.** P-A′ as written is reachable only in the top ~12% of
`cascade_frac`'s declared range `[0.0, 0.9]`. A sweep grid centred on the value
the unit test exercises (`cascade_frac = 0.5`, which by this arithmetic leaves
≈ 0.12/decade — over twice the bound) would fail P-A′ **for an arithmetic
reason rather than a mechanistic one.**

Caveats, stated honestly: the drift bound is quoted in `d̂`-ratio space in the
prereg while the linearity above holds in `1/d̂` space, so 0.79 is a
first-order figure, not a threshold; and it assumes cascaded rows are *fully*
n-flat, which is the very thing P-A′ proposes to test. If cascaded rows are
only partly flat, the required `f` is **higher**, not lower. The direction of
the correction is unambiguous even though the constant is soft.

**Recommended before freeze:** state the sweep grid for `cascade_frac`
explicitly and make sure it reaches ≥ 0.85, or widen the declared upper bound.

## 2. This puts P-A′ and count-quietness back in tension

The r11 finding was that one mechanism was doing two jobs, and the whole r12
architecture is a bet on decoupling. But §1 implies the cascade must be the
**dominant** structure inside every patch (≈ 80–90% of seed rows), not a light
perturbation. Count-quietness has so far been checked at `f = 0.5`
(`test_r12_cascade_builds_the_graded_ladder`, unit scale, "count tail within
noise").

At `f = 0.9` almost every row in a patch is a descendant of ~10% of rows, and
parents are chosen uniformly from *all* earlier rows, so in-degree in the
attachment tree is roughly geometric rather than flat. Whether that leaks into
the kNN count tail is a measurement, and the decoupling check (stage 2) is the
right place for it — but note it must be run **at the `f` that P-A′ actually
requires**, not at `f = 0.5`. A stage-2 pass at `f = 0.5` would not license the
operating point P-A′ needs.

**This is the specific way H12's premise could fail**: not because either
mechanism is wrong, but because the *amount* of cascade needed for G1
n-flatness is large enough to stop being count-quiet.

## 3. Two declared ranges contradict P-A′'s own mechanism statement

**(a) `cascade_smin` upper bound vs the "≥ 3 scale octaves" precondition.**
P-A′ requires "a cluster-in-cluster cascade over ≥ 3 scale octaves". Offsets
span `[smin, 1] × patch radius`, i.e. `log2(1/smin)` octaves. The declared range
is `("cascade_smin", 0.001, 0.3, 0.02)`, and `smin = 0.3` gives **1.74
octaves** — inside the declared range but outside P-A′'s stated precondition.
The ≥ 3-octave requirement implies `smin ≤ 0.125`.

**(b) `cascade_alpha ≠ 1` breaks the scale-freedom the mechanism claim rests
on.** The offset law is `s = smin^(u^alpha)`, `u ~ U(0,1)`. At `alpha = 1`,
`log s` is uniform — genuinely scale-free, which is exactly what the claim
"on a scale-free pair-distance distribution the TwoNN μ-statistics are
subsample-invariant" requires. At `alpha ≠ 1` the log-scale density is warped
(`∝ u^(1−alpha)`) and the spectrum is no longer scale-free. The declared range
is `[0.3, 3.0]`.

**Recommended before freeze:** restrict the P-A′ grid to `smin ≤ 0.125` and
test the mechanism claim at `alpha = 1`, declaring `alpha` a robustness
dimension that is *not* part of the claim. Otherwise a sweep can wander into
settings where the mechanism is absent by construction and report that as
mechanism failure.

## 4. Why the ambient process is *not* the threat (a concern I withdrew)

Worth recording because it is counter-intuitive and it changes what the failure
modes are. The obvious worry is that cascade offsets are **absolute** (`s ×
patch radius`, n-independent) while ambient within-patch spacing thins as
`n^(−1/d_local)` — which would reproduce the r11 "fixed absolute scale in a
thinning reference" pathology in a new guise.

It does not, because `local_dim` is 57 (default; range 8–120). Ambient spacing
scales as `n_seed^(−1/57)`: going from 100 to 10,000 rows per patch changes it
by about **8%**. In this dimension the ambient scale is nearly n-invariant, so
it contributes almost no drift and cannot swamp the cascade. Both terms in
`μ = r2/r1` are n-quiet for a cascaded row (`r1 = s·pr` by construction,
`r2 ≈ ambient ≈ 0.85–0.92·pr`), which is the actual reason the mechanism is
plausible.

This also suggests where the measured +0.24/decade in the *fresh* rows comes
from: not from geometry thinning but from TwoNN's own finite-sample negative
bias shrinking as n grows. If that is the true source, then P-A′'s mechanism is
better described as *saturating `r1` below the estimator's bias regime* than as
a property of the geometry — and the real corpus's n-stability would be
evidence that it, too, carries a scale-free near-neighbour ladder. Testable,
not tested here.

## 5. The failure clause is currently too strong for what the sweep can show

P-A′'s failure clause reads: P-A′ fails ⇒ "ID n-flatness in this geometry
family requires explicit near-duplicate owners; that is the round-9 suspect
confirmed at mechanism level and **primary capacity-conjecture evidence**."

That inference is only valid if the cascade was actually *present and
adequately powered* when it failed. Given §1 and §3, a failure could instead
mean: `f` was too small (arithmetic), `smin` was too large (fewer than 3
octaves), or `alpha ≠ 1` (spectrum not scale-free). Those are implementation
and grid facts, not facts about the geometry family — and the clause as written
would promote them to primary evidence for a conjecture.

**Recommended before freeze — pick one:**

1. **Narrow the clause** to "this cascade family at the declared grid", leaving
   the capacity-conjecture inference to a later round; or
2. **Add a mechanism-presence gate** that must pass before the clause can fire:
   a direct check that the realized structure has the property the claim is
   about, so failure is unambiguous.

Option 2 is cheap and is the stronger science. The gate should verify, at unit
scale and at the freeze-candidate setting: (i) the realized base→base pair
distances are log-uniform over ≥ 3 octaves (a KS or slope test on
`log r1`, not just the q01/median ratio the current test uses); and (ii) the
per-row neighbour **ladder** `r_{j+1}/r_j` is scale-free over the first few `j`,
since μ is a ratio of the first two rungs and a mechanism that fixes only `r1`
does not necessarily make the ratio n-invariant. The existing
`test_r12_cascade_builds_the_graded_ladder` establishes that the cascade
*changes* the ladder; it does not establish that the ladder is *scale-free*,
which is the property P-A′'s mechanism claim actually names.

---

## 6. Gate built and run — measured results (2026-07-28)

The item-5 gate is implemented as `geometry.cascade_spectrum_gate` and
exercised by `test_r12_cascade_passes_its_mechanism_presence_gate`. It reports
three readings on the sub-ambient rows the cascade creates (cut at the
cascade-off median r1): octaves spanned, KS distance of `log2 r1` from uniform
(flatness ⇒ scale-freedom), and the spread of `log2 μ`. Thresholds were fixed
a priori from the prereg text — ≥ 3 octaves, KS ≤ 0.15, μ-spread ≥ 0.5 — and
**were not adjusted after seeing these numbers.** Unit scale (n = 3000,
dim = 64, seed 19), run on Atlas.

| setting | octaves | KS | μ-spread | gate |
|---|---|---|---|---|
| cascade OFF (control) | 0.74 | 0.463 | 0.178 | **fail** (as required — gate is not vacuous) |
| frac 0.50, smin 0.05, α 1 | 3.02 | 0.134 | 0.907 | **pass** |
| frac 0.85, smin 0.05, α 1 ← audit's freeze candidate | 3.05 | **0.219** | 0.705 | **fail** (flatness) |
| frac 0.85, smin 0.30, α 1 | **2.18** | 0.141 | 0.472 | **fail** (octaves) |
| frac 0.85, smin 0.05, α 3 | 3.02 | **0.118** | 0.708 | **pass** |

Three consequences, one of which reverses a recommendation above.

**(a) A new tension, and it is the r11 shape again — caught before freeze this
time.** The operating point §1's arithmetic requires (`frac ≳ 0.79`) is
precisely where the realized spectrum stops being log-uniform: KS climbs
0.134 → 0.219 as frac goes 0.5 → 0.85. The mechanism is plausibly that with
only ~15% fresh parents, most rows attach to already-cascaded rows, so a pair
distance becomes a **sum of offsets along the tree path** rather than a single
log-uniform draw — and sums of log-uniform variables concentrate toward their
largest term. So the same knob again buys one property at the cost of another:
`frac` trades ID-flatness reach against spectrum scale-freedom. This is pinned
as a characterization assertion in the test so it cannot be lost.

**(b) Item 4 is WITHDRAWN, and inverted: `alpha` is the compensator, not a
threat.** The audit argued the mechanism claim holds only at `alpha = 1`
because that is where the *offset law* is log-uniform. Measured, the opposite
matters: at frac 0.85 the *realized* spectrum is flatter at `alpha = 3`
(KS 0.118) than at `alpha = 1` (0.219). The claim in P-A′ is about the
pair-distance distribution the μ-statistics actually see, not about the input
draw, and warping the input law evidently offsets the tree-sum distortion at
high frac. **My a priori reasoning conflated the input law with the realized
spectrum and was wrong.**

**(c) There is therefore a candidate operating point that satisfies both
constraints at once: `frac 0.85, smin 0.05, alpha ≈ 3`** — high enough frac for
§1's mixture arithmetic, and passing the presence gate (3.02 octaves,
KS 0.118, μ-spread 0.708). That is the setting I would take into the stage-2
decoupling check. Whether it is *count-quiet* at frac 0.85 is unmeasured and is
exactly what stage 2 must answer.

**Item 3a is confirmed by measurement:** `smin = 0.30` yields 2.18 realized
octaves, below P-A′'s own ≥ 3 floor. (Predicted 1.74 from the offset law alone;
the realized value is higher because ambient structure contributes to the
sub-ambient tail. The conclusion is unchanged.)

**What this does not do.** None of the above measures G1 n-drift across the
ladder, so P-A′ remains entirely undecided and unfrozen. These are precondition
readings of the same kind as the existing unit-scale mechanism tests, which the
prereg explicitly treats as not-the-registered-question.

---

## Summary of recommendations (all pre-freeze, all the author's call)

| # | Item | Status after §6 | Why it matters |
|---|---|---|---|
| 1 | Sweep grid for `cascade_frac` must reach ≥ 0.85 | **stands** | Below ~0.8, P-A′ fails on arithmetic, not mechanism |
| 2 | Run the stage-2 decoupling check at the `f` P-A′ needs | **stands, now sharper** | A pass at `f = 0.5` does not license `f = 0.85`; count-quietness at high frac is the open question |
| 3 | Restrict grid to `smin ≤ 0.125` | **confirmed by measurement** (2.18 octaves at 0.30) | `smin = 0.3` violates P-A′'s own ≥ 3-octave precondition |
| 4 | Test the claim at `alpha = 1`; declare `alpha` robustness-only | **WITHDRAWN — inverted** | I conflated the input offset law with the realized spectrum; `alpha ≈ 3` is what makes the realized spectrum flat at high frac |
| 5 | Add a mechanism-presence gate before the failure clause can fire | **DONE** (`cascade_spectrum_gate` + test) | A P-A′ failure is now separable from mechanism-absent |
| 6 | Take `frac 0.85 / smin 0.05 / alpha 3` into stage 2 | **new** | The only setting measured to satisfy both the mixture arithmetic and the presence gate |
| 7 | State P-A′'s mechanism claim over the **realized** pair spectrum, not the input draw | **new** | The μ-statistics see the realized distribution; §6(b) shows the two can disagree sharply |

None of these adjust a band. Items 1–3 and 6 are grid/scope declarations, 5 is
an added gate, and 7 is a wording precision — all strictly *tightening* moves of
the kind the amendment rule permits on a draft. Item 4 is a withdrawal of my own
recommendation on measured evidence.
