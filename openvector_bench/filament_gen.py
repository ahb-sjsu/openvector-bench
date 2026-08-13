# SPDX-License-Identifier: MIT
"""Filament family: low-dimensional threads in a high-dimensional arrangement.

**Status: EXPLORATORY.** Not registered, not an admission claim, seal untouched.

## Why this shape

`R21B_SCALE_DEPENDENCE.md` measured the target as a curve: real's local growth
dimension RISES with radius, from ~15.7 at r = 0.888 to ~37.8 at r = 1.125, and
the ladders collapse in radius to 1.9% so this is geometry rather than estimator
bias. Four constructions have now been excluded for the same structural reason —
each has a local dimension that is scale-invariant or globally fixed:

* self-similar cascades — flat by construction (`R21_BITMAP_PROBE`);
* Whitney flags — *inverted*, s falls 0.47-0.62x where real rises, because a
  cone is high-dimensional inside and the inter-cone layout is low-dimensional;
* conformal maps — local similarities, so dimension-preserving exactly, and
  Liouville restricts them to Mobius in dim >= 3;
* elliptic / elliptical constructions — flat tori and elliptical distributions
  both fix local dimension globally; the radial profile moves density, not
  dimension.

This family is the **mirror image of the Whitney failure**. Points lie on
`2**log2_filaments` low-dimensional threads (`fil_dim`, a few directions each),
whose centres are scattered across an `arrange_dim`-dimensional arrangement:

    x = c_f  +  scale_f * (u @ B_f),     u ~ N(0, I_fil_dim)

At radii below a filament's extent a neighbourhood runs ALONG the thread and
sees `fil_dim` directions. Past that extent it reaches neighbouring threads,
whose offsets span the arrangement, and the direction count opens up toward
`arrange_dim`. So

    s(r) : fil_dim  ->  arrange_dim

rises, and the crossover radius is a genuine characteristic scale rather than a
depth budget. `scale_spread` gives the per-filament extents a lognormal spread,
which smears what would otherwise be a step into a ramp — real's transition is
gradual, spanning a factor of ~1.27 in radius.

**The null is a scale merge, not a dimension merge.** Setting
`fil_dim == arrange_dim` was tried first and is NOT a null: it removes the
dimension separation while leaving the scale separation (extent 0.15 against a
centre spacing of ~sqrt(2)) intact, and it duly produced a STRONGER rise
(beta +4.79) than the family arm. The correct null raises `fil_scale` until a
thread's extent matches its centre spacing and sets `scale_spread = 0`, so
there is a single scale and s(r) must flatten. A thread extent of
`fil_scale * sqrt(fil_dim)` against a spacing of ~sqrt(2) puts that at
`fil_scale ~ 0.5` for `fil_dim = 8`.

## Scope of this version

Emission uses ``default_rng``, matching every other family in
``generator_search.py``, so it is reproducible per (seed, n) but NOT bit-exact
across platforms and NOT random-access. That is deliberate: random access is a
`DISTRIBUTION.md` requirement and this family is built to be convertible —
row -> filament and filament -> basis are both pure hash lookups, so the
splitmix64 machinery in ``bitmap_gen`` ports directly. The conversion is
deferred until the profile is shown to be worth keeping.
"""

from __future__ import annotations

import numpy as np

from openvector_bench.geometry import normalize

# --------------------------------------------------------------------------- #
# Revived form: occupancy-parameterised, shared-basis, scalable                #
# --------------------------------------------------------------------------- #
# The single-scale family below was excluded by R21C because `s_lo` RISES with n
# where real's falls. R28 shows that was a parameterisation artifact: R21C held
# the thread COUNT fixed, so points-per-thread grew with n. With the count
# scaling as pool size, `s_lo` falls in 120 of 120 arms measured.
#
# Two changes make the revived form scalable and deployable:
#
# 1. **Occupancy, not count.** `points_per_thread` is the knob; the thread count
#    follows from n. Below ~4 points/thread `s_lo` falls, above ~12 it rises.
# 2. **A shared basis pool.** Each thread selects `fil_dim` directions from one
#    pool of `n_basis` vectors by hash, instead of drawing an independent basis.
#    A per-thread basis needs ~174,000 bases at a 600k pool — a Python loop and
#    ~4e9 floats. Indexing a shared pool is a gather, vectorises, and is also
#    what makes thread membership and directions pure functions of the row
#    index, hence random-access. Semantic directions being shared across topics
#    is arguably the more faithful model anyway.
#
# Centres are stored as `arrange_dim` coefficients rather than ambient vectors
# (150k x 40 floats instead of 150k x 1024) and expanded per chunk, which is
# what keeps memory bounded at registered scale.

FILAMENT_POOL_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("points_per_thread", 1.0, 40.0, 4.0),  # occupancy — the R21C fix
    ("fil_dim", 2.0, 128.0, 48.0),  # local thread dimension
    ("arrange_dim", 4.0, 256.0, 40.0),  # arrangement dimension -> s_hi
    ("fil_scale", 0.02, 1.0, 0.20),  # thread extent -> crossover radius
    ("log2_basis", 8.0, 14.0, 12.0),  # shared direction pool size
    ("dup_frac", 0.0, 0.2, 0.01),  # small near-duplicate population
    ("dup_cos", 0.80, 0.999, 0.95),  # their parent-child cosine
)


def filament_pool_corpus(p: dict[str, float], n: int, dim: int, seed: int,
                         chunk: int = 50_000) -> np.ndarray:
    """Occupancy-parameterised filaments over a shared basis pool.

    Memory-bounded: centres live as `arrange_dim` coefficients and are expanded
    per chunk, and thread directions are gathered from a shared pool rather than
    materialised per thread.
    """
    rng = np.random.default_rng(seed)
    ppt = max(float(p["points_per_thread"]), 1e-6)
    n_thread = max(2, int(round(n / ppt)))
    fil_dim = max(1, int(round(p["fil_dim"])))
    arr_dim = min(max(2, int(round(p["arrange_dim"]))), dim)
    n_basis = max(fil_dim * 2, int(round(2 ** p["log2_basis"])))
    fs = np.float32(p["fil_scale"])

    basis_a = np.linalg.qr(rng.standard_normal((dim, arr_dim)))[0].astype(np.float32)
    cc = rng.standard_normal((n_thread, arr_dim)).astype(np.float32)
    cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
    basis_pool = (rng.standard_normal((n_basis, dim)).astype(np.float32)
                  / np.sqrt(dim, dtype=np.float32))
    thread_idx = rng.integers(0, n_basis, (n_thread, fil_dim))

    owner = rng.integers(0, n_thread, n)
    x = np.empty((n, dim), dtype=np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        own = owner[s:e]
        acc = cc[own] @ basis_a.T
        u = rng.standard_normal((e - s, fil_dim)).astype(np.float32)
        sel = thread_idx[own]
        for j in range(fil_dim):
            acc += (fs * u[:, j])[:, None] * basis_pool[sel[:, j]]
        x[s:e] = acc

    dup_frac = float(p.get("dup_frac", 0.0))
    if dup_frac > 0:
        k = int(round(n * dup_frac))
        if k > 0:
            tgt = rng.choice(n, k, replace=False)
            src = rng.integers(0, n, k)
            c = float(np.clip(p.get("dup_cos", 0.95), 0.05, 0.999))
            rel = np.float32(np.sqrt(1.0 / c**2 - 1.0))
            par = x[src]
            pn = np.linalg.norm(par, axis=1, keepdims=True)
            nz = rng.standard_normal((k, dim)).astype(np.float32)
            nz /= np.maximum(np.linalg.norm(nz, axis=1, keepdims=True), 1e-12)
            x[tgt] = par + rel * pn * nz
    return normalize(x)


FILAMENT_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("log2_filaments", 4.0, 18.0, 14.0),  # F = 2**this threads
    ("fil_dim", 1.0, 64.0, 8.0),  # thread dimension -> s at SMALL radius
    ("arrange_dim", 4.0, 256.0, 40.0),  # arrangement dim -> s at LARGE radius
    ("fil_scale", 0.005, 1.0, 0.15),  # thread extent vs centre spacing -> crossover
    ("scale_spread", 0.0, 2.0, 0.5),  # lognormal spread of extents -> ramp not step
    ("size_tail", 0.0, 2.5, 1.0),  # Zipf on thread occupancy -> hubness
    ("noise", 0.0, 0.2, 0.01),  # isotropic floor
)


def filament_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """A corpus of low-dimensional threads scattered in a high-dimensional layout.

    Returns unit-normed rows, matching ``synth_corpus``'s contract.
    """
    rng = np.random.default_rng(seed)
    n_fil = min(max(2, int(round(2 ** p["log2_filaments"]))), max(2, n // 2))
    fil_dim = min(max(1, int(round(p["fil_dim"]))), dim)
    arr_dim = min(max(2, int(round(p["arrange_dim"]))), dim)

    # Thread centres: unit vectors confined to an arr_dim-dimensional subspace,
    # so the number of centres within radius r grows as r**arr_dim and the
    # large-radius growth slope reads arr_dim rather than the ambient dimension.
    basis_a = np.linalg.qr(rng.standard_normal((dim, arr_dim)).astype(np.float32))[0]
    centres = rng.standard_normal((n_fil, arr_dim)).astype(np.float32) @ basis_a.T
    centres = normalize(centres)

    # Heavy-tailed occupancy: a few dense threads are the hub candidates.
    w = np.arange(1, n_fil + 1, dtype=np.float64) ** (-p["size_tail"])
    counts = rng.multinomial(n, w / w.sum())

    # Lognormal extents: without a spread the crossover is a step, and real's
    # ramp spans a factor of ~1.27 in radius.
    scales = np.float32(p["fil_scale"]) * np.exp(
        np.float32(p["scale_spread"]) * rng.standard_normal(n_fil).astype(np.float32)
    )

    x = np.empty((n, dim), dtype=np.float32)
    row = 0
    inv_sq = np.float32(1.0 / np.sqrt(dim))
    for f in range(n_fil):
        ck = int(counts[f])
        if ck == 0:
            continue
        # Thread directions span the FULL ambient space (not the arrangement
        # subspace), which keeps effective rank high and stops the corpus
        # collapsing onto an arr_dim-dimensional flat.
        b = rng.standard_normal((fil_dim, dim)).astype(np.float32) * inv_sq
        u = rng.standard_normal((ck, fil_dim)).astype(np.float32)
        x[row : row + ck] = centres[f] + scales[f] * (u @ b)
        row += ck
    if row < n:  # multinomial rounding
        x[row:] = centres[rng.integers(0, n_fil, n - row)]

    noise = float(p["noise"])
    if noise > 0.0:
        x += np.float32(noise) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x)  # de-correlate row order from thread order
    return normalize(x)
