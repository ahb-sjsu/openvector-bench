"""RC1_PLAN Phase C: alignment for s(53)/g3/g4 (and now g6).

Mechanism under test: real's neighbourhood subspaces SHARE structure — `R39`
measured mean principal angle 68.1 deg between the 36-dim local subspaces of
different neighbourhoods against the generator family's 80.3, and real's local
eff_rank (168.4) nearly coincides with its global (182.3) where the generator's
diverged. The indicated fix, never implemented: correlated direction sets.

Two implementations probed:
  * rho — articles within a 27-cluster draw a fraction rho of their direction
    slots from a cluster-shared set (gates and shared indices all keyed, so
    random access survives);
  * log2_pool DOWN — a smaller shared pool forces reuse globally. Swept upward
    in `R43` (nothing); never downward. R39's local~global coincidence is
    maximal sharing, and pool size is its simplest lever.

Registered targets: angle -> 68, local eff_rank -> 168 with local ~ global,
s(53) -> 28.9, g4 -> 359. KILL: angle ~68 with s(53) unmoved -> R39's
discriminator is a correlate, not a mechanism.

Arm 0 (rho=0, lp=13) is the Phase B champion unchanged — a bit-consistency
check across code edits (expect RATIO +2.381, logG1 -0.475, g1 15.45).

Champion config: brk 0.125, w_loc 0.6, d_glob 24, decay 0.50, mix 0.6,
branch 64, fil_dim 48, nlev 6, d_loc 64, fil_scale 1.0, size_spread 1.2.
"""

import json
import os
import time

import numpy as np
import torch

from hashgpu import hgauss_t, hidx_t, hunif_t, verify

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("device=" + DEV, flush=True)
verify(DEV)

DIM, ART_MEAN, POOL = 1024, 23, 600000
N_FIX, NQ = 25000, 10000
NEED = N_FIX + NQ
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})
REAL_S = np.array([8.82, 9.43, 11.46, 14.02, 16.08, 20.11, 23.40, 26.01,
                   28.88, 29.98, 31.29, 33.19, 34.02, 34.82, 35.53, 35.73])
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


def build(brk=0.125, branch=64, d_glob=24, decay=0.50, mix=0.6, rho=0.0,
          log2_pool=13, fil_dim=48, nlev=6, d_loc=64, w_loc=0.6,
          fil_scale=1.0, arr_levels=3, size_spread=1.2, seed=41):
    rng = np.random.default_rng(seed)
    ln = rng.lognormal(np.log(ART_MEAN) - 0.5 * size_spread ** 2, size_spread,
                       int(POOL / ART_MEAN * 2.5) + 16)
    b = np.cumsum(np.maximum(1, np.round(ln)).astype(np.int64))
    b = np.append(b[b < POOL], POOL)
    n_art = len(b)
    starts = np.concatenate([[0], b[:-1]])
    npool = int(2 ** log2_pool)
    pool = torch.from_numpy(
        (rng.standard_normal((npool, DIM)) / np.sqrt(DIM)).astype(np.float32)).to(DEV)
    bg = torch.from_numpy(np.linalg.qr(rng.standard_normal((DIM, d_glob)))[0]
                          .astype(np.float32)).to(DEV)
    cen = torch.zeros((n_art, DIM), device=DEV)
    lw = np.array([0.72 ** L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    cl0 = None
    for L in range(arr_levels):
        ncl = max(2, int(round(n_art / (27 * branch ** L))))
        cid = torch.from_numpy(rng.integers(0, ncl, n_art)).to(DEV)
        if L == 0:
            cl0 = cid.clone()          # the 27-article cluster, for sharing
        cc = rng.standard_normal((ncl, d_glob)).astype(np.float32)
        cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
        cen += float(lw[L]) * (torch.from_numpy(cc).to(DEV)[cid] @ bg.T)

    plw = np.sqrt(np.array([decay ** i for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]
    x = torch.empty((POOL, DIM), device=DEV)
    wp = float(np.sqrt(mix))
    wb = float(np.sqrt(max(0.0, 1.0 - mix)))

    def share(priv, cl_row, comp_salt, gate_keys, count):
        """Replace a fraction rho of direction slots with cluster-shared draws.

        Gates and shared indices are keyed, so this is a pure function of the
        row — random access survives. rho=0 returns priv untouched (and makes
        no hash calls), keeping the baseline bit-identical to Phase B.
        """
        if rho <= 0.0:
            return priv
        sh = hidx_t(cl_row * 131 + comp_salt, count, npool)
        gt = hunif_t(gate_keys, count) < rho
        return torch.where(gt, sh, priv)

    for st in range(0, POOL, 50000):
        en = min(st + 50000, POOL)
        a_t = torch.from_numpy(a_of[st:en].astype(np.int64)).to(DEV)
        p_t = torch.from_numpy(pos[st:en]).to(DEV)
        cl_row = cl0[a_t].long()
        acc = cen[a_t].clone()
        sid = seg_of(a_t, p_t, brk)
        sdir = share(hidx_t(sid, d_loc, npool), cl_row, 17,
                     a_t * 271 + 19, d_loc)
        sco = hgauss_t(sid, d_loc)
        sco = sco / sco.norm(dim=1, keepdim=True).clamp_min(1e-12)
        for j in range(d_loc):
            acc += (w_loc * sco[:, j]).unsqueeze(1) * pool[sdir[:, j]]
        for L in range(nlev):
            key = sid * 31 + L * 7919 + (p_t >> L)
            c = hgauss_t(key, fil_dim)
            dd = share(hidx_t(key, fil_dim, npool), cl_row, L * 7 + 23,
                       a_t * 271 + L * 11 + 29, fil_dim)
            amp = float(fil_scale * wp * plw[L] / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (amp * c[:, j]).unsqueeze(1) * pool[dd[:, j]]
            del c, dd
        if wb > 0.0:
            bdir = share(hidx_t(sid * 100003 + 7, fil_dim, npool), cl_row, 97,
                         a_t * 271 + 41, fil_dim)
            bco = hgauss_t(sid * 1009 + (p_t + 1) * 500009 + 11, fil_dim)
            bamp = float(fil_scale * wb / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (bamp * bco[:, j]).unsqueeze(1) * pool[bdir[:, j]]
            del bdir, bco
        x[st:en] = acc
        del acc
    del cen
    return normalize_t(x), a_of


def knn_t(base, q, k, bs=4096):
    od, oi = [], []
    for s in range(0, q.shape[0], bs):
        sim = q[s:s + bs] @ base.T
        dv, iv = torch.topk(sim, k, dim=1)
        od.append((2.0 - 2.0 * dv).clamp_min(0).sqrt())
        oi.append(iv)
    return torch.cat(od), torch.cat(oi)


def exch(sup, nb, nq, seed=31):
    p = np.random.default_rng(seed).permutation(np.asarray(sup))[:nb + nq]
    return np.sort(p[:nb]), np.sort(p[nb:])


def clumped(n_rows, need, bb, rng):
    nb = int(np.ceil(need / bb)) + 8
    st = rng.choice(max(1, n_rows - bb), size=nb, replace=False)
    idx = np.unique((st[:, None] + np.arange(bb)[None, :]).ravel())
    while len(idx) < need:
        idx = np.unique(np.concatenate(
            [idx, rng.choice(n_rows, need - len(idx) + 64, replace=False)]))
    return np.sort(rng.permutation(idx)[:need])


def id_twonn(d):
    r1, r2 = d[:, 0], d[:, 1]
    m = r1 > 0
    mu = r2[m] / np.maximum(r1[m], 1e-12)
    mu = mu[mu > 1.0]
    if len(mu) < 100:
        return float("nan")
    mu = mu[mu <= np.quantile(mu, 0.9)]
    return float(len(mu) / np.sum(np.log(mu)))


def subspace_panel(x, bi, nnn):
    """R39's discriminators: mean principal angle between the 36-dim local
    subspaces of distinct neighbourhoods, local eff_rank, top-36 variance.
    Real: 68.1 deg, 168.4, 0.496. The old family: 80.3, 175.9, 0.530."""
    sel = np.random.default_rng(5).choice(nnn.shape[0], 24, replace=False)
    subs, leff, t36 = [], [], []
    for i in sel:
        P = x[torch.from_numpy(bi[nnn[i]]).to(DEV)]
        P = P - P.mean(0, keepdim=True)
        S = torch.linalg.svdvals(P)
        lam = (S ** 2)
        lam = lam / lam.sum()
        leff.append(float(1.0 / (lam ** 2).sum()))
        t36.append(float(lam[:36].sum()))
        _, _, Vh = torch.linalg.svd(P, full_matrices=False)
        subs.append(Vh[:36])
    angs = []
    for a2 in range(0, 22, 2):
        sv = torch.linalg.svdvals(subs[a2] @ subs[a2 + 1].T).clamp(-1, 1)
        angs.append(float(torch.rad2deg(torch.arccos(sv)).mean()))
    return (float(np.median(angs)), float(np.median(leff)),
            float(np.median(t36)))


def spectrum_t(base_t):
    xc = base_t - base_t.mean(0, keepdim=True)
    lam = torch.linalg.svdvals(xc) ** 2 / max(xc.shape[0] - 1, 1)
    lam = lam[lam > 0].double()
    frac = torch.cumsum(lam, 0) / lam.sum()
    eff = float(lam.sum() ** 2 / (lam ** 2).sum())
    d90 = int(torch.searchsorted(
        frac, torch.tensor(0.90, dtype=frac.dtype, device=frac.device)).item() + 1)
    return eff, d90


ARMS = [dict(), dict(rho=0.3), dict(rho=0.6), dict(rho=0.9),
        dict(log2_pool=10), dict(log2_pool=9), dict(log2_pool=8),
        dict(rho=0.6, log2_pool=10)]
_i = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
mine = [ARMS[_i]] if _i < len(ARMS) else []
out = {}
for arm in mine:
    t0 = time.time()
    x, a_of = build(**arm)

    # gates protocol with k=500 so the subspace panel mirrors R39
    bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
    d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)],
                  x[torch.from_numpy(qi).to(DEV)], 500)
    dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
    del d, nn
    g1 = id_twonn(dn)
    cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
    g6 = float(((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12))
    bt = x[torch.from_numpy(bi).to(DEV)]
    rr = torch.randperm(bt.shape[0], device=DEV)[:4096]
    mean_d = float((2.0 - 2.0 * (x[torch.from_numpy(qi[:512]).to(DEV)]
                                 @ bt[rr].T)).clamp_min(0).sqrt().mean())
    g5 = mean_d / float(np.median(dn[:, 9]))
    angle, leff, t36 = subspace_panel(x, bi, nnn)
    g3, g4 = spectrum_t(bt[:50000])
    del bt

    # clumped-protocol s(k)
    rng = np.random.default_rng(20_100)
    b2, q2 = exch(clumped(POOL, NEED, 100, rng), N_FIX, NQ)
    d2, _ = knn_t(x[torch.from_numpy(b2).to(DEV)],
                  x[torch.from_numpy(q2).to(DEV)], 500)
    dm = d2.cpu().numpy()
    del d2
    r = np.array([float(np.median(dm[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    rms = float(np.sqrt(np.mean((s - REAL_S) ** 2)))

    # §3b spans
    sp = {}
    for P in (50000, 600000):
        rg = np.random.default_rng(700 + P // 1000)
        b3, q3 = exch(rg.choice(P, NEED, replace=False), N_FIX, NQ)
        d3, _ = knn_t(x[torch.from_numpy(b3).to(DEV)],
                      x[torch.from_numpy(q3).to(DEV)], 500)
        d3n = d3.cpu().numpy()
        r3 = np.array([float(np.median(d3n[:, k - 1])) for k in KG])
        s3 = np.gradient(np.log(np.array(KG, float)), np.log(r3))
        sp[P] = (float(s3[-1] / max(s3[0], 1e-9)), id_twonn(d3n))
        del d3
    rspan = sp[50000][0] - sp[600000][0]
    gspan = float(np.log(sp[50000][1] / sp[600000][1]))
    del x

    key = json.dumps(arm, sort_keys=True) if arm else "champion"
    out[key] = {"angle": angle, "local_eff": leff, "top36": t36,
                "g3_eff_rank": g3, "g4_dims90": g4,
                "g1": g1, "g5": g5, "g6": g6, "rms": rms,
                "s53": float(s[8]), "s500": float(s[15]), "s14": float(s[4]),
                "ratio_span": rspan, "logg1_span": gspan,
                "s": [float(v) for v in s]}
    ib_r = "IN " if 2.227 <= rspan <= 2.567 else "   "
    ib_g = "IN " if -0.602 <= gspan <= -0.386 else "   "
    print("%-28s | ang %5.1f locEff %6.1f t36 %.3f | g3 %6.1f g4 %4d | "
          "s53 %5.1f s500 %5.1f | r %+6.3f %s g %+6.3f %s| g1 %5.2f g5 %5.3f "
          "g6 %5.3f  (%.0fs)"
          % (key, angle, leff, t36, g3, g4, s[8], s[15], rspan, ib_r,
             gspan, ib_g, g1, g5, g6, time.time() - t0), flush=True)
    print("RESULT_JSON " + json.dumps(out), flush=True)

print("real                         | ang  68.1 locEff  168.4 t36 0.496 | "
      "g3  182.3 g4  359 | s53  28.9 s500  35.7 | r +2.397 IN  g -0.494 IN | "
      "g1 17.23 g5 1.369 g6 1.696")
print("PHASEC_DONE", flush=True)
