"""Segmented articles in a nested arrangement — the RC-2 frozen family.

This is the `R56`-`R61` construction plus the three mechanisms the RC1_PLAN
campaign added to it, in the order they were found:

* **path decay + ball mixture** (Phase A, `R62`): the within-segment path's
  level-variance decay is a parameter (frozen 0.50, against the historical
  0.72), and a fraction ``1 - path_mix`` of the fine-scale energy is an
  unstructured per-row ball. This is the `g1` lever — without it the family's
  intrinsic dimension saturates near 4 against real's 17.23; with it, ~16.2.
* **rho direction-sharing** (Phase C, `R64`): a keyed fraction ``rho`` of
  every direction-index draw is replaced by the draw of the row's outermost
  arrangement cluster, so distinct neighbourhoods reuse direction sets. This
  is the `g6` (hubness) lever, and at 0.3 it is free elsewhere.
* **per-level arrangement frames** (cycle b, `R66`): each nested-cluster
  level projects through its OWN orthonormal frame instead of one shared
  ``d_glob``-dim basis. The shared frame was a hard ceiling on coarse-scale
  dimension — the coherent direction of every `R65` density-response failure.
  With the ceiling removed, the §3 four-rung trend enters its registered band
  and is seed-robust (4/4 seeds, `R66`) — the first density-response
  criterion this family holds.

## Structure, from the measurements

* **Articles** — contiguous runs of rows, lognormal lengths with mean ~23
  (`R34`; `R53` measured the heavy tail). Lengths come from a frozen
  256-quantile table of lognormal(ln 23 - 0.72, 1.2) — the audited law —
  because computing ``exp`` at generation time would put libm in the byte
  path (`R48`). Articles are drawn inside 4096-row superblocks (an article
  never crosses one; ~0.6% edge effect, stated not hidden).
* **Segments** — an article is a *sequence* of segments, each with its own
  centre. `R55` showed why: gating a level removes a row's variation, so with
  all levels off two rows collapse onto the article centre and become
  identical. Breaking the **shared** component is what fills the dip.
* **Within-segment path** — levels changing at doubling rates, so cosine
  falls off with index gap (`R30`), mixed with the per-row ball.
* **Arrangement** — nested clustering over articles, ``27 * branch**L``
  articles per cluster (`R58`: branch optimum at 64), one frame per level.
  Assignment is **keyed-random** within an ``arr_window``-row window (frozen
  600k, the registered pool size): the first port of this family assigned
  clusters by article *index*, which put whole contiguous runs in one
  cluster and broke `g6`/`g8`/`s(k)` outright (`R67` first evaluation). The
  arrangement repeats independently per window, so coarse structure has
  correlation length ``arr_window`` — a declared property, not an accident.

## Random access

Every structural decision is a pure function of the row index, so row ``i``
is computable without generating row ``i-1``:

* a row's superblock is ``i >> 12``; the superblock's article boundaries are
  a cumulative sum of at most 4096 table lookups keyed on the superblock —
  O(1) work shared by every row in it, no scan over predecessors.
* all coefficients and directions come from :mod:`openvector_bench.hashrng`,
  keyed on ``(article, segment, level, block)``; the segment id folds the
  article through :func:`~openvector_bench.hashrng.mix_keys` so ids cannot
  collide across articles.
* the arrangement uses
  :func:`~openvector_bench.geometry.reproducible_matmul`, because a float32
  BLAS product is not bit-reproducible across platforms (`R48`).

## What this does not do

It does not pass the full registered slate, and the remaining misses are
family-level, not tuning gaps (`R66`): the §3b five-pool spans have a
generation-seed spread 4x their admission window, the §3b absolute G1 levels
run ~15-20% low, and the G1-vs-n exponent sits ~0.01 outside its band. RC-2
evaluates this frozen configuration once, held-out, and records the verdict
either way.
"""

from __future__ import annotations

import numpy as np

from .geometry import normalize, reproducible_matmul
from .costab import cos2pi
from .hashrng import hash_gaussian, hash_index, hash_uniform, mix_keys

# (name, lo, hi, default) — defaults are the RC-7 FROZEN configuration: F8
# (`R87`/`R88`) = the RC-3 frozen D12 plus the near-dup ladder (p_dup 0.05)
# and the continuum sheet (w_cont 0.25), seed-robust 8-of-10 on the package.
# Prior identities recover exactly: RC-3 at p_dup 0, w_cont 0 (e8423665...,
# spec/RC3_FREEZE.md); RC-2 additionally at seg_break 0.116, pool_alpha 0
# (80d94f61..., spec/RC2_FREEZE.md). Do not retune; the freeze is the point.
SEGMENT_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("arr_window", 1e4, 1e7, 600000.0),  # arrangement correlation length (rows)
    ("seg_break", 0.0, 0.5, 0.126),  # segment break rate (R71-R74: the D12 pocket)
    ("branch", 2.0, 512.0, 64.0),  # articles per cluster grow as 27*branch**L
    ("arr_levels", 1.0, 5.0, 3.0),  # nested arrangement scales
    ("d_glob", 8.0, 256.0, 24.0),  # arrangement subspace dim (per level)
    ("d_loc", 4.0, 256.0, 64.0),  # segment-centre subspace dimension
    ("w_loc", 0.05, 3.0, 0.60),  # segment centre vs arrangement weight
    ("fil_dim", 2.0, 256.0, 48.0),  # within-segment manifold dimension
    ("fil_scale", 0.05, 3.0, 1.0),  # within-segment extent
    ("nlev", 1.0, 10.0, 6.0),  # within-segment path levels
    ("log2_pool", 8.0, 18.0, 10.0),  # shared direction pool (R64: the g4 lever)
    ("path_decay", 0.05, 1.0, 0.50),  # path level-variance decay (R62: the g1 lever)
    ("path_mix", 0.0, 1.0, 0.60),  # path fraction; 1-path_mix is the ball
    ("rho", 0.0, 1.0, 0.30),  # cluster-shared direction fraction (R64: g6)
    ("level_frames", 0.0, 1.0, 1.0),  # 1: one frame per arrangement level (R66)
    (
        "pool_alpha",
        0.0,
        1.0,
        0.22,
    ),  # pool amplitude power law (R70-R74: g8/rspan lever)
    ("p_dup", 0.0, 0.5, 0.05),  # near-duplicate gate rate (R82: the g1exp mechanism)
    ("alpha_dup", 0.5, 1.0, 0.95),  # duplicate blend toward the source row
    # dup source locality (0 = arr_window). R85: a small window resolves dups
    # in every prefix pool equally, steepening g1exp WITHOUT compressing the
    # section-3b spans.
    ("dup_window", 0.0, 1e7, 0.0),
    # RC7 hybrid: thin continuum sheet over the cluster backbone (R87). A
    # band-limited random field over per-article latents supplies the coarse
    # effective rank (g3) and latent-neighbour structure the clusters lack.
    ("w_cont", 0.0, 1.0, 0.25),  # sheet weight in the coarse budget (0: off)
    ("cont_lat", 1.0, 16.0, 2.0),  # latent dimension of the field
    ("cont_bw", 0.05, 8.0, 0.5),  # base bandwidth (octave 0)
    ("cont_oct", 1.0, 6.0, 3.0),  # octaves (mirror the per-level frames)
    ("cont_freq", 4.0, 128.0, 24.0),  # frequencies per octave
    # RC11/RC12 echo groups: scattered near-parallel micro-clusters. A gated
    # row blends toward its group's midpoint prototype (two keyed base rows).
    # Small k and window-locality are the mechanism (RC11_VERDICT): every
    # pair resolves at sample fraction ~s, prefix pools stay proportionate,
    # in-degree is bounded by k-1.
    ("p_echo", 0.0, 0.5, 0.0),  # echo gate rate (0: off)
    ("echo_k", 2.0, 64.0, 3.0),  # target members per group
    ("echo_win", 0.0, 1e7, 100000.0),  # group locality window (rows)
    ("echo_alpha", 0.5, 1.0, 0.96),  # blend toward the prototype
)

_MAXLEV = 8
_SB_BITS = 12  # superblock = 4096 rows
_SB = 1 << _SB_BITS
_ART_MEAN = 23.0  # mean of the frozen length law, for cluster counts

# Frozen 256-quantile table of round(lognormal(ln 23 - 0.5*1.2**2, 1.2)) at
# midpoints (m + 0.5)/256, clipped >= 1 — the article-length law the harness
# audits used (`R53` tail), with no transcendental in the generation path.
# Mean 22.73, max 357. Regenerate only by editing this comment's formula.
_ART_LEN = np.array(
    (
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        7,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        9,
        9,
        9,
        9,
        9,
        9,
        9,
        9,
        9,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        11,
        11,
        11,
        11,
        11,
        11,
        11,
        12,
        12,
        12,
        12,
        12,
        12,
        12,
        13,
        13,
        13,
        13,
        13,
        13,
        13,
        14,
        14,
        14,
        14,
        14,
        14,
        15,
        15,
        15,
        15,
        15,
        16,
        16,
        16,
        16,
        16,
        17,
        17,
        17,
        17,
        17,
        18,
        18,
        18,
        18,
        18,
        19,
        19,
        19,
        19,
        20,
        20,
        20,
        21,
        21,
        21,
        21,
        22,
        22,
        22,
        23,
        23,
        23,
        24,
        24,
        24,
        25,
        25,
        25,
        26,
        26,
        27,
        27,
        27,
        28,
        28,
        29,
        29,
        30,
        30,
        31,
        31,
        32,
        32,
        33,
        33,
        34,
        35,
        35,
        36,
        37,
        37,
        38,
        39,
        40,
        40,
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        50,
        51,
        52,
        54,
        55,
        57,
        59,
        60,
        62,
        64,
        67,
        69,
        72,
        75,
        78,
        82,
        86,
        90,
        95,
        101,
        108,
        117,
        127,
        140,
        158,
        185,
        230,
        357,
    ),
    dtype=np.int64,
)


def _hier_block(
    keys: np.ndarray, pos: np.ndarray, rate: float, salt: int
) -> np.ndarray:
    """Hierarchical block id: ``pos >> k`` for the first level whose bit fires.

    Pure function of ``pos``, so it needs no scan over predecessors. Block
    lengths are geometric in ``rate``. Used for segments, whose positions live
    inside an article (<= 357), where the geometric law matches the audited
    harness construction.
    """
    chosen = np.full(pos.shape, _MAXLEV, dtype=np.int64)
    found = np.zeros(pos.shape, dtype=bool)
    for j in range(_MAXLEV):
        blk = pos >> np.int64(j)
        bit = (
            hash_uniform(keys, np.full_like(pos, j), blk, count=1, salt=salt)[..., 0]
            < rate
        )
        take = bit & (~found)
        chosen = np.where(take, j, chosen)
        found |= bit
    return (chosen.astype(np.int64) << np.int64(32)) | (pos >> chosen)


def _articles(idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Article id, within-article position and article start row for each row.

    Lengths are frozen-table lognormal draws keyed on (superblock, slot);
    boundaries are their cumulative sum inside the 4096-row superblock. Every
    row of a superblock shares one boundary computation — random access
    without a predecessor scan.
    """
    sb = idx >> np.int64(_SB_BITS)
    r = idx & np.int64(_SB - 1)
    u_sb, sb_inv = np.unique(sb, return_inverse=True)
    lens = _ART_LEN[hash_index(u_sb, count=_SB, modulus=256, salt=7)]
    ends = np.cumsum(lens, axis=1)  # (n_sb, 4096), ends[-1] >= 4096
    art = np.empty(idx.shape, dtype=np.int64)
    pos = np.empty(idx.shape, dtype=np.int64)
    start = np.empty(idx.shape, dtype=np.int64)
    for s in range(len(u_sb)):
        g = sb_inv == s
        m = np.searchsorted(ends[s], r[g], side="right")
        art[g] = (u_sb[s] << np.int64(_SB_BITS + 1)) | m
        st = np.where(m > 0, ends[s][m - 1], 0)
        pos[g] = r[g] - st
        start[g] = (u_sb[s] << np.int64(_SB_BITS)) + st
    return art, pos, start


def segment_corpus(
    p: dict[str, float],
    n: int,
    dim: int,
    seed: int,
    chunk: int = 50_000,
    rows: np.ndarray | None = None,
) -> np.ndarray:
    """Emit rows of ``dim``. Bit-exact, chunk-invariant, random-access.

    ``rows`` emits an arbitrary set of row indices instead of ``0..n-1``. This
    is the property the harness version lacked: with article boundaries coming
    from a ``cumsum``, row ``i`` could not be produced without its predecessors.
    Here every structural decision is a function of the index, so
    ``segment_corpus(p, 0, dim, seed, rows=[10**12])`` returns exactly the row
    that a full generation would place at 10**12.
    """
    arr_window = max(_SB, int(round(p["arr_window"])))
    seg_break = float(p["seg_break"])
    branch = max(2, int(round(p["branch"])))
    arr_levels = max(1, int(round(p["arr_levels"])))
    d_glob = min(max(2, int(round(p["d_glob"]))), dim)
    d_loc = max(1, int(round(p["d_loc"])))
    w_loc = float(p["w_loc"])
    fil_dim = max(1, int(round(p["fil_dim"])))
    fil_scale = float(p["fil_scale"])
    nlev = max(1, int(round(p["nlev"])))
    n_pool = int(round(2 ** float(p["log2_pool"])))
    path_decay = float(p.get("path_decay", 0.72))
    pool_alpha = float(p.get("pool_alpha", 0.0))
    p_dup = min(0.5, max(0.0, float(p.get("p_dup", 0.0))))
    alpha_dup = float(p.get("alpha_dup", 0.95))
    dup_window = int(round(float(p.get("dup_window", 0.0)))) or arr_window
    w_cont = min(1.0, max(0.0, float(p.get("w_cont", 0.0))))
    cont_lat = max(1, int(round(p.get("cont_lat", 2.0))))
    cont_bw = float(p.get("cont_bw", 0.5))
    cont_oct = max(1, int(round(p.get("cont_oct", 3.0))))
    cont_freq = max(4, int(round(p.get("cont_freq", 24.0))))
    p_echo = min(0.5, max(0.0, float(p.get("p_echo", 0.0))))
    echo_k = max(2, int(round(p.get("echo_k", 3.0))))
    echo_win = max(1000, int(round(p.get("echo_win", 100000.0))))
    echo_alpha = float(p.get("echo_alpha", 0.96))
    path_mix = min(1.0, max(0.0, float(p.get("path_mix", 1.0))))
    rho = min(1.0, max(0.0, float(p.get("rho", 0.0))))
    level_frames = bool(round(p.get("level_frames", 0.0)))

    # clusters per level within one window, matching the audited pool-relative
    # construction: n_articles / (27 * branch**L), never below 2
    ncl = [
        max(2, int(round((arr_window / _ART_MEAN) / (27 * branch**L))))
        for L in range(arr_levels)
    ]

    rng = np.random.default_rng(seed)
    pool = rng.standard_normal((n_pool, dim)).astype(np.float32) / np.sqrt(
        dim, dtype=np.float32
    )
    if pool_alpha > 0.0:
        # power-law amplitude profile over pool slots (R70): shapes the PCA
        # tail (g4, g8) without touching any mechanism. Unit mean square, so
        # overall variance is preserved; a no-op at alpha = 0 by branch.
        w = (1.0 + np.arange(n_pool, dtype=np.float64)) ** (-pool_alpha)
        w /= np.sqrt((w**2).mean())
        pool *= w.astype(np.float32)[:, None]
    # One orthonormal frame per arrangement level (R66), or one shared frame.
    # Drawn up front, in level order, so the emission is chunk-invariant.
    if level_frames:
        frames = [
            np.linalg.qr(rng.standard_normal((dim, d_glob)))[0].astype(np.float32)
            for _ in range(arr_levels)
        ]
    else:
        frames = [
            np.linalg.qr(rng.standard_normal((dim, d_glob)))[0].astype(np.float32)
        ] * arr_levels

    cont_assets = None
    if w_cont > 0.0:
        # sheet assets, drawn after the frames in a fixed order (chunk-safe):
        # per octave, frequencies (bandwidth doubling), phases, and a frame
        cont_assets = []
        for o in range(cont_oct):
            Wo = (
                rng.standard_normal((cont_freq, cont_lat)) * cont_bw * (2.0**o)
            ).astype(np.float32)
            phio = rng.uniform(0.0, 1.0, cont_freq).astype(np.float32)
            Fo = np.linalg.qr(rng.standard_normal((dim, cont_freq)))[0].astype(
                np.float32
            )
            cont_assets.append((Wo, phio, Fo))
        cont_low = np.array([0.72**o for o in range(cont_oct)], dtype=np.float32)
        cont_low /= np.linalg.norm(cont_low)
        wc_bak = np.float32(np.sqrt(max(0.0, 1.0 - w_cont**2)))

    lw = np.array([0.72**L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    plw = np.sqrt(np.array([path_decay**i for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    inv = np.float32(fil_scale / np.sqrt(fil_dim))
    wp = np.float32(np.sqrt(path_mix))
    wb = np.float32(np.sqrt(max(0.0, 1.0 - path_mix)))

    def _share(priv, cl, art, extra, count, salt_dir, salt_gate):
        """Replace a keyed fraction ``rho`` of direction slots with the row's
        outermost-cluster draw (R64). Both the shared draw and the gate are
        pure functions of their keys, so random access is preserved."""
        if rho <= 0.0:
            return priv
        sh = hash_index(cl, extra, count=count, modulus=n_pool, salt=salt_dir)
        gt = hash_uniform(art, extra, count=count, salt=salt_gate) < rho
        return np.where(gt, sh, priv)

    want = (
        np.arange(n, dtype=np.int64)
        if rows is None
        else np.asarray(rows, dtype=np.int64)
    )
    out = np.empty((len(want), dim), dtype=np.float32)
    for cs in range(0, len(want), chunk):
        ce = min(cs + chunk, len(want))
        idx = want[cs:ce]

        art, pos, art_start = _articles(idx)
        win = art_start // np.int64(arr_window)
        seg = _hier_block(art, pos, seg_break, salt=23)
        # fold the article in so segment ids cannot collide across articles
        sid = mix_keys(art, seg).view(np.int64)

        # Shared components are computed once per distinct key and gathered
        # back, not once per row. ~23 rows share an article and a few share a
        # segment, so this is a large constant factor. Random access means a row
        # is computable *from* its index, not that shared work must be repeated:
        # the output is bit-identical either way (asserted in the tests).
        u_art, art_first, art_inv = np.unique(
            art, return_index=True, return_inverse=True
        )
        u_win = win[art_first]
        u_sid, sid_first, sid_inv = np.unique(
            sid, return_index=True, return_inverse=True
        )

        # arrangement: keyed-random nested clustering over articles within the
        # window, one frame per level (R66; R67 first evaluation showed why
        # index-contiguous assignment is not this family)
        acc = np.zeros((ce - cs, dim), dtype=np.float32)
        cl0 = None
        for L in range(arr_levels):
            cid = hash_index(
                u_art, np.full_like(u_art, L), count=1, modulus=ncl[L], salt=41
            )[..., 0]
            if L == 0:
                cl0 = u_win * np.int64(1_000_003) + cid
            coef = hash_gaussian(
                u_win, np.full_like(u_art, L), cid, count=d_glob, salt=43
            )
            coef /= np.maximum(np.linalg.norm(coef, axis=1, keepdims=True), 1e-12)
            _cw = float(lw[L]) * (float(wc_bak) if cont_assets is not None else 1.0)
            acc += _cw * reproducible_matmul(coef, frames[L].T)[art_inv]
        if cont_assets is not None:
            # the continuum sheet: per-article latents, band-limited field.
            # Phase sums and projections are fixed-order (bit-exact).
            ul = hash_uniform(u_art, count=cont_lat, salt=149)
            cont = np.zeros((len(u_art), dim), dtype=np.float32)
            for o, (Wo, phio, Fo) in enumerate(cont_assets):
                phase = np.repeat(phio[None, :], len(u_art), axis=0)
                for dd_ in range(cont_lat):
                    phase = phase + ul[:, dd_ : dd_ + 1] * Wo[None, :, dd_]
                feat = cos2pi(phase) * np.float32(np.sqrt(2.0 / cont_freq))
                cont += float(cont_low[o]) * reproducible_matmul(feat, Fo.T)
            acc += np.float32(w_cont) * cont[art_inv]
            del cont
        row_cl0 = cl0[art_inv]
        u_cl = row_cl0[sid_first]  # outermost cluster of each unique segment
        u_sart = art[sid_first]  # article of each unique segment

        # segment centre: the shared component a break resets
        sdir = _share(
            hash_index(u_sid, count=d_loc, modulus=n_pool, salt=53),
            u_cl,
            u_sart,
            np.zeros_like(u_cl),
            d_loc,
            97,
            101,
        )
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
            blk = pos >> np.int64(L)
            c = hash_gaussian(key, blk, count=fil_dim, salt=61)
            dd = _share(
                hash_index(key, blk, count=fil_dim, modulus=n_pool, salt=67),
                row_cl0,
                art,
                np.full_like(row_cl0, L),
                fil_dim,
                107,
                109,
            )
            amp = inv * wp * plw[L]
            for j in range(fil_dim):
                acc += (amp * c[:, j])[:, None] * pool[dd[:, j]]
            del c, dd

        # per-row ball: the unstructured share of the fine scale (R62). The
        # directions are the segment's (shareable under rho); the coefficients
        # are the row's own.
        if wb > 0.0:
            bdir = _share(
                hash_index(u_sid, count=fil_dim, modulus=n_pool, salt=71),
                u_cl,
                u_sart,
                np.zeros_like(u_cl),
                fil_dim,
                113,
                127,
            )
            bdir = bdir[sid_inv]
            bco = hash_gaussian(sid, pos + np.int64(1), count=fil_dim, salt=79)
            bamp = inv * wb
            for j in range(fil_dim):
                acc += (bamp * bco[:, j])[:, None] * pool[bdir[:, j]]
            del bdir, bco
        out[cs:ce] = acc
    out = normalize(out)
    if p_dup > 0.0:
        # Near-duplicate ladder (R82, the g1exp mechanism): a keyed fraction
        # of rows becomes a near-copy of a keyed source row in the same
        # arr_window window — the low-dimensional structure that only dense
        # samples resolve. Depth-1: sources are always base rows, so random
        # access needs at most one extra emission and no recursion.
        gate = hash_uniform(want, count=1, salt=131)[..., 0] < p_dup
        if gate.any():
            win0 = (want // np.int64(dup_window)) * np.int64(dup_window)
            src = win0 + hash_index(want, count=1, modulus=dup_window, salt=137)[..., 0]
            gi = np.nonzero(gate)[0]
            u_src, s_inv = np.unique(src[gi], return_inverse=True)
            base_p = dict(p)
            base_p["p_dup"] = 0.0
            src_rows = segment_corpus(base_p, 0, dim, seed, chunk=chunk, rows=u_src)
            a = np.float32(alpha_dup)
            b = np.float32(np.sqrt(max(0.0, 1.0 - float(alpha_dup) ** 2)))
            # normalize ONLY the blended rows: renormalizing already-unit
            # plain rows would shift last bits and break batch invariance
            out[gi] = normalize(a * src_rows[s_inv] + b * out[gi])
    if p_echo > 0.0:
        egate = hash_uniform(want, count=1, salt=151)[..., 0] < p_echo
        if egate.any():
            ei = np.nonzero(egate)[0]
            w_no = want[ei] // np.int64(echo_win)
            m_w = max(2, int(round(p_echo * echo_win / echo_k)))
            gid = hash_index(want[ei], count=1, modulus=m_w, salt=157)[..., 0]
            gkey = w_no * np.int64(1_000_003) + gid
            u_g, g_inv = np.unique(gkey, return_inverse=True)
            gw = u_g // np.int64(1_000_003)
            s1 = (
                gw * np.int64(echo_win)
                + hash_index(u_g, count=1, modulus=echo_win, salt=163)[..., 0]
            )
            s2 = (
                gw * np.int64(echo_win)
                + hash_index(u_g, count=1, modulus=echo_win, salt=167)[..., 0]
            )
            base_p = dict(p)
            base_p["p_echo"] = 0.0
            u_src, src_inv = np.unique(np.concatenate([s1, s2]), return_inverse=True)
            sr = segment_corpus(base_p, 0, dim, seed, chunk=chunk, rows=u_src)
            proto = sr[src_inv[: len(s1)]] + sr[src_inv[len(s1) :]]
            proto = normalize(proto)
            a = np.float32(echo_alpha)
            b = np.float32(np.sqrt(max(0.0, 1.0 - float(echo_alpha) ** 2)))
            out[ei] = normalize(a * proto[g_inv] + b * out[ei])
    return out
