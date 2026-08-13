"""Two nested regimes, built from `R31`'s measured constants.

Every prior family was *fitted* to a target. This one is constructed from a
description of what real embeddings are, measured in `R31`:

| regime | G1 | mu | ratio | reached when |
|---|---|---|---|---|
| within-article passages | ~15 | ~1.057 | ~4.0 | >= ~10 same-article rows sampled |
| cross-article structure | ~26 | ~1.029 | ~1.29 | no adjacent rows sampled |

and one structural fact: groups are **contiguous in row index**, because a
corpus is ordered by article and that is what makes subsampling thin the group
inventory (`R30`).

The falsifiable claim is that the `PROFILE.md` §3b density ladder follows from
those regimes *without being fitted*. §3b is therefore deliberately absent from
the construction.

## Construction

For row ``i`` with group ``G = i // group_size``::

    centre(G) = normalize(arr_coeffs(G) @ basis_arr.T)
    offset(i) = fil_scale * sum_j u(i, j) * basis_pool[h(G, j)] / sqrt(fil_dim)
    x(i)      = normalize(centre(G) + offset(i))

``basis_arr`` is a fixed ``dim x arr_dim`` orthonormal frame, so **every centre
lies in one ``arr_dim``-dimensional subspace** and the centre cloud has
intrinsic dimension ``arr_dim``. Each group draws its own ``fil_dim`` directions
from a shared pool, so the within-group manifold has intrinsic dimension
``fil_dim``.

## What `R30` got wrong, and what this does differently

`R30` set ``arrange_dim = 40`` and assumed the arrangement had dimension 40. It
measured 6-13. **The parameters here are calibrated against measured G1, not
assumed**: :func:`calibrate` reports the intrinsic dimension of each regime as
built, and the caller adjusts until they match. A parameter is a request; the
measurement is the fact.

## mu is not a free target

For a locally Poisson process in k dimensions the median of ``r2/r1`` is
approximately ``2**(1/k)``. Real's cross-article regime measures mu 1.0293
against 1.0269 predicted from G1 26.1 -- essentially Poisson. Its within-article
regime measures 1.0576 against 1.0447 predicted from G1 15.9, a ~29% excess.
So mu is determined by G1 in the arrangement and carries independent
information only within groups, where real is *not* locally uniform.
``size_spread`` exists for that excess and is 0 by default, since nothing yet
shows it is the right mechanism.
"""

from __future__ import annotations

import numpy as np

from .geometry import normalize, reproducible_matmul

# (name, lo, hi, default) -- the search-space convention used across the project.
TWOSCALE_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("group_size", 2.0, 400.0, 100.0),   # contiguous rows per group (R31: 10-100)
    ("arr_dim", 4.0, 128.0, 26.0),       # cross-group intrinsic dim (R31: ~26)
    ("fil_dim", 2.0, 64.0, 15.0),        # within-group intrinsic dim (R31: ~15)
    ("fil_scale", 0.01, 1.0, 0.15),      # within extent vs centre spacing
    ("log2_basis", 8.0, 16.0, 13.0),     # shared direction pool size
    ("size_spread", 0.0, 1.5, 0.0),      # lognormal spread on group size
)


def twoscale_corpus(p: dict[str, float], n: int, dim: int, seed: int,
                    chunk: int = 50_000) -> np.ndarray:
    """Emit ``n`` rows of ``dim`` with contiguous groups and two nested scales.

    Memory-bounded: centres are held as ``arr_dim`` coefficients and expanded per
    chunk, and within-group directions are gathered from a shared pool rather
    than materialised per group.
    """
    rng = np.random.default_rng(seed)
    gs = max(float(p["group_size"]), 1.0)
    arr_dim = min(max(2, int(round(p["arr_dim"]))), dim)
    fil_dim = max(1, int(round(p["fil_dim"])))
    fs = np.float32(p["fil_scale"])
    n_basis = max(fil_dim * 2, int(round(2 ** p["log2_basis"])))
    spread = float(p.get("size_spread", 0.0))

    # Group boundaries. Contiguous by construction (R30): a prefix of the corpus
    # must contain proportionally fewer distinct groups.
    if spread <= 0:
        n_group = max(2, int(np.ceil(n / gs)))
        bounds = np.minimum(np.arange(1, n_group + 1, dtype=np.int64)
                            * int(round(gs)), n)
    else:
        est = int(n / gs * 2.0) + 16
        ln = rng.lognormal(np.log(gs) - 0.5 * spread ** 2, spread, est)
        bounds = np.cumsum(np.maximum(1, np.round(ln)).astype(np.int64))
        bounds = np.append(bounds[bounds < n], n)
        n_group = len(bounds)

    # All centres share ONE arr_dim-dimensional frame, so the centre cloud has
    # intrinsic dimension arr_dim rather than merely being parameterised by it.
    basis_arr = np.linalg.qr(
        rng.standard_normal((dim, arr_dim)))[0].astype(np.float32)
    coeffs = rng.standard_normal((n_group, arr_dim)).astype(np.float32)
    coeffs /= np.maximum(np.linalg.norm(coeffs, axis=1, keepdims=True), 1e-12)

    basis_pool = (rng.standard_normal((n_basis, dim)).astype(np.float32)
                  / np.sqrt(dim, dtype=np.float32))
    group_dirs = rng.integers(0, n_basis, (n_group, fil_dim))

    inv = np.float32(1.0 / np.sqrt(fil_dim))
    x = np.empty((n, dim), dtype=np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        own = np.minimum(
            np.searchsorted(bounds, np.arange(s, e), side="right"), n_group - 1)
        acc = reproducible_matmul(coeffs[own], basis_arr.T)
        u = rng.standard_normal((e - s, fil_dim)).astype(np.float32)
        sel = group_dirs[own]
        for j in range(fil_dim):
            acc += (fs * inv * u[:, j])[:, None] * basis_pool[sel[:, j]]
        x[s:e] = acc
    return normalize(x)


# `twoscale_corpus` is SUPERSEDED by `cascade_corpus` below. The
# group-of-balls construction fails the cross-article regime: at group_size 100
# over 600k rows a b=1 clumping draw still takes ~6 rows per group, and because
# those rows are i.i.d. in a tight ball they collapse G1 to 7.2 against a target
# of 26.1. Real is not flat within a group -- `R30` measured cosine decaying
# 0.598 -> 0.304 -> 0.236 across index gaps 1 -> 16 -> 128. It is kept because
# the arrangement calibration is reused and the failure is instructive.

# Level weights fitted by NNLS to `R30`'s measured index autocorrelation, as
# variance shares; the fit is reproduced by
# `harness/rc1/fit_cascade_weights.py`. The fit is exact, which is
# NOT evidence: 16 free non-negative parameters against 8 measured gaps (NNLS
# zeroes all but 9) interpolates by construction. What the weights buy is a construction whose autocorrelation is
# real's by design, so that G1, the ratio and the §3b spans -- none of them
# fitted -- become a genuine test.
CASCADE_WEIGHTS: tuple[float, ...] = (
    0.3336, 0.0548, 0.0807, 0.1018, 0.0876, 0.0537, 0.0305, 0.0218,
)
CASCADE_GLOBAL: float = 0.2355

# Per-level intrinsic dimensions, derived (not fitted) from real's measured
# s(r) curve -- `R33`, `harness/rc1/derive_level_dims.py`.
#
# Blum-Hopcroft-Kannan §2.3 and §2.4.1: components in different subspaces are
# near-orthogonal in high dimension, so squared distances add, and volume in a
# d-ball grows as r^d. Two rows differing in levels 0..L therefore sit at radius
# R(L) = sqrt(2 * sum_{l<=L} w_l^2) and their difference occupies the *sum* of
# those levels' subspaces. The local growth dimension at R(L) is thus the
# CUMULATIVE dimension sum_{l<=L} d_l, which inverts to give d_l from a measured
# s(r).
#
# This decouples the two constraints: the weights are fixed by the
# autocorrelation (`R30`) and the dimensions by the s(r) curve (`R32`). `R32`
# tied them together through a two-way fast/slow split and could produce no ramp
# at all.
#
# CAVEAT: R(L) for L=0 and L>=4 falls outside real's measured radius range
# (0.881..1.125 at b=100), so four of these eight are extrapolations.
CASCADE_LEVEL_DIMS: tuple[int, ...] = (9, 1, 5, 17, 5, 1, 1, 1)


def cascade_corpus(p: dict[str, float], n: int, dim: int, seed: int,
                   chunk: int = 50_000) -> np.ndarray:
    """A trajectory in embedding space indexed by row, not a bag of clusters.

    Row ``i`` is a weighted sum of components that change at doubling rates::

        x(i) = sum_s w_s * v(s, i >> s) + w_glob * m

    Two rows share the level-``s`` component iff ``i >> s == j >> s``, so the
    cosine between them falls off with index gap exactly as the weights dictate.
    With :data:`CASCADE_WEIGHTS` that fall-off is real's measured one.

    The dimensional structure is what makes it two-regime. Fast levels
    (``s <= fast_levels``) live in a **low-dimensional** subspace of size
    ``fast_dim``, so rows a few apart differ within a thin manifold; slow levels
    live in a wider ``slow_dim`` subspace, so distant rows differ across the
    full arrangement. Fast components in the ambient 1024 would put the local
    dimension at 1024 rather than real's ~15.

    Random-access by construction: every component is indexed by ``i >> s``, so
    row ``i`` is computable without generating any other row.
    """
    rng = np.random.default_rng(seed)
    w = np.sqrt(np.asarray(CASCADE_WEIGHTS, dtype=np.float32))
    w_glob = np.float32(np.sqrt(CASCADE_GLOBAL) * float(p.get("global_scale", 1.0)))
    n_lev = len(w)

    raw = p.get("level_dims")
    if raw is None:
        # Legacy two-way split, reproducing `R32` byte for byte: fast and slow
        # levels SHARE one basis each. It produces no ramp, because a single
        # pair of parameters cannot satisfy both the autocorrelation and the
        # s(r) curve.
        fast_dim = min(max(2, int(round(p["fast_dim"]))), dim)
        slow_dim = min(max(2, int(round(p["slow_dim"]))), dim)
        fast_levels = max(0, int(round(p["fast_levels"])))
        dims = [fast_dim if s <= fast_levels else slow_dim for s in range(n_lev)]
        basis_f = np.linalg.qr(
            rng.standard_normal((dim, fast_dim)))[0].astype(np.float32)
        basis_s = np.linalg.qr(
            rng.standard_normal((dim, slow_dim)))[0].astype(np.float32)
        bases = [basis_f if s <= fast_levels else basis_s for s in range(n_lev)]
    else:
        dims = [max(1, int(round(v))) for v in raw][:n_lev]
        dims += [1] * (n_lev - len(dims))
        if sum(dims) > dim:
            raise ValueError(f"level dims sum to {sum(dims)} > ambient {dim}")
        # Levels occupy MUTUALLY ORTHOGONAL blocks of one frame. The
        # cumulative-dimension identity (see CASCADE_LEVEL_DIMS) needs the
        # difference vector across levels 0..L to span sum_{l<=L} d_l
        # independent directions; a shared basis collapses that sum, which is
        # why the legacy path above cannot produce a ramp.
        frame = np.linalg.qr(
            rng.standard_normal((dim, sum(dims))))[0].astype(np.float32)
        bases, off = [], 0
        for s in range(n_lev):
            bases.append(frame[:, off:off + dims[s]])
            off += dims[s]

    m = rng.standard_normal(dim).astype(np.float32)
    m /= np.linalg.norm(m)

    # One coefficient table per level, indexed by i >> s.
    tables = []
    for s in range(n_lev):
        c = rng.standard_normal((int(n >> s) + 2, dims[s])).astype(np.float32)
        c /= np.maximum(np.linalg.norm(c, axis=1, keepdims=True), 1e-12)
        tables.append(c)

    x = np.empty((n, dim), dtype=np.float32)
    for st in range(0, n, chunk):
        en = min(st + chunk, n)
        idx = np.arange(st, en)
        acc = np.broadcast_to(w_glob * m, (en - st, dim)).copy()
        for s in range(n_lev):
            acc += w[s] * reproducible_matmul(tables[s][idx >> s], bases[s].T)
        x[st:en] = acc
    return normalize(x)


def centre_cloud(p: dict[str, float], n_group: int, dim: int,
                 seed: int) -> np.ndarray:
    """The arrangement alone — one point per group, no within-group offset.

    Used to measure what ``arr_dim`` actually delivers. `R30` set the parameter
    and never checked; the arrangement measured G1 6-13 against a requested 40.
    """
    rng = np.random.default_rng(seed)
    arr_dim = min(max(2, int(round(p["arr_dim"]))), dim)
    basis_arr = np.linalg.qr(
        rng.standard_normal((dim, arr_dim)))[0].astype(np.float32)
    coeffs = rng.standard_normal((n_group, arr_dim)).astype(np.float32)
    coeffs /= np.maximum(np.linalg.norm(coeffs, axis=1, keepdims=True), 1e-12)
    return normalize(reproducible_matmul(coeffs, basis_arr.T))


CASCADE_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("fast_dim", 2.0, 64.0, 15.0),      # within-article manifold (R31: G1 ~15)
    ("slow_dim", 8.0, 128.0, 26.0),     # cross-article arrangement (R31: G1 ~26)
    ("fast_levels", 0.0, 6.0, 2.0),     # levels 0..this use fast_dim
    ("global_scale", 0.0, 2.0, 1.0),    # the shared mean direction
)
