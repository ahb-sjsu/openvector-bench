"""RC1_PLAN Phase A: fix g1 — decay sweep x ball/path mixture.

PREDICTIONS, stated before the run (R60/R61 measured g1 at 4.31-4.87,
invariant to d_glob, fil_dim, brk and w_loc):

The diagnosis (RC1_PLAN §3.1): in a pure dyadic path, adjacent rows differ at
level 0 and gap-2 rows at levels 0+1, so the two-NN ratio is pinned at
mu ~ sqrt(1 + decay). The path level-variance decay has been 0.72 since R49 --
never swept -- predicting TwoNN ~3.7 (measured 4.3-4.9), and predicting
decay ~0.125 hits real's 17.23.

  * (decay 0.125, pure path): g1 -> ~17.  Mechanism check. Autocorrelation
    should COLLAPSE toward two-level; NN index gap stays 1.
  * (decay 0.72, mix 0.4): g1 -> ~17 with NN gap ~3.  The anatomical fix --
    R42 measured mix 0.4 -> g1 17.01 directly, and real's k=1 neighbour sits
    at median index gap 3, not 1 (R34): its article is a cloud, not a chain.
  * KILL: (decay 0.125, pure path) leaving g1 < 8 falsifies the diagnosis.

The mixture: within-segment displacement = sqrt(mix)*path + sqrt(1-mix)*ball,
variance-preserving (the R42 convention). The ball's directions are keyed on
the SEGMENT and its coefficients per row, so it stays random-access and the
displacement stays inside the segment's subspace.

Anatomy measured alongside summaries (the R46/R57 lesson): registered Facco
g1, k=1 NN median index gap (real: 3), autocorrelation (real: 0.598, 0.530,
0.449, 0.367, 0.304 at gaps 1,2,4,8,16), s(k), g5, g6, D_article, overlap,
and both §3b spans.

Config: the §3b-relevant point P_B (brk 0.030, w_loc 0.6, branch 64,
d_glob 30) so Phase B can re-adjudicate from the same lineage.
"""

import json
import os
import time

import numpy as np
import torch  # noqa: E402

from hashgpu import hgauss_t, hidx_t, hunif_t, verify

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("device=" + DEV, flush=True)
verify(DEV)

DIM, ART_MEAN, POOL = 1024, 23, 600000
N_FIX, NQ = 25000, 10000
NEED = N_FIX + NQ
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})
REAL_S = np.array(
    [
        8.82,
        9.43,
        11.46,
        14.02,
        16.08,
        20.11,
        23.40,
        26.01,
        28.88,
        29.98,
        31.29,
        33.19,
        34.02,
        34.82,
        35.53,
        35.73,
    ]
)
MAXLEV = 8


def normalize_t(x):
    return x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)


def seg_of(a_t, pos_t, brk):
    chosen = torch.full_like(pos_t, MAXLEV)
    found = torch.zeros_like(pos_t, dtype=torch.bool)
    for j in range(MAXLEV):
        key = a_t * 1000003 + 104729 * (j + 1) + (pos_t >> j)
        bit = hunif_t(key, 1)[..., 0] < brk
        chosen = torch.where(bit & (~found), torch.full_like(chosen, j), chosen)
        found = found | bit
    return a_t * 1000003 + chosen * 7919 + (pos_t >> chosen)


def build(
    brk,
    branch,
    d_glob,
    decay,
    mix,
    fil_dim=48,
    nlev=6,
    d_loc=64,
    w_loc=0.6,
    fil_scale=1.0,
    arr_levels=3,
    size_spread=1.2,
    log2_pool=13,
    seed=41,
):
    rng = np.random.default_rng(seed)
    ln = rng.lognormal(
        np.log(ART_MEAN) - 0.5 * size_spread**2,
        size_spread,
        int(POOL / ART_MEAN * 2.5) + 16,
    )
    b = np.cumsum(np.maximum(1, np.round(ln)).astype(np.int64))
    b = np.append(b[b < POOL], POOL)
    n_art = len(b)
    starts = np.concatenate([[0], b[:-1]])
    npool = int(2**log2_pool)
    pool = torch.from_numpy(
        (rng.standard_normal((npool, DIM)) / np.sqrt(DIM)).astype(np.float32)
    ).to(DEV)
    bg = torch.from_numpy(
        np.linalg.qr(rng.standard_normal((DIM, d_glob)))[0].astype(np.float32)
    ).to(DEV)
    cen = torch.zeros((n_art, DIM), device=DEV)
    lw = np.array([0.72**L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    for L in range(arr_levels):
        ncl = max(2, int(round(n_art / (27 * branch**L))))
        cid = torch.from_numpy(rng.integers(0, ncl, n_art)).to(DEV)
        cc = rng.standard_normal((ncl, d_glob)).astype(np.float32)
        cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
        cen += float(lw[L]) * (torch.from_numpy(cc).to(DEV)[cid] @ bg.T)

    # Path level weights: variance ratio `decay` per level. At decay 0.72 this
    # is EXACTLY the R49-R61 schedule (the 0.45 constant normalizes out), so the
    # baseline arm reproduces the prior lineage bit-comparably.
    plw = np.sqrt(np.array([decay**i for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)

    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]
    x = torch.empty((POOL, DIM), device=DEV)
    wp = float(np.sqrt(mix))
    wb = float(np.sqrt(max(0.0, 1.0 - mix)))
    for st in range(0, POOL, 50000):
        en = min(st + 50000, POOL)
        a_t = torch.from_numpy(a_of[st:en].astype(np.int64)).to(DEV)
        p_t = torch.from_numpy(pos[st:en]).to(DEV)
        acc = cen[a_t].clone()
        sid = seg_of(a_t, p_t, brk)
        sdir = hidx_t(sid, d_loc, npool)
        sco = hgauss_t(sid, d_loc)
        sco = sco / sco.norm(dim=1, keepdim=True).clamp_min(1e-12)
        for j in range(d_loc):
            acc += (w_loc * sco[:, j]).unsqueeze(1) * pool[sdir[:, j]]
        # within-segment path (variance share `mix`)
        for L in range(nlev):
            key = sid * 31 + L * 7919 + (p_t >> L)
            c = hgauss_t(key, fil_dim)
            dd = hidx_t(key, fil_dim, npool)
            amp = float(fil_scale * wp * plw[L] / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (amp * c[:, j]).unsqueeze(1) * pool[dd[:, j]]
            del c, dd
        # within-segment ball (variance share 1-mix): directions keyed on the
        # segment, coefficients per row -> NN is no longer deterministically the
        # index-adjacent row, which is the anatomical point (real NN gap ~3).
        if wb > 0.0:
            bdir = hidx_t(sid * 100003 + 7, fil_dim, npool)
            bco = hgauss_t(sid * 1009 + (p_t + 1) * 500009 + 11, fil_dim)
            bamp = float(fil_scale * wb / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (bamp * bco[:, j]).unsqueeze(1) * pool[bdir[:, j]]
            del bdir, bco
        x[st:en] = acc
        del acc
    del cen
    return normalize_t(x), a_of


def knn_t(base, q, k, bs=6144):
    od, oi = [], []
    for s in range(0, q.shape[0], bs):
        sim = q[s : s + bs] @ base.T
        dv, iv = torch.topk(sim, k, dim=1)
        od.append((2.0 - 2.0 * dv).clamp_min(0).sqrt())
        oi.append(iv)
    return torch.cat(od), torch.cat(oi)


def exch(sup, nb, nq, seed=31):
    p = np.random.default_rng(seed).permutation(np.asarray(sup))[: nb + nq]
    return np.sort(p[:nb]), np.sort(p[nb:])


def clumped(n_rows, need, bb, rng):
    nb = int(np.ceil(need / bb)) + 8
    st = rng.choice(max(1, n_rows - bb), size=nb, replace=False)
    idx = np.unique((st[:, None] + np.arange(bb)[None, :]).ravel())
    while len(idx) < need:
        idx = np.unique(
            np.concatenate(
                [idx, rng.choice(n_rows, need - len(idx) + 64, replace=False)]
            )
        )
    return np.sort(rng.permutation(idx)[:need])


def id_twonn(d):
    """Facco two-NN MLE, trimmed at the 90th percentile of mu -- as registered."""
    r1, r2 = d[:, 0], d[:, 1]
    m = r1 > 0
    mu = r2[m] / np.maximum(r1[m], 1e-12)
    mu = mu[mu > 1.0]
    if len(mu) < 100:
        return float("nan")
    mu = mu[mu <= np.quantile(mu, 0.9)]
    return float(len(mu) / np.sum(np.log(mu)))


ARMS = [
    (0.72, 0.6),
    (0.72, 0.5),
    (0.60, 0.6),
    (0.60, 0.5),
    (0.50, 0.6),
    (0.50, 0.5),
    (0.40, 0.5),
    (0.40, 0.45),
]
_i = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
mine = [ARMS[_i]] if _i < len(ARMS) else []
out = {}
for decay, mix in mine:
    t0 = time.time()
    x, a_of = build(0.030, 64, 30, decay, mix)

    # autocorrelation (real: 0.598, 0.530, 0.449, 0.367, 0.304)
    ac = [
        round(float((x[:100000] * x[g : 100000 + g]).sum(1).mean().item()), 3)
        for g in (1, 2, 4, 8, 16)
    ]

    # gates protocol: 200k base + 10k queries, exchangeable
    bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
    d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)], x[torch.from_numpy(qi).to(DEV)], 100)
    dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
    del d, nn
    g1 = id_twonn(dn)
    nn_gap = float(np.median(np.abs(bi[nnn[:, 0]] - qi)))
    cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
    g6 = float(((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12))
    bt = x[torch.from_numpy(bi).to(DEV)]
    rr = torch.randperm(bt.shape[0], device=DEV)[:4096]
    mean_d = float(
        (2.0 - 2.0 * (x[torch.from_numpy(qi[:512]).to(DEV)] @ bt[rr].T))
        .clamp_min(0)
        .sqrt()
        .mean()
    )
    g5 = mean_d / float(np.median(dn[:, 9]))
    del bt

    # clumped-protocol s(k) + anatomy
    rng = np.random.default_rng(20_100)
    b2, q2 = exch(clumped(POOL, NEED, 100, rng), N_FIX, NQ)
    d2, n2 = knn_t(
        x[torch.from_numpy(b2).to(DEV)], x[torch.from_numpy(q2).to(DEV)], 500
    )
    dm, nm = d2.cpu().numpy(), n2.cpu().numpy()
    del d2, n2
    r = np.array([float(np.median(dm[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    rms = float(np.sqrt(np.mean((s - REAL_S) ** 2)))
    same = a_of[b2[nm]] == a_of[q2][:, None]
    din, dout = dm[same], dm[~same]
    D = float(np.percentile(din, 90) / max(np.percentile(din, 10), 1e-9))
    ovl = float((dout < np.percentile(din, 90)).mean())

    # §3b spans
    sp = {}
    for P in (50000, 600000):
        rg = np.random.default_rng(700 + P // 1000)
        b3, q3 = exch(rg.choice(P, NEED, replace=False), N_FIX, NQ)
        d3, _ = knn_t(
            x[torch.from_numpy(b3).to(DEV)], x[torch.from_numpy(q3).to(DEV)], 500
        )
        d3n = d3.cpu().numpy()
        r3 = np.array([float(np.median(d3n[:, k - 1])) for k in KG])
        s3 = np.gradient(np.log(np.array(KG, float)), np.log(r3))
        sp[P] = (float(s3[-1] / max(s3[0], 1e-9)), id_twonn(d3n))
        del d3
    rspan = sp[50000][0] - sp[600000][0]
    gspan = float(np.log(sp[50000][1] / sp[600000][1]))
    del x

    out["decay%s_mix%s" % (decay, mix)] = {
        "g1": g1,
        "nn_gap": nn_gap,
        "g5": g5,
        "g6": g6,
        "rms": rms,
        "autocorr": ac,
        "s": [float(v) for v in s],
        "D_article": D,
        "overlap": ovl,
        "ratio_span": rspan,
        "logg1_span": gspan,
    }
    print(
        "decay %.3f mix %.1f | g1 %6.2f  NNgap %4.0f | g5 %5.3f g6 %5.3f | "
        "rms %5.2f s14 %5.1f | ac %s | span r %+6.3f g %+6.3f  (%.0fs)"
        % (
            decay,
            mix,
            g1,
            nn_gap,
            g5,
            g6,
            rms,
            s[4],
            ac,
            rspan,
            gspan,
            time.time() - t0,
        ),
        flush=True,
    )
    print("RESULT_JSON " + json.dumps(out), flush=True)

print(
    "real              | g1  17.23  NNgap    3 | g5 1.369 g6 1.696 | "
    "rms  0.00 s14  16.1 | ac [0.598, 0.53, 0.449, 0.367, 0.304] | "
    "span r +2.397 g -0.494"
)
print("PHASEA_DONE", flush=True)
