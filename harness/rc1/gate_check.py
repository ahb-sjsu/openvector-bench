"""R59: the registered gates at R58's best operating point.

R56-R58 tracked only s(k) and an inline hubness skew. The `g1` reported there
was wrong twice over -- `log(2)/mean(log mu)` where the registered Facco MLE is
`n / sum(log mu)` with mu trimmed to (1, q90] -- so it carried a spurious 0.693
factor and no trimming. It was flagged as non-comparable; this measures the real
thing.

R57 is the reason to do this before more tuning: a summary can look right while
the curve underneath is wrong, and rms alone does not see the gates.

Estimators mirror openvector_bench.geometry exactly:
  g1  id_twonn      n / sum(log mu),  mu = r2/r1 in (1, q90]
  g3  eff_rank      (sum lam)^2 / sum(lam^2)  on the centred base
  g4  dims90        first index where cumulative variance >= 0.90
  g5  rel_contrast  mean random-pair distance / median r(k)
  g6  hubness       skew of the k-occurrence counts
g8 (pca_retention) is omitted: it needs a second full k-NN in PCA space and
would push the pod past the ~60 s window that R57 established.
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
    plw = np.sqrt(np.array([0.45 * (0.72**i) for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]
    x = torch.empty((POOL, DIM), device=DEV)
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
        for L in range(nlev):
            key = sid * 31 + L * 7919 + (p_t >> L)
            c = hgauss_t(key, fil_dim)
            dd = hidx_t(key, fil_dim, npool)
            amp = float(fil_scale * plw[L] / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (amp * c[:, j]).unsqueeze(1) * pool[dd[:, j]]
            del c, dd
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


def spectrum_t(base_t):
    xc = base_t - base_t.mean(0, keepdim=True)
    lam = torch.linalg.svdvals(xc) ** 2 / max(xc.shape[0] - 1, 1)
    lam = lam[lam > 0].double()
    frac = torch.cumsum(lam, 0) / lam.sum()
    eff = float(lam.sum() ** 2 / (lam**2).sum())
    d90 = int(
        torch.searchsorted(
            frac, torch.tensor(0.90, dtype=frac.dtype, device=frac.device)
        ).item()
        + 1
    )
    return eff, d90


ARMS = [(0.143, 64, 30), (0.143, 64, 38), (0.143, 32, 30), (0.143, 64, 45)]
_i = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
mine = [ARMS[_i]] if _i < len(ARMS) else []
out = {}
for brk, branch, dg in mine:
    t0 = time.time()
    x, a_of = build(brk, branch, dg)
    # gates protocol: 200k base, 10k queries, uniform exchangeable split
    bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
    bt = x[torch.from_numpy(bi).to(DEV)]
    qt = x[torch.from_numpy(qi).to(DEV)]
    d, nn = knn_t(bt, qt, 100)
    dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
    g1 = id_twonn(dn)
    cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
    g6 = float(((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12))
    rr = torch.randperm(bt.shape[0], device=DEV)[:4096]
    ref = bt[rr]
    qq = qt[:512]
    mean_d = float((2.0 - 2.0 * (qq @ ref.T)).clamp_min(0).sqrt().mean())
    g5 = mean_d / float(np.median(dn[:, 9]))
    g3, g4 = spectrum_t(bt[:50000])
    del bt, qt, d, nn
    # profile + §3b spans on the clumped protocol
    rng = np.random.default_rng(20_100)
    b2, q2 = exch(clumped(POOL, NEED, 100, rng), N_FIX, NQ)
    d2, _ = knn_t(x[torch.from_numpy(b2).to(DEV)], x[torch.from_numpy(q2).to(DEV)], 500)
    dm = d2.cpu().numpy()
    r = np.array([float(np.median(dm[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    rms = float(np.sqrt(np.mean((s - REAL_S) ** 2)))
    del d2
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
    out["brk%s_br%s_dg%s" % (brk, branch, dg)] = {
        "g1": g1,
        "g3_eff_rank": g3,
        "g4_dims90": g4,
        "g5": g5,
        "g6": g6,
        "rms": rms,
        "ratio_span": rspan,
        "logg1_span": gspan,
        "s": [float(v) for v in s],
    }
    print(
        "br%-3d dg%-3d | g1 %6.2f  g3 %6.1f  g4 %4d  g5 %5.3f  g6 %5.3f | "
        "rms %5.2f | span r %+6.3f g %+6.3f  (%.0fs)"
        % (branch, dg, g1, g3, g4, g5, g6, rms, rspan, gspan, time.time() - t0),
        flush=True,
    )
    print("RESULT_JSON " + json.dumps(out), flush=True)

print(
    "real        | g1  17.23  g3  182.3  g4  359  g5 1.369  g6 1.696 | "
    "rms  0.00 | span r +2.397 g -0.494"
)
print("GATE_CHECK_DONE", flush=True)
