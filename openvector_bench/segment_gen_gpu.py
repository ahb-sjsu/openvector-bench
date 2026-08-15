"""Torch mirror of :func:`segment_gen.segment_corpus` — byte-identical, GPU-fast.

Phase E of `DISTRIBUTION.md`: fleet-scale regeneration needs more than the
numpy path's ~3 MB/s/core, and NRP kills GPU pods that idle the GPU. This
module emits the SAME BYTES as ``segment_corpus`` at roughly two orders of
magnitude the throughput, by splitting the work along the determinism
boundary:

* **GPU (torch)** — the hash draws, gathers, and rank-1/elementwise
  accumulations. Elementwise float32 operations are IEEE-determined and
  their order is specified by the code (the same loop order as the numpy
  reference), so these are bit-safe on any backend. Integer hashing uses
  int64-as-uint64 with masked logical shifts (the `hashgpu` technique,
  applied to :mod:`hashrng`'s exact constants and key-folding).
* **CPU (numpy)** — every reduction (row norms) and the near-dup / echo
  blend passes, executed by the reference implementation itself. Summation
  order in reductions is backend-dependent, so they are never mirrored.

Correctness is preserved the only honest way: ``verify(device)`` regenerates
the frozen reference identities and asserts the SHA-256s; any caller should
gate on it once per process. The numpy module remains the definition.
"""

from __future__ import annotations

import numpy as np

try:
    import torch
except ImportError:  # pragma: no cover - GPU module is optional
    torch = None

from .costab import _TAB
from .geometry import normalize
from .hashrng import hash_index, hash_uniform
from .segment_gen import _ART_LEN, _ART_MEAN, _MAXLEV, _SB, _SB_BITS

_MASKS = {n: (1 << (64 - n)) - 1 for n in (11, 27, 30, 31)}
_GAMMA = int(np.int64(np.uint64(0x9E3779B97F4A7C15).astype(np.int64)))
_MIX1 = int(np.int64(np.uint64(0xBF58476D1CE4E5B9).astype(np.int64)))
_MIX2 = int(np.int64(np.uint64(0x94D049BB133111EB).astype(np.int64)))
_SGAUSS = int(np.int64(np.uint64(0x1D8E4E27C47D124F).astype(np.int64)))
_SINDEX = int(np.int64(np.uint64(0xA0761D6478BD642F).astype(np.int64)))


def _lsr(x, n):
    return (x >> n) & _MASKS[n]


def _sm64(x):
    z = x + _GAMMA
    z = (z ^ _lsr(z, 30)) * _MIX1
    z = (z ^ _lsr(z, 27)) * _MIX2
    return z ^ _lsr(z, 31)


def _sm64_int(x: int) -> int:
    """Python-int splitmix64 for scalar column constants."""
    m = (1 << 64) - 1
    z = (x + 0x9E3779B97F4A7C15) & m
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & m
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & m
    return z ^ (z >> 31)


def _as_i64(v: int) -> int:
    return int(np.int64(np.uint64(v & ((1 << 64) - 1)).astype(np.int64)))


def _mix_keys_t(*keys):
    acc = None
    for k in keys:
        k64 = k if torch.is_tensor(k) else torch.tensor(k, dtype=torch.int64)
        k64 = k64.to(torch.int64)
        acc = k64 if acc is None else _sm64(acc ^ _sm64(k64))
    return _sm64(acc)


def _u53(h):
    return (_lsr(h, 11).to(torch.float64) / float(1 << 53)).to(torch.float32)


def hash_uniform_t(*keys, count=1, salt=0):
    base = _sm64(_mix_keys_t(*keys) ^ _as_i64(salt))
    cols = torch.arange(count, dtype=torch.int64, device=base.device)
    return _u53(_sm64(base.unsqueeze(-1) ^ (cols + _sm64(cols))))


def hash_gaussian_t(*keys, count=1, salt=0):
    base = _sm64(_mix_keys_t(*keys) ^ _as_i64(salt) ^ _SGAUSS)
    cols = torch.arange(count, dtype=torch.int64, device=base.device)
    out = torch.zeros(base.shape + (count,), dtype=torch.float32, device=base.device)
    for t in range(12):
        tt = _as_i64(t * _sm64_int((t + 0x1D8E4E27C47D124F) & ((1 << 64) - 1)))
        out += _u53(_sm64(base.unsqueeze(-1) ^ (cols + tt)))
    return out - np.float32(6.0)


def hash_index_t(*keys, count=1, modulus, salt=0):
    base = _sm64(_mix_keys_t(*keys) ^ _as_i64(salt) ^ _SINDEX)
    cols = torch.arange(count, dtype=torch.int64, device=base.device)
    h = _sm64(base.unsqueeze(-1) ^ (cols + _sm64(cols + _SINDEX)))
    m = int(modulus)
    corr = (1 << 64) % m
    r = h % m
    return torch.where(h < 0, (r + corr) % m, r)


def _cos2pi_t(x, tab):
    t = x - torch.floor(x)
    q = t * np.float32(4.0)
    qf = torch.floor(q)
    qi = qf.to(torch.int64) & 3
    f = q - qf
    a = torch.where((qi & 1) == 0, f, np.float32(1.0) - f)
    idx = a * np.float32(512.0)
    i0 = torch.minimum(idx.to(torch.int64), torch.tensor(511, device=x.device))
    frac = (idx - i0).to(torch.float32)
    v = (
        tab[i0] * (np.float32(1.0) - frac)
        + tab[torch.minimum(i0 + 1, torch.tensor(512, device=x.device))] * frac
    )
    sign = torch.where((qi == 1) | (qi == 2), np.float32(-1.0), np.float32(1.0))
    return v * sign


def _first_index(inv, n_unique, device):
    first = torch.full((n_unique,), 1 << 62, dtype=torch.int64, device=device)
    pos = torch.arange(inv.shape[0], dtype=torch.int64, device=device)
    first.scatter_reduce_(0, inv, pos, reduce="amin")
    return first


def _row_normalize_np(t):
    a = t.cpu().numpy()
    a = a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-12)
    return torch.from_numpy(a).to(t.device)


def segment_corpus_gpu(p, n, dim, seed, chunk=50_000, rows=None, device="cuda"):
    """Byte-identical GPU emission of ``segment_corpus(p, n, dim, seed)``."""
    if torch is None:
        raise RuntimeError("torch unavailable; use segment_gen.segment_corpus")
    dev = torch.device(device)
    tab = torch.from_numpy(np.asarray(_TAB)).to(dev)
    artlen = torch.from_numpy(np.asarray(_ART_LEN)).to(dev)

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
    path_mix = min(1.0, max(0.0, float(p.get("path_mix", 1.0))))
    rho = min(1.0, max(0.0, float(p.get("rho", 0.0))))
    level_frames = bool(round(p.get("level_frames", 0.0)))
    pool_alpha = float(p.get("pool_alpha", 0.0))
    w_cont = min(1.0, max(0.0, float(p.get("w_cont", 0.0))))
    cont_lat = max(1, int(round(p.get("cont_lat", 2.0))))
    cont_bw = float(p.get("cont_bw", 0.5))
    cont_oct = max(1, int(round(p.get("cont_oct", 3.0))))
    cont_freq = max(4, int(round(p.get("cont_freq", 24.0))))

    ncl = [
        max(2, int(round((arr_window / _ART_MEAN) / (27 * branch**L))))
        for L in range(arr_levels)
    ]

    rng = np.random.default_rng(seed)
    pool_np = rng.standard_normal((n_pool, dim)).astype(np.float32) / np.sqrt(
        dim, dtype=np.float32
    )
    if pool_alpha > 0.0:
        w = (1.0 + np.arange(n_pool, dtype=np.float64)) ** (-pool_alpha)
        w /= np.sqrt((w**2).mean())
        pool_np *= w.astype(np.float32)[:, None]
    pool = torch.from_numpy(pool_np).to(dev)
    if level_frames:
        frames = [
            np.linalg.qr(rng.standard_normal((dim, d_glob)))[0].astype(np.float32)
            for _ in range(arr_levels)
        ]
    else:
        frames = [
            np.linalg.qr(rng.standard_normal((dim, d_glob)))[0].astype(np.float32)
        ] * arr_levels
    frames_t = [torch.from_numpy(f).to(dev) for f in frames]
    cont_assets = None
    if w_cont > 0.0:
        cont_assets = []
        for o in range(cont_oct):
            Wo = (
                rng.standard_normal((cont_freq, cont_lat)) * cont_bw * (2.0**o)
            ).astype(np.float32)
            phio = rng.uniform(0.0, 1.0, cont_freq).astype(np.float32)
            Fo = np.linalg.qr(rng.standard_normal((dim, cont_freq)))[0].astype(
                np.float32
            )
            cont_assets.append(
                (
                    torch.from_numpy(Wo).to(dev),
                    torch.from_numpy(phio).to(dev),
                    torch.from_numpy(Fo).to(dev),
                )
            )
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

    def _hier_block_t(keys, pos, rate, salt):
        chosen = torch.full_like(pos, _MAXLEV)
        found = torch.zeros_like(pos, dtype=torch.bool)
        for j in range(_MAXLEV):
            blk = pos >> j
            bit = (
                hash_uniform_t(keys, torch.full_like(pos, j), blk, count=1, salt=salt)[
                    ..., 0
                ]
                < rate
            )
            take = bit & (~found)
            chosen = torch.where(take, torch.full_like(chosen, j), chosen)
            found |= bit
        return (chosen << 32) | (pos >> chosen)

    def _articles_t(idx):
        sb = idx >> _SB_BITS
        r = idx & (_SB - 1)
        u_sb, sb_inv = torch.unique(sb, return_inverse=True)
        lens = artlen[hash_index_t(u_sb, count=_SB, modulus=256, salt=7)]
        ends = torch.cumsum(lens, dim=1)
        art = torch.empty_like(idx)
        pos = torch.empty_like(idx)
        start = torch.empty_like(idx)
        for s in range(u_sb.shape[0]):
            g = sb_inv == s
            m = torch.searchsorted(ends[s], r[g], right=True)
            art[g] = (u_sb[s] << (_SB_BITS + 1)) | m
            st = torch.where(
                m > 0, ends[s][torch.clamp(m - 1, min=0)], torch.zeros_like(m)
            )
            pos[g] = r[g] - st
            start[g] = (u_sb[s] << _SB_BITS) + st
        return art, pos, start

    def _share(priv, cl, art, extra, count, salt_dir, salt_gate):
        if rho <= 0.0:
            return priv
        sh = hash_index_t(cl, extra, count=count, modulus=n_pool, salt=salt_dir)
        gt = hash_uniform_t(art, extra, count=count, salt=salt_gate) < rho
        return torch.where(gt, sh, priv)

    want_np = (
        np.arange(n, dtype=np.int64)
        if rows is None
        else np.asarray(rows, dtype=np.int64)
    )
    out = np.empty((len(want_np), dim), dtype=np.float32)
    for cs in range(0, len(want_np), chunk):
        ce = min(cs + chunk, len(want_np))
        idx = torch.from_numpy(want_np[cs:ce]).to(dev)
        art, pos, art_start = _articles_t(idx)
        win = art_start // arr_window
        seg = _hier_block_t(art, pos, seg_break, salt=23)
        sid = _mix_keys_t(art, seg)

        u_art, art_inv = torch.unique(art, return_inverse=True)
        art_first = _first_index(art_inv, u_art.shape[0], dev)
        u_win = win[art_first]
        u_sid, sid_inv = torch.unique(sid, return_inverse=True)
        sid_first = _first_index(sid_inv, u_sid.shape[0], dev)

        acc = torch.zeros((ce - cs, dim), dtype=torch.float32, device=dev)
        cl0 = None
        for L in range(arr_levels):
            cid = hash_index_t(
                u_art, torch.full_like(u_art, L), count=1, modulus=ncl[L], salt=41
            )[..., 0]
            if L == 0:
                cl0 = u_win * 1_000_003 + cid
            coef = hash_gaussian_t(
                u_win, torch.full_like(u_art, L), cid, count=d_glob, salt=43
            )
            coef = _row_normalize_np(coef) if False else coef
            cf = coef.cpu().numpy()
            cf /= np.maximum(np.linalg.norm(cf, axis=1, keepdims=True), 1e-12)
            coef = torch.from_numpy(cf).to(dev)
            _cw = float(lw[L]) * (float(wc_bak) if cont_assets is not None else 1.0)
            proj = torch.zeros((u_art.shape[0], dim), dtype=torch.float32, device=dev)
            fr = frames_t[L]
            for j in range(d_glob):
                proj += coef[:, j : j + 1] * fr[:, j].unsqueeze(0)
            acc += np.float32(_cw) * proj[art_inv]
        if cont_assets is not None:
            ul = hash_uniform_t(u_art, count=cont_lat, salt=149)
            cont = torch.zeros((u_art.shape[0], dim), dtype=torch.float32, device=dev)
            for o, (Wo, phio, Fo) in enumerate(cont_assets):
                phase = phio.unsqueeze(0).repeat(u_art.shape[0], 1)
                for dd_ in range(cont_lat):
                    phase = phase + ul[:, dd_ : dd_ + 1] * Wo[:, dd_].unsqueeze(0)
                feat = _cos2pi_t(phase, tab) * np.float32(np.sqrt(2.0 / cont_freq))
                fproj = torch.zeros_like(cont)
                for j in range(cont_freq):
                    fproj += feat[:, j : j + 1] * Fo[:, j].unsqueeze(0)
                cont += np.float32(float(cont_low[o])) * fproj
            acc += np.float32(w_cont) * cont[art_inv]
            del cont
        row_cl0 = cl0[art_inv]
        u_cl = row_cl0[sid_first]
        u_sart = art[sid_first]

        sdir = _share(
            hash_index_t(u_sid, count=d_loc, modulus=n_pool, salt=53),
            u_cl,
            u_sart,
            torch.zeros_like(u_cl),
            d_loc,
            97,
            101,
        )
        sco = hash_gaussian_t(u_sid, count=d_loc, salt=57)
        sc = sco.cpu().numpy()
        sc /= np.maximum(np.linalg.norm(sc, axis=1, keepdims=True), 1e-12)
        sco = torch.from_numpy(sc).to(dev)
        cen = torch.zeros((u_sid.shape[0], dim), dtype=torch.float32, device=dev)
        for j in range(d_loc):
            cen += (np.float32(w_loc) * sco[:, j]).unsqueeze(1) * pool[sdir[:, j]]
        acc += cen[sid_inv]
        del cen

        for L in range(nlev):
            key = sid * 31 + L
            blk = pos >> L
            c = hash_gaussian_t(key, blk, count=fil_dim, salt=61)
            dd = _share(
                hash_index_t(key, blk, count=fil_dim, modulus=n_pool, salt=67),
                row_cl0,
                art,
                torch.full_like(row_cl0, L),
                fil_dim,
                107,
                109,
            )
            amp = inv * wp * plw[L]
            for j in range(fil_dim):
                acc += (np.float32(amp) * c[:, j]).unsqueeze(1) * pool[dd[:, j]]
            del c, dd
        if wb > 0.0:
            bdir = _share(
                hash_index_t(u_sid, count=fil_dim, modulus=n_pool, salt=71),
                u_cl,
                u_sart,
                torch.zeros_like(u_cl),
                fil_dim,
                113,
                127,
            )
            bdir = bdir[sid_inv]
            bco = hash_gaussian_t(sid, pos + 1, count=fil_dim, salt=79)
            bamp = inv * wb
            for j in range(fil_dim):
                acc += (np.float32(bamp) * bco[:, j]).unsqueeze(1) * pool[bdir[:, j]]
            del bdir, bco
        out[cs:ce] = acc.cpu().numpy()
        del acc
    out = normalize(out)

    # blend passes: verbatim CPU mirrors of segment_gen's dup/echo layers
    p_dup = min(0.5, max(0.0, float(p.get("p_dup", 0.0))))
    alpha_dup = float(p.get("alpha_dup", 0.95))
    dup_window = int(round(float(p.get("dup_window", 0.0)))) or arr_window
    if p_dup > 0.0:
        gate = hash_uniform(want_np, count=1, salt=131)[..., 0] < p_dup
        if gate.any():
            win0 = (want_np // np.int64(dup_window)) * np.int64(dup_window)
            src = (
                win0
                + hash_index(want_np, count=1, modulus=dup_window, salt=137)[..., 0]
            )
            gi = np.nonzero(gate)[0]
            u_src, s_inv = np.unique(src[gi], return_inverse=True)
            base_p = dict(p)
            base_p["p_dup"] = 0.0
            src_rows = segment_corpus_gpu(
                base_p, 0, dim, seed, chunk=chunk, rows=u_src, device=device
            )
            a = np.float32(alpha_dup)
            b = np.float32(np.sqrt(max(0.0, 1.0 - float(alpha_dup) ** 2)))
            out[gi] = normalize(a * src_rows[s_inv] + b * out[gi])
    p_echo = min(0.5, max(0.0, float(p.get("p_echo", 0.0))))
    echo_k = max(2, int(round(p.get("echo_k", 3.0))))
    echo_win = max(1000, int(round(p.get("echo_win", 100000.0))))
    echo_alpha = float(p.get("echo_alpha", 0.96))
    if p_echo > 0.0:
        egate = hash_uniform(want_np, count=1, salt=151)[..., 0] < p_echo
        if egate.any():
            ei = np.nonzero(egate)[0]
            w_no = want_np[ei] // np.int64(echo_win)
            m_w = max(2, int(round(p_echo * echo_win / echo_k)))
            gid = hash_index(want_np[ei], count=1, modulus=m_w, salt=157)[..., 0]
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
            sr = segment_corpus_gpu(
                base_p, 0, dim, seed, chunk=chunk, rows=u_src, device=device
            )
            proto = normalize(sr[src_inv[: len(s1)]] + sr[src_inv[len(s1) :]])
            a = np.float32(echo_alpha)
            b = np.float32(np.sqrt(max(0.0, 1.0 - float(echo_alpha) ** 2)))
            out[ei] = normalize(a * proto[g_inv] + b * out[ei])
    return out


FROZEN = {
    "rc3": ("e84236658665bc2d", dict(), 2027),
    "rc7": ("fa6342a0193a23ba", None, 3001),  # F8 = the committed defaults
}


def verify(device="cuda"):
    """Regenerate the frozen 6k references on GPU; assert byte identity."""
    import hashlib

    from .segment_gen import SEGMENT_PARAMS

    p = {k: d for k, _, _, d in SEGMENT_PARAMS}
    h7 = hashlib.sha256(
        segment_corpus_gpu(p, 6000, 1024, 3001, device=device).tobytes()
    ).hexdigest()
    assert h7.startswith("fa6342a0193a23ba"), "gpu RC-7 mismatch: " + h7
    p3 = dict(p)
    p3["p_dup"] = 0.0
    p3["w_cont"] = 0.0
    h3 = hashlib.sha256(
        segment_corpus_gpu(p3, 6000, 1024, 2027, device=device).tobytes()
    ).hexdigest()
    assert h3.startswith("e84236658665bc2d"), "gpu RC-3 mismatch: " + h3
    return h7, h3
