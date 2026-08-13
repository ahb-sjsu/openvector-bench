"""Segmented articles in a nested arrangement — the `R56`-`R61` construction.

This is the family that fills the k=14 dip (`R56`), reaches `s(4)` and `s(14)`
together (`R58`), and brings the `PROFILE.md` §3b ratio span into band with `g6`
simultaneously within 1% (`R61`). It does **not** pass §3b, which requires both
spans: `R61` established the two in-band windows are disjoint in ``w_loc``.

It is recorded here because the measured constants and the mechanism are the
durable part, and because the harness version was not random-access.

## Structure, from the measurements

* **Articles** — contiguous runs of rows, mean ~23 (`R34`: a row has ~23
  index-local neighbours and the count saturates there).
* **Segments** — an article is a *sequence* of segments, each with its own
  centre. `R55` showed why: gating a level removes a row's variation, so with all
  levels off two rows collapse onto the article centre and become identical.
  Breaking the **shared** component is what fills the dip.
* **Within-segment path** — levels changing at doubling rates, so cosine falls
  off with index gap (`R30`).
* **Arrangement** — nested clustering over articles, ``27 * branch**L`` articles
  per cluster. `R58`: branch has an optimum at 64, and above ~512 the outer level
  degenerates because ``27 * branch**2`` exceeds the article count.

## Random access

Every structural decision is a pure function of the row index, so row ``i`` is
computable without generating row ``i-1``:

* article and segment are **hierarchical blocks** — ``i >> k`` for the smallest
  ``k`` whose keyed break-bit fires. This replaces the harness version's
  ``cumsum`` over lognormal article lengths, which was O(n) and defeated random
  access. Geometric block lengths give the heavy tail `R53` measured.
* all coefficients and directions come from :mod:`openvector_bench.hashrng`,
  keyed on ``(article, segment, level, block)``.
* the arrangement uses :func:`~openvector_bench.geometry.reproducible_matmul`,
  because a float32 BLAS product is not bit-reproducible across platforms
  (`R48`).

## What this does not do

It does not pass the registered gates. At the best §3b point `g1` is ~4.4
against 17.23, invariant to `d_glob`, `fil_dim` and the break rate including
zero (`R60`). That is recorded as a property of the family, not a tuning gap.
"""

from __future__ import annotations

import numpy as np

from .geometry import normalize, reproducible_matmul
from .hashrng import hash_gaussian, hash_index, hash_uniform

# (name, lo, hi, default) — defaults are `R61`'s ratio-span-in-band point.
SEGMENT_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("art_break", 0.005, 0.5, 0.045),   # article break rate -> mean run ~23
    ("seg_break", 0.0, 0.5, 0.030),     # segment break rate (R61: ratio span in band)
    ("branch", 2.0, 512.0, 64.0),       # articles per cluster grow as 27*branch**L
    ("arr_levels", 1.0, 5.0, 3.0),      # nested arrangement scales
    ("d_glob", 8.0, 256.0, 30.0),       # arrangement subspace dimension
    ("d_loc", 4.0, 256.0, 64.0),        # segment-centre subspace dimension
    ("w_loc", 0.05, 3.0, 0.60),         # segment centre vs arrangement weight
    ("fil_dim", 2.0, 256.0, 48.0),      # within-segment manifold dimension
    ("fil_scale", 0.05, 3.0, 1.0),      # within-segment extent
    ("nlev", 1.0, 10.0, 6.0),           # within-segment path levels
    ("log2_pool", 8.0, 18.0, 13.0),     # shared direction pool
)

_MAXLEV = 8


def _hier_block(keys: np.ndarray, pos: np.ndarray, rate: float,
                salt: int) -> np.ndarray:
    """Hierarchical block id: ``pos >> k`` for the first level whose bit fires.

    Pure function of ``pos``, so it needs no scan over predecessors. Block
    lengths are geometric in ``rate``, which gives the heavy tail `R53` measured
    (most runs short, a few far longer).
    """
    chosen = np.full(pos.shape, _MAXLEV, dtype=np.int64)
    found = np.zeros(pos.shape, dtype=bool)
    for j in range(_MAXLEV):
        blk = pos >> np.int64(j)
        bit = hash_uniform(keys, np.full_like(pos, j), blk,
                           count=1, salt=salt)[..., 0] < rate
        take = bit & (~found)
        chosen = np.where(take, j, chosen)
        found |= bit
    return (chosen.astype(np.int64) << np.int64(32)) | (pos >> chosen)


def segment_corpus(p: dict[str, float], n: int, dim: int, seed: int,
                   chunk: int = 50_000,
                   rows: np.ndarray | None = None) -> np.ndarray:
    """Emit rows of ``dim``. Bit-exact, chunk-invariant, random-access.

    ``rows`` emits an arbitrary set of row indices instead of ``0..n-1``. This
    is the property the harness version lacked: with article boundaries coming
    from a ``cumsum``, row ``i`` could not be produced without its predecessors.
    Here every structural decision is a function of the index, so
    ``segment_corpus(p, 0, dim, seed, rows=[10**12])`` returns exactly the row
    that a full generation would place at 10**12.
    """
    art_break = float(p["art_break"])
    seg_break = float(p["seg_break"])
    branch = max(2, int(round(p["branch"])))
    arr_levels = max(1, int(round(p["arr_levels"])))
    d_glob = min(max(2, int(round(p["d_glob"]))), dim)
    d_loc = max(1, int(round(p["d_loc"])))
    w_loc = float(p["w_loc"])
    fil_dim = max(1, int(round(p["fil_dim"])))
    fil_scale = float(p["fil_scale"])
    nlev = max(1, int(round(p["nlev"])))
    n_pool = int(2 ** round(p["log2_pool"]))

    rng = np.random.default_rng(seed)
    pool = (rng.standard_normal((n_pool, dim)).astype(np.float32)
            / np.sqrt(dim, dtype=np.float32))
    bg = np.linalg.qr(rng.standard_normal((dim, d_glob)))[0].astype(np.float32)

    lw = np.array([0.72 ** L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    plw = np.sqrt(np.array([0.45 * (0.72 ** i) for i in range(nlev)],
                           dtype=np.float32))
    plw /= np.linalg.norm(plw)
    inv = np.float32(fil_scale / np.sqrt(fil_dim))

    want = (np.arange(n, dtype=np.int64) if rows is None
            else np.asarray(rows, dtype=np.int64))
    out = np.empty((len(want), dim), dtype=np.float32)
    for start in range(0, len(want), chunk):
        end = min(start + chunk, len(want))
        idx = want[start:end]
        zero = np.zeros_like(idx)

        # article: hierarchical run over the row index
        art = _hier_block(zero, idx, art_break, salt=11)
        # segment: hierarchical run over the position within the article
        art_start = art & np.int64(0xFFFFFFFF)
        pos = idx - (art_start << (art >> np.int64(32)))
        seg = _hier_block(art, np.maximum(pos, 0), seg_break, salt=23)
        sid = art * np.int64(1_000_003) + seg

        # Shared components are computed once per distinct key and gathered
        # back, not once per row. ~23 rows share an article and a few share a
        # segment, so this is a large constant factor. Random access means a row
        # is computable *from* its index, not that shared work must be repeated:
        # the output is bit-identical either way (asserted in the tests).
        u_art, art_inv = np.unique(art, return_inverse=True)
        u_sid, sid_inv = np.unique(sid, return_inverse=True)

        # arrangement: nested clustering over articles
        acc = np.zeros((end - start, dim), dtype=np.float32)
        for L in range(arr_levels):
            per = 27 * (branch ** L)
            # cluster id at this level: articles sharing `art // per` share a
            # centre. Assignment is by the article index rather than a hash, so
            # it is a pure function of the row (`R35`: above-article structure
            # is not index-local, but the *arrangement* still keys off article).
            coef = hash_gaussian(u_art // max(1, per), np.full_like(u_art, L),
                                 count=d_glob, salt=43)
            coef /= np.maximum(np.linalg.norm(coef, axis=1, keepdims=True), 1e-12)
            acc += float(lw[L]) * reproducible_matmul(coef, bg.T)[art_inv]

        # segment centre: the shared component a break resets
        sdir = hash_index(u_sid, count=d_loc, modulus=n_pool, salt=53)
        sco = hash_gaussian(u_sid, count=d_loc, salt=57)
        sco /= np.maximum(np.linalg.norm(sco, axis=1, keepdims=True), 1e-12)
        cen = np.zeros((len(u_sid), dim), dtype=np.float32)
        for j in range(d_loc):
            cen += (np.float32(w_loc) * sco[:, j])[:, None] * pool[sdir[:, j]]
        acc += cen[sid_inv]
        del cen

        # within-segment path, keyed on the segment so a break resets it too
        for L in range(nlev):
            key = sid * np.int64(31) + L
            blk = np.maximum(pos, 0) >> np.int64(L)
            c = hash_gaussian(key, blk, count=fil_dim, salt=61)
            dd = hash_index(key, blk, count=fil_dim, modulus=n_pool, salt=67)
            amp = inv * plw[L]
            for j in range(fil_dim):
                acc += (amp * c[:, j])[:, None] * pool[dd[:, j]]
            del c, dd
        out[start:end] = acc
    return normalize(out)
