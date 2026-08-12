# The geometry generators were not cross-toolchain reproducible; now they are

**Engineering result, not a registered round.** No admission claim, seal
untouched. Measured 2026-08-11. Drivers `harness/distribution/xtoolchain.py`,
`harness/rc1/float_repro.py`; records `results/xtoolchain.json`,
`results/float_repro.json`.

## Why this was worth checking

Closing `R22`'s cross-toolchain gap showed regeneration is exact for
`philox_u8` — 16/16 shards byte-identical across Windows/numpy 2.3.5 and
Linux/numpy 2.4.4 — and the reason is structural: that emitter is **pure integer
arithmetic** over a counter-based bit generator, with no floating point in the
path.

The geometry generators are not. `twoscale_corpus` and `cascade_corpus` use QR
factorisations, normal draws and matrix products throughout. Whether they inherit
the same guarantee is a question, not an assumption, and `DISTRIBUTION.md` §3
makes regeneration a first-class source rather than an optimisation.

## They did not

Same construction, same seed, two platforms:

| | Windows 10 / numpy 2.3.5 | Linux glibc2.39 / numpy 2.4.4 |
|---|---|---|
| QR factorisation alone | `4cbb9cfe…` | `4cbb9cfe…` ✓ |
| full float32 build | `780554a1…` | `4d9cb7e8…` **✗** |
| first value | 0.1064392700791359 | 0.1064392477273941 |

The QR agrees. The divergence appears at the 8th significant digit, which is
float32 rounding.

## The cause is the matrix product, not the RNG

Isolating each operation on identical inputs — same OpenBLAS build on both
machines:

| operation | Windows | Linux | |
|---|---|---|---|
| RNG inputs A, B | `1c56bd3f…` | `1c56bd3f…` | ✓ |
| `A @ B` in **float32** | `f81d6818…` | `a04d9149…` | **✗** |
| `A @ B` in **float64** | `1638aeb2…` | `1638aeb2…` | ✓ |
| explicit rank-1 loop, float32 | `8bfa2e55…` | `8bfa2e55…` | ✓ |

The random draws are identical, so numpy's bit generator is not the problem.
SIMD width and cache blocking differ between the two builds, which changes the
**order of the inner sum**, and float32 has too little precision to absorb the
reordering. Float64 has enough headroom at this reduction length; a fixed-order
accumulation avoids the question entirely.

## Fix

`geometry.reproducible_matmul` accumulates one rank-1 term at a time, in a fixed
order, using no BLAS. Float64 reduction was the alternative and was also
verified, but it relies on f64 headroom being sufficient for the reduction
length — which is a property of the sizes in use rather than of the method, so
the conservative option was taken. The cost is a Python loop over the inner
dimension, which is small in every call site here (`arr_dim`, `fil_dim`,
per-level dimensions).

Applied to the three matrix products in `twoscale_gen.py`. After the change:

| generator | Windows | Linux | |
|---|---|---|---|
| `twoscale_corpus` | `8bb81844a05456cf` | `8bb81844a05456cf` | ✓ |
| `cascade_corpus` | `87224fa52a9a54a5` | `87224fa52a9a54a5` | ✓ |

## What this does and does not settle

**Settled:** the geometry generators now produce byte-identical output across
OS, libc, Python patch and numpy minor version — the same standard `philox_u8`
already met, and the standard `DISTRIBUTION.md` §3 requires of a regeneration
tier.

**Not settled, and these remain open under task 2:**

* **Random access.** The construction is *structured* for it — article is
  `i // 23`, super-cluster a hash of the article, path level `position >> s` —
  but the implementation still materialises whole tables and uses a numpy RNG
  seeded once per corpus. Emitting row `i` without generating its predecessors
  requires porting the draws to `splitmix64` keyed on `(level, index)`.
* **Emission rate.** `DISTRIBUTION.md` §3's cost inversion needs roughly
  10 MB/s/core; unmeasured for these generators, and `reproducible_matmul`
  makes it slower, not faster. The trade may need revisiting if the rate misses.
* Two platforms is not a survey. ARM, a different BLAS vendor, and a
  32-bit target are untested.

## A constraint this places on the geometry work

Any construction that reaches a reduction long enough to exhaust float32 — or
that is tempted back onto BLAS for speed — forfeits the regeneration guarantee.
That is a design constraint on `R47`'s indicated next step (a multi-level
arrangement), not merely a packaging detail to settle later.
