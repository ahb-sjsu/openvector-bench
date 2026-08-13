# Phase C: the alignment kill fires, and the sweep finds the g4 and g6 levers

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-13 on NRP A10s (24 arms, three indexed jobs — the phase's full
envelope). Driver `harness/rc1/phasec.py`; record `results/r64.json`. Executes
`RC1_PLAN.md` Phase C.

## The claim under test, and its pre-registered kill

`R39` measured two discriminators separating real from the then-generator: mean
principal angle between the 36-dim local subspaces of distinct neighbourhoods
(real 68.1°, generator 80.3°), and local/global eff_rank coincidence (real
168/182 against a divergent 176/111). Phase C implemented the indicated
mechanism — correlated direction sets — two ways: `rho` (a cluster-shared
fraction of direction slots, keyed, random-access preserved) and `log2_pool`
swept **down** (a smaller pool forces global reuse; upward was tried in `R43`,
downward never).

Kill, registered in the plan and the task: *angle reaches ~68° with s(53)
unmoved → the discriminator is a correlate, not a mechanism.*

## The kill fires

| arm | angle | s(53) |
|---|---|---|
| **real** | **68.1°** | **28.9** |
| champion (baseline) | 72.3° | 24.0 |
| lp10 + rho 0.6 | **67.4°** | 23.1 |
| lp8 | 62.1° | 24.4 |
| all 24 arms | 62–73° | 21.6–24.6 |

The angle sweeps through and past real's value; **s(53) never moves**, and the
two are uncorrelated across the full grid. `R39`'s subspace-angle discriminator
is a **correlate** of whatever produces real's mid-curve, not the mechanism.
Per the plan, the hyperbolic arrangement moves up the queue for s(53) — it is
now the best-motivated untried mechanism for the one remaining curve defect.

The baseline arm also reproduced Phase B's champion exactly (ratio +2.381,
log G1 −0.475, g1 15.45) — the bit-consistency check across code edits passed.

## What the sweep found anyway: two levers this family lacked

**`log2_pool` is the g4 lever.** dims90: 718 → 442 → 302 → 190 across
lp 13/10/9/8, with real's 359 at lp ≈ 9.5 (measured 370–371). It also pulls g1
toward real (15.45 → 16.67 at lp 8), lands t36 (0.508 vs real's 0.496), and
brings the angle through real's value. Swept upward against g6 in `R43` with
nothing; the informative direction was down.

**`rho` is the g6 lever.** Hubness: 2.020 → 1.824 → 1.758 → 1.740 across
rho 0/0.3/0.6/0.9, toward real's 1.696 — and at rho 0.3 it is essentially free:
both §3b spans remain in band (+2.355 / −0.434), g1 and g5 undisturbed. **The
Phase B champion plus rho 0.3 strictly dominates the Phase B champion** and
becomes the working configuration.

**The rank *level* problem is now isolated.** Local eff_rank sits at ~73–79 and
global at ~92–102 across every arm, against real's 168/182. The local/global
*pattern* — near-coincidence, local slightly below — is now real-like; the
*level* is half, and none of these levers touches it. Recorded for Phase D and
beyond; `d_loc`/`fil_dim` are the natural candidates and were held fixed here.

## The new tension, mapped to its edge

The pool size that fixes g4 shifts the two §3b span crossings apart. At lp 13
they overlap comfortably (Phase B). At lp 10 (rho 0.3, wl 0.6, dg 24), scanning
brk finely:

| brk | ratio span | log G1 span |
|---|---|---|
| 0.113 | **+2.320 IN** | −0.361 (out by 0.025) |
| 0.116 | +2.217 (out by 0.010) | −0.371 (out by 0.015) |
| 0.119 | +2.100 | −0.378 (out by 0.008) |
| 0.122 | +1.941 | **−0.387 IN** (by 0.001) |

The ratio exits at brk ≈ 0.115 and log G1 enters at ≈ 0.121 — a gap of ~0.006
in brk, consistently signed across the bracket, with the closest joint miss
(brk 0.116) **inside single-seed noise of both band edges**. The `w_loc` bridge
is refuted (0.55 collapses the ratio span to +1.43).

## Hand-off to Phase D: two operating points, not one

* **OP-1, spans-first**: lp 13, rho 0.3, brk 0.125, wl 0.6, dg 24 — both spans
  comfortably in band, g6 1.824, g4 717 (2x out).
* **OP-2, gates-first**: lp 10, rho 0.3, brk 0.116, wl 0.6, dg 24 — g4 441,
  angle 67°, g6 1.79, both spans out by 0.010–0.015.

The gaps separating OP-2 from the bands are smaller than single-seed noise, and
`spec/PROFILE.md`'s bands come from block-to-block variance that Phase D will
finally apply to the generator side. **Choosing between these on single-seed
point estimates would be exactly the error this arc keeps recataloguing** — so
both go to the Phase D audit, where the five-pool ladder, the §3 four-rung
ladder, g8, and seed/block error bars adjudicate.

## Budget

24 arms this phase; 64 across Phases A–C. All within the plan's per-phase
envelope of one to three sweeps.
