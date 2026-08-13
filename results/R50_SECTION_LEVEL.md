# The k=14 dip resists a third mechanism, and the emitter gets its random-access primitive

**Exploratory, not a registered round.** No admission claim, seal untouched.
Measured 2026-08-12. Drivers `harness/rc1/section_probe.py`; records
`results/section.json`. Follows `R49`.

## Part 1 — an index-contiguous section level, refuted

`R49` fixed the middle of `s(k)` with a multi-level arrangement and left two
defects, of which the k = 14 dip was the larger: `s(14)` sits at 8.2 against
real's 16.1, and it was insensitive to every arrangement change.

`R30` suggested a mechanism. Real's index correlation decays smoothly out to gap
**~128 rows** — about five 23-row articles — so real has index locality *above*
the article. Every round since `R36` gave adjacent articles zero correlation,
because super-clusters are hash-assigned (`R35` established that above-article
structure is not index-local, but that was measured on *article centres*, which
is a coarser statement than "no correlation at gap 24-128").

Adding a section level: `sec_arts` consecutive articles, contiguous in index,
sharing a component of weight `w_sec`.

| sec_arts | w_sec | g5 | eff_rank | g1 | g6 | ratio | **rms** | s(4) | **s(14)** | s(53) | s(500) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **real** | | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** | — | **8.8** | **16.1** | **28.9** | **35.7** |
| — (`R49` best) | — | 1.675 | 198.6 | 13.10 | 1.671 | 4.608 | **10.84** | 11.5 | 8.2 | 22.8 | 53.0 |
| 5 | 0.4 | 1.731 | 213.4 | 13.26 | 1.690 | 5.060 | 12.24 | 11.1 | 7.9 | 24.4 | 56.0 |
| 5 | 0.8 | 1.893 | 248.3 | 13.36 | 1.734 | 5.729 | 14.77 | 10.9 | 7.7 | 20.5 | 62.4 |
| 12 | 0.6 | 1.803 | 227.0 | 13.25 | 1.709 | 5.340 | 12.96 | 10.9 | 8.0 | 26.3 | 58.2 |

**Every arm is worse, and the dip deepens rather than fills** — 8.2 → 7.9 → 7.7
as `w_sec` rises, monotonically. Widening the section to 12 articles does not
help either.

So the k = 14 dip has now resisted three distinct mechanisms:

1. distributed article extents (`R47`),
2. nested arrangement levels (`R49`),
3. index-contiguous sections (here).

Adding correlated structure at *any* scale near the article makes it worse. That
is consistent with the dip being a **gap** rather than a deficit: extra
correlated mass at a nearby radius pulls neighbours inward and widens the void
beyond, rather than filling it. What would fill it is mass at *intermediate*
radius with no accompanying tightening — which none of the three supplies.

Recording this as a bounded negative. Three mechanisms is not a proof of
impossibility, and this arc has four instances of "nothing moves X" being wrong.

## Part 2 — `hashrng`, the random-access primitive

Task 2 needs the emitter to compute row `i` without generating row `i − 1`, and
to do so byte-identically on any platform. `R48` fixed the float reproducibility
of the *existing* builders; this supplies the primitive a properly random-access
emitter needs.

`openvector_bench/hashrng.py` generalises the pattern `bitmap_gen` established
and `learned_gen.hash_noise` implemented for `(row, column)`, to arbitrary key
tuples — so a construction with nested levels can key each independently:

* `splitmix64` — the finaliser, pure integer, bijective on uint64;
* `mix_keys(*keys)` — order-dependent folding, so a level index cannot alias a
  row index;
* `hash_uniform`, `hash_gaussian`, `hash_index` — draws keyed on any tuple.

Gaussians use **Irwin-Hall** (12 uniforms minus 6) rather than Box-Muller:
`log`, `sqrt` and `cos` route through libm, which is not bit-identical across
platforms. The cost is truncation at ±6σ, which is immaterial for geometry and
is asserted in the tests rather than left implicit.

Verified: unit variance (mean 0.0028, sd 1.0009 over 160k draws); **row 10¹⁴
computed alone equals its value in a batch**; chunk-invariant across a 137-row
chunking; key order respected. And byte-identical across toolchains —

| | Windows / numpy 2.3.5 | Linux glibc2.39 / numpy 2.4.4 |
|---|---|---|
| `hash_gaussian` | `62b259397aba146e` | `62b259397aba146e` |
| keyed by (level, row) | `7e9525c2e34c62a4` | `7e9525c2e34c62a4` |
| `hash_uniform` | `6f3c3778ae962f8b` | `6f3c3778ae962f8b` |
| `hash_index` | `a02ec6f10d5cf153` | `a02ec6f10d5cf153` |

## What is established

* An index-contiguous section level does not fill the k = 14 dip; it deepens it,
  monotonically in weight, at two section widths.
* The dip is insensitive to correlated structure added at any scale tried near
  the article, which is the signature of a void rather than a deficit.
* The emitter has a verified integer-exact, random-access randomness primitive
  meeting the `DISTRIBUTION.md` §3 contract.

## What is not

* Whether anything fills the dip. Three mechanisms are refuted and no fourth is
  designed.
* The port itself. `hashrng` exists and is tested, but no generator uses it yet —
  the geometry is still moving, and porting a moving target was judged premature.
* Emission rate, still unmeasured, and `reproducible_matmul` makes it worse.
