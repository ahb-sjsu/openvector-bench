# g1 is invariant to three levers, including turning segmentation off

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12 on NRP A10s. Driver `harness/rc1/gate_check.py`; record
`results/r60.json`. Follows `R59`.

## Two hypotheses, both refuted

`R59` found `g1` at 4.87 against real's 17.23 at the best-rms point, and noted it
was identical across `d_glob`. Two mechanisms were then tested.

**`fil_dim` — refuted.** It sets the within-segment manifold dimension and is
normalised by `sqrt(fil_dim)`, so raising it changes the dimensionality of the
local displacement without changing its scale. That should have lifted `g1` while
leaving `g5` alone:

| fil_dim | g1 | g3 | g5 | g6 | rms |
|---|---|---|---|---|---|
| 48 | 4.87 | 122.1 | 1.354 | 1.932 | 5.30 |
| 72 | 4.84 | 122.4 | 1.353 | 1.899 | 5.46 |
| 96 | 4.84 | 122.4 | 1.352 | 1.825 | 5.63 |
| 120 | 4.83 | 122.5 | 1.352 | 1.809 | 5.53 |

`g1` moves 4.87 → 4.83 across a 2.5x range. `g6` does improve (1.932 → 1.809
against 1.696), which is the one thing the sweep bought.

**Segment size — refuted.** Working back from the estimator, `g1` = 4.87 implies
mean `log mu` ≈ 0.205, so typical `r2/r1` ≈ 1.23 against real's ≈ 1.06. A row in
a 2-row segment has `r1` to its partner and `r2` cross-segment, which is exactly
that pattern, so small segments looked like the cause:

| brk | g1 | g5 | g6 | rms | s(14) | ratio span | log G1 span |
|---|---|---|---|---|---|---|---|
| **real** | **17.23** | **1.369** | **1.696** | — | **16.08** | **+2.397** | **−0.494** |
| 0.000 | 4.31 | 1.626 | 1.559 | 7.55 | 9.3 | +1.944 | **−0.813** |
| 0.050 | 4.55 | 1.574 | 1.740 | 7.39 | 4.8 | **+2.697** | −0.953 |
| 0.090 | 4.70 | 1.479 | 1.857 | 6.06 | 11.5 | +5.514 | −1.090 |
| 0.143 | **4.87** | **1.354** | 1.932 | **5.30** | **16.3** | +1.192 | −1.296 |

**`g1` runs 4.31 → 4.87 across the whole range, including `brk` = 0 — no
segmentation at all.** Segmentation is not what depresses it.

## What that establishes

`g1` is now invariant to **three independent levers**: `d_glob` (`R59`, identical
to 3 s.f.), `fil_dim` (4.87 → 4.83 over 2.5x), and `brk` (4.31 → 4.87 including
off). It sits near 4.3-4.9 regardless.

That makes it a property of the **construction family** rather than a parameter
of it — the same conclusion `R33` reached about the index cascade, arrived at the
same way, by exhausting the levers rather than by argument.

The caveat this arc has earned: "invariant to everything tried" has been wrong
six times here, most recently in `R43`/`R44` where `w_loc` had simply never been
varied. Three levers is not a proof. What is different is that one of the three
turns the mechanism **off** — `brk` = 0 removes segmentation entirely and `g1`
still reads 4.31 — so the invariance is not confined to a corner of the space.

## An unnoticed trade

The `brk` sweep also shows the §3b spans running **opposite** to `rms`:

* `ratio span` +2.697 at brk 0.05 — nearest the +2.397 ± 0.085 band of anything
  measured — while rms there is 7.39;
* `log G1 span` −0.813 at brk 0, closest of the four, where rms is 7.55;
* at brk 0.143, rms is best (5.30) and both spans are furthest out.

So the operating point chosen in `R58` for its curve fit is the *worst* of the
four for the registered §3b criterion. That is worth stating plainly: `rms` and
the registered statistic disagree about which configuration is better.

## What is established

* `g1` ~4.3-4.9 is invariant to `d_glob`, `fil_dim` and `brk` including brk = 0.
* `g6` improves to 1.809 against 1.696 at `fil_dim` 120, its closest measured.
* `g5` holds at 1.352-1.354 across `fil_dim`, so it is decoupled from it.
* The §3b spans and the s(k) rms prefer opposite ends of the break range.

## What is not

* What sets `g1`. Three levers are exhausted; untried are the path level count
  and weight decay, `w_loc`, `log2_pool` and `size_spread`.
* Whether any single configuration can satisfy the §3b spans and the curve
  together — on this evidence they are in opposition.
* `g8` pca_retention, still unmeasured.
