# Sharded lookup tables + a designed metric: a registered falsification

**Run:** 2026-07-21, screening grid (n=8000, dim=1024, battery B, k=10), colouring
isolated from the discrete mechanism. Driver
[`harness/generator/codebook_probe.py`](../harness/generator/codebook_probe.py);
numbers [`results/codebook_probe.json`](codebook_probe.json). Train/validation only;
the sealed set was never loaded.

**The question:** "what about lookup tables and some type of Mahalanobis distance?"
The hypothesis was that *discrete, combinatorial* neighbourhoods would let the two-NN
estimator read a low, controllable intrinsic dimension at n=8k — cracking the G1 wall
that the continuous families (EC, stratified) hit — while a designed (Mahalanobis)
spectrum set the effective rank. Pre-registered before the run:

> PRIMARY (make-or-break): G1 tracks `d_latent`; at `d_latent=61`, **G1 ∈ [40, 110]**.
> FALSIFIED if G1 ≥ 200 (same wall), ≤ 8 (duplicate collapse), or flat vs `d_latent`.

## Result: falsified — G1 does not move

| `d_latent` | 20 | 40 | 61 | 90 |
|---|---:|---:|---:|---:|
| **G1 (two-NN)** | 324.8 | 293.5 | 319.8 | 318.4 |
| unique cells | 1.00 | 1.00 | 1.00 | 1.00 |

G1 is **flat vs `d_latent`** and pinned at ~320 (≈5× real's 61.4) — the identical wall.
`unique_cells = 1.00` rules out the duplicate-collapse failure mode: every row is its own
cell, so this is not the ec_ff degeneracy. The mechanistic bet was simply wrong. With M
random-projection shards, two rows that are near in the `d_latent`-dim latent still flip
*many* shards, and each flip is an independent random R^(dim/M) jump, so the local
difference vector spans the ambient space regardless of how low `d_latent` is. Discreteness
controls *which cells exist*, not the ambient dimensionality of a local move.

A diagnostic sweep confirms the wall is robust to the obvious levers — neither the
isotropic noise floor nor the shard count touches G1:

| | noise 0.0 | 0.05 | 0.20 |
|---|---:|---:|---:|
| **shards 8** — G1 | 366 | 367 | 347 |
| **shards 8** — G3 | 100 | 100 | 108 |
| **shards 64** — G1 | 297 | 300 | 320 |
| **shards 64** — G3 | 367 | 368 | 385 |

## What did work (kept, but not sufficient)

- **The Mahalanobis spectrum is a designed quantity, as argued.** Colouring by a power-law
  in a random basis moved G3 across **385 → 41 → 4** (decay 0 → 0.5 → 1.0); shard count moved
  it **100 → 380**. So the effective rank is fully controllable — but it is *coupled* to G1
  through the conditioning of the colouring (aggressive decay inflated G1 320 → 447), so it is
  not a free knob.
- **Hubness works.** Zipf cluster sizes gave G6 = 14.6 (1.54× — if anything, too much),
  a clean, reusable mechanism.

## What this settles — the wall is not a generator trick

The G1 ≈ 320 wall now stands across **three independent families**: elliptic curves (both
readings, [`EC_FALSIFICATION.md`](EC_FALSIFICATION.md)), the Whitney-stratified flag family
(screened negative), and sharded lookup tables. It is robust to nominal latent dimension,
stratum-dimension spectrum, shard count, and the isotropic noise floor. Meanwhile the real
target reads **61 at the same n**, with a near-flat n-slope (+0.036) — real is *not* leaning
on being well-sampled. So the missing ingredient is a property of the real embeddings that
**no from-scratch procedural family has reproduced**, and it is not one of the structural
knobs tried.

A concrete suspect the evidence points to: the two-NN estimate is set by the short-range
ratio `r2/r1`. Real's value (id≈61 ⇒ E[log(r2/r1)]≈0.016) means the *nearest* neighbour is
distinctly closer than the second — consistent with **fine-scale near-duplicate / paraphrase
pairs** (a heavy short-range spike in the pair-distance distribution), which a
uniform-local-density synthetic corpus does not have (its two nearest neighbours are nearly
equidistant ⇒ id reads ambient). This is testable directly on the target.

## Two honest forks

1. **Diagnose the target, then build to it.** Measure the real corpus's short-range structure
   — the `r1` and `r2/r1` distributions and the per-neighbourhood local-covariance spectrum —
   and test the near-duplicate-pair hypothesis. One measurement either hands us the property to
   engineer or definitively rules it out. This is the rigorous move: stop guessing generators,
   characterise what produces id=61.
2. **Invoke the seam clause.** The accumulating evidence (three falsified families, a robust
   wall) is that a procedural generator may not reach the G1 gate. The project charter is
   explicit that this is a reportable outcome: *"if they fail, the family stops at the seam and
   says so."* Scoping the family to the procedural side of the real/procedural seam is a valid,
   registered result — not a hidden failure.

Recommendation: **fork 1 first** — it is one measurement, and it is the only thing that can
either crack the wall or justify fork 2 on evidence rather than exhaustion. Nothing here passes
RC-1; the seal is untouched.
