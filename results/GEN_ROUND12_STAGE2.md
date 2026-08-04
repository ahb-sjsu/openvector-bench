# Round-12 stage 2 — the decoupling check. P-A′ fails, and the presence gate fails with it

Measured 2026-08-03 on NRP, full registered ladder (n = 25k/50k/100k/200k,
pool 420,000, instance 472,500, dim 1024), `screening: false`, 228 cells.
Driver [`harness/rc1/r12_stage2.py`](../harness/rc1/r12_stage2.py), raw output
[`r12_stage2.json`](r12_stage2.json). Instruments imported from stage 1, so
cells are aligned with [`r11v2_real_ref.json`](r11v2_real_ref.json).

Calibration only. Nothing is frozen, no band is adjusted, the sealed rows were
never touched.

**Why this run existed.** The committed `r12_stage1.json` has `grid_c = null`:
the cascade sweep was added to the stage-1 driver after that result was
produced, so the cascade had never been measured on the ladder. Its only
evidence was the unit-scale presence gate at n = 3000, dim = 64 in
[`R12_PREFREEZE_AUDIT.md`](R12_PREFREEZE_AUDIT.md) §6.

---

## The headline: the mechanism is not present at ladder scale

| arm | octaves | KS | μ-spread | gate |
|---|---|---|---|---|
| ctrl (cascade off) | 0.32 | 0.316 | 0.041 | fail, as required |
| **casc** (frac .85, smin .05, α 3) | **1.99** | **0.198** | 0.465 | **fail** |
| casc_a1 (same, α 1) | 1.90 | 0.206 | 0.454 | fail |
| occ | 0.43 | 0.221 | 0.041 | fail |
| both | 2.03 | 0.193 | 0.462 | fail |

The audit's freeze candidate measured 3.02 octaves and KS 0.118 at unit scale
and passed. On the ladder the same knobs give 1.99 octaves and KS 0.198, missing
both thresholds. **The unit-scale gate reading did not transfer.**

This is the single most important line in the run, and it is the reason the
gate was built. Per audit recommendation 5, **P-A′'s failure clause must not
fire.** The clause would promote a failure to "ID n-flatness in this geometry
family requires explicit near-duplicate owners, primary capacity-conjecture
evidence." That inference is only valid with the mechanism present and
adequately powered. It was not present. The gate did exactly the job it was
added to do, one round after being added.

## P-A′: fails, and not marginally

Drift is `d log10(G1) / d log10(n)` minus real's own, so 0 means matching real.
The bound is 0.05.

| arm | G1 drift | G1 level vs real | count-quiet |
|---|---|---|---|
| ctrl | +0.296 | 1.86× | — |
| casc (α 3) | **−0.33** | **0.35×** | no, worst z = 29.4 |
| casc_a1 (α 1) | **+0.083** | **0.25×** | — |

The +0.083 at α = 1 looks close to the bound and must not be read that way.
G1 by n tells the real story:

- ctrl: 34.8 → 37.8 → 40.7 → 43.4 (drifting up, level 1.86× real)
- casc: 13.4 → 8.1 → 5.4 → 4.6 (collapsing)
- casc_a1: 7.1 → 4.5 → 4.2 → 5.6 (already collapsed, then flat)

**The cascade does not flatten intrinsic dimension, it destroys it.** The band
is [0.85, 1.15] and these sit at 0.25 to 0.35. α = 1 has a small drift number
because G1 has bottomed out near 4 to 7, not because the ladder became
scale-free. Reporting +0.083 as near-success would be exactly the scalar-gaming
the campaign caught in round 7, where the optimizer hit a G6 band with the wrong
anatomy.

The audit's own §2 predicted one tension: the frac needed for flatness would
stop being count-quiet. Measured, high frac breaks three things at once — count
quietness (z = 29.4), the scale-free spectrum (KS 0.198), and now the G1 level
itself.

Its mixture arithmetic also proved directionally right and quantitatively
optimistic, exactly as it warned. Predicted residual at f = 0.85 was 0.044;
measured at α = 1 was 0.083, about double, consistent with the caveat that the
figure assumes cascaded rows are *fully* n-flat and the required f is higher if
they are not.

## §6(b) of the audit is falsified, and the α = 1 arm is why

The audit withdrew its α = 1 recommendation on a unit-scale reading: at frac
.85, α = 3 gave KS 0.118 against α = 1's 0.219, so α = 3 was declared the
compensator for the tree-sum distortion. On the ladder:

- KS is effectively identical, 0.198 (α 3) against 0.206 (α 1)
- drift is wildly different, −0.33 (α 3) against +0.083 (α 1)

So α = 3 buys no realized flatness at this scale and is far worse on the target
statistic. The withdrawal rested on a reading that does not hold where the gates
are scored. This arm was added specifically to test that, and it earned its
place — the same way the 3-seed stability check did in round 6.

## P-B′ and decoupling: both move the other's gate

- Occupancy is **not ID-quiet** (worst z = 5.2 at n50k/k10), and its S_k slope
  fails badly at k100 (−0.503 against a 0.05 bound) while k10 (+0.076) and k30
  (−0.03) are near it. The k-profile is the finding, as the failure clause
  anticipated.
- Running both is not quiet against either single arm: z = 4.15 on G1 against
  the cascade alone, z = 21.39 on S_k against occupancy alone.

Decoupling does not hold as registered. But with the presence gate failing this
is provisional too — it is measured with one of the two mechanisms mis-scaled.

## Instrument check

The control's drift, +0.296, is consistent with stage 1's independently measured
fresh-row drift of +0.24/decade. The instrument agrees with prior work, which is
worth stating because everything above depends on it.

## What this licenses next

Not a freeze, and not the failure clause. The cascade has to be made present at
ladder scale before P-A′ can be decided at all. `smin = 0.05` gives 4.3 nominal
octaves and realizes 2.0; the declared range reaches 0.001, which is 10 nominal
octaves, so there is room to buy the missing octaves. Whether the G1 collapse
survives that is the open question, and it is a different question from the one
the audit posed — the collapse is a level failure, not a drift failure.

The reading I would take into that decision, stated as a direction rather than a
conclusion because the clause is blocked: a cascade at 85% attachment behaves
like the near-duplicate planting round 12 set out to replace. Whether that is a
fact about the family or about this operating point is exactly what a
presence-passing run would settle.

Naming note: arms and thresholds here are the author's from PREREG_ROUND12 v2
and R12_PREFREEZE_AUDIT; the α = 1 comparison arm and the pooled draw-noise
scoring are mine.

---

# Addendum — stage 2b: smin does not buy the octaves

Run 2026-08-04. Partial: three of six grid points completed before the run was
killed by a thermal guard on Atlas. The three that completed are the ones that
answer stage 2's question, so they are recorded here rather than held.

Phase 1 reads only the presence gate, at ladder scale (n = 200,000, dim = 1024),
under the rule that nothing is read for drift or level at a setting whose
mechanism is absent.

| frac | smin | nominal octaves | realized | KS | passed |
|---|---|---|---|---|---|
| — (control) | — | — | 0.32 | 0.316 | no |
| 0.85 | 0.05 | 4.3 | 1.90 | 0.206 | no |
| 0.85 | 0.01 | 6.6 | 1.94 | 0.349 | no |
| 0.85 | 0.001 | 10.0 | 1.94 | 0.455 | no |

**The octaves are not buyable with `smin`.** Going from 0.05 to 0.001 adds 5.7
nominal octaves and moves the realized count by 0.04, from 1.90 to 1.94. The
realized spectrum is pinned near 2 octaves. Flatness gets *worse* as smin falls,
KS 0.206 to 0.455, so the finer offsets are not merely invisible, they skew the
distribution.

This closes the option stage 2 left open. The recommendation there was that
`smin` reaches 0.001 in the declared range and the missing octaves should
therefore be purchasable. Measured, they are not. The cascade's failure to be
present at ladder scale is not a mistuning.

**Still untested:** the frac arm (0.60, 0.35, 0.15 at smin 0.01), which is where
the sibling-crowding reading would be confirmed or refuted — that r1 is the
distance to the nearest *sibling* rather than to the parent, so the offset law
never reaches the statistic the gate reads, and lowering frac should raise
realized octaves. That prediction is registered in the driver and unmeasured.

Ops note, recorded because it cost four attempts: this job cannot run on NRP.
Its memory sawtooths between 830 Mi and 9,528 Mi per phase-1 iteration, an 11.5x
swing, against a utilization policy that allows 20-150% of request, a 7.5x
window. Sizing for the peak puts the troughs at 4-14% and the sweep kills it;
sizing for the troughs OOMs. On Atlas it ran until the box reached 92 C under
concurrent load and the guard stopped it.
