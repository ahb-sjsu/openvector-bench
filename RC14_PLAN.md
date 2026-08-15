# RC-14: in-distribution placement — the last licensed door

**Status: plan, 2026-08-15.** From `results/RC13_VERDICT.md`: linear
maps bound battery B at ×2.6 because real queries land in local
micro-neighbourhoods a globally-aligned cloud does not occupy. The open
question RC-13 registered: can a declared use of train data **short of
memorization** close it? PREREG §7 licenses train for "fitting
distributional parameters" — and a mixture density IS distributional
parameters. K components over ~300k train rows (≈75 rows per component)
is compression of the density, not storage of the data; the boundary
between them is precisely what this campaign measures.

## Mechanisms

* **M1 (probe) — centroid contraction.** Post-process: move each
  aligned synthetic row partially toward its nearest train k-means
  centroid, `x' = normalize(x + λ(c(x) − x))`, λ and K swept. Cheap,
  answers whether density-ward placement closes g1@B/g8@B at all, and
  at what battery-A cost.
* **M2 (mechanism, if M1 confirms) — keyed mixture skeleton.** The
  generator's coarse placement drawn from the train-fitted mixture
  (component by keyed choice, offset by keyed gaussian within component
  scale) — random-access, bit-exact with hashed frozen artifacts,
  replacing the post-process with a generative form.
* **M3 — G6 variance diagnostic.** The level matches (`R103`); re-measure
  the G6 cells at 10+ subsamples both sides as a *diagnostic* of the
  CI-width failure mode. Any protocol change (registered SUBSAMPLES=5)
  would be a declared symmetric amendment, decided only after the
  diagnostic and disclosed as such.

## Registered predictions and kills

* **P1:** g1@B falls below ×2 at some (λ, K) with battery A within its
  measured margins. **Kill:** if g1@B stays ≥ ×2 even at λ high enough
  to damage A, in-distribution placement by compressed density fails
  and the ×2.6 boundary stands as the final registered result.
* **P2:** the A-cost of λ is smooth and small at the B-closing dose
  (contraction toward density modes is not far from A-preserving at
  small λ).
* **Memorization guard, declared:** K ≤ 4096 and no component may
  average fewer than 32 train rows; the mixture artifact is hashed and
  its per-component occupancy disclosed. Anything finer is out of
  bounds by this plan's own definition.

## Protocol

Validation-stage; sealed rows excluded; real cells reused (r101). One
probe sweep, one mechanism sweep if confirmed, then the full battery
re-run → the seal decision (operator's explicit word) → formal §5
admission. §6 unchanged, waits on scatter. Budget so far: 0.
