"""RC-3 Phase B (re-aimed per R69): spectrum-tail and density-response sweep.

The rank hypothesis died at Phase A; the robust residue is g4 (+24%), rspan
(4.6 vs <=2.94), g1exp (-0.09 vs <=-0.112), g8 (-0.008). Sixteen arms:

* pool_alpha - NEW lever: power-law amplitude profile over the shared
  direction pool, (1+j)^-alpha normalized to unit mean square. Targets the
  PCA tail (g4) without touching any mechanism.
* seg_break / path_mix / w_loc / d_glob - the density-response levers,
  never measured at the corrected-family operating point.

Harness generator (lognormal cumsum articles, keyed-random clusters,
per-level frames - mirrors the frozen package family; rspan fidelity gap
~0.6 noted in R69, signs transfer). Judged against the R68 ten-block bands.
One arm per pod (NRP indexed job).
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
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})
MAXLEV = 8

# R68 ten-block bands (mean +- 2 sd, n = 10; results/reband10.json)
BANDS = {
    "g1": (14.82, 20.86),
    "g5": (1.348, 1.424),
    "g6": (1.663, 1.840),
    "g3": (151.0, 200.4),
    "g4": (351.2, 363.1),
    "g8": (0.730, 0.743),
    "trend": (0.357, 0.657),
    "g1exp": (-0.228, -0.122),
    "rspan": (0.951, 2.963),
    "gspan": (-0.624, -0.245),
}


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
    brk=0.116,
    branch=64,
    d_glob=24,
    decay=0.50,
    mix=0.6,
    rho=0.3,
    log2_pool=10,
    fil_dim=48,
    nlev=6,
    d_loc=64,
    w_loc=0.6,
    fil_scale=1.0,
    arr_levels=3,
    size_spread=1.2,
    seed=41,
    pool_alpha=0.0,
    pool_floor=0.0,
    chap_size=0,
    w_chap=0.0,
    fine_lo=0.0,
    d_cen=0,
    cen_beta=0.0,
    w_topic=0.0,
    n_topics=4,
    topic_b=0.5,
    topic_m0=64,
    topic_idf=0.35,
    topic_levels=12,
    p_dup=0.0,
    alpha_dup=0.95,
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
    if pool_alpha > 0.0 or pool_floor > 0.0:
        # two-scale profile (RC4 mechanism 1): power-law head over a live
        # plateau - concentrates dims90 without killing eff rank
        w = np.maximum(
            (1.0 + np.arange(npool, dtype=np.float64)) ** (-pool_alpha), pool_floor
        )
        w /= np.sqrt((w**2).mean())
        pool = pool * torch.from_numpy(w.astype(np.float32)).to(DEV).unsqueeze(1)
    cen = torch.zeros((n_art, DIM), device=DEV)
    lw = np.array([0.72**L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    cl0 = None
    for L in range(arr_levels):
        ncl = max(2, int(round(n_art / (27 * branch**L))))
        cid = torch.from_numpy(rng.integers(0, ncl, n_art)).to(DEV)
        if L == 0:
            cl0 = cid.clone()
        cc = rng.standard_normal((ncl, d_glob)).astype(np.float32)
        cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
        bgL = torch.from_numpy(
            np.linalg.qr(rng.standard_normal((DIM, d_glob)))[0].astype(np.float32)
        ).to(DEV)
        cen += float(lw[L]) * (torch.from_numpy(cc).to(DEV)[cid] @ bgL.T)

    if w_chap > 0.0 and chap_size > 0:
        # chapters (RC4 mechanism 2): blocks of consecutive articles share a
        # centre - controlled index-locality above the article
        nch = int(n_art // chap_size) + 1
        chid = torch.from_numpy(np.arange(n_art) // chap_size).to(DEV)
        chf = torch.from_numpy(
            np.linalg.qr(rng.standard_normal((DIM, d_glob)))[0].astype(np.float32)
        ).to(DEV)
        chc = rng.standard_normal((nch, d_glob)).astype(np.float32)
        chc /= np.maximum(np.linalg.norm(chc, axis=1, keepdims=True), 1e-12)
        cen = cen + float(w_chap) * (torch.from_numpy(chc).to(DEV)[chid] @ chf.T)

    cen_frame = None
    if d_cen > 0:
        # RC5: segment centres live in a dedicated low-dim subspace; the
        # global spectrum concentrates while fine components stay full-spread
        cen_frame = torch.from_numpy(
            np.linalg.qr(rng.standard_normal((DIM, d_cen)))[0].astype(np.float32)
        ).to(DEV)
        if cen_beta > 0.0:
            # decaying spectrum WITHIN the centre subspace (RC5 Phase B):
            # the flat frame raised dims90; real bulk spectra decay
            cw = (1.0 + np.arange(d_cen, dtype=np.float64)) ** (-cen_beta)
            cen_frame = cen_frame * torch.from_numpy(
                (cw / np.sqrt((cw**2).mean())).astype(np.float32)
            ).to(DEV)

    plw = np.sqrt(np.array([decay**i for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]
    x = torch.empty((POOL, DIM), device=DEV)
    wp = float(np.sqrt(mix))
    wb = float(np.sqrt(max(0.0, 1.0 - mix)))

    lo_slot = int(fine_lo * npool)
    nfine = max(1, npool - lo_slot)

    def share(priv, cl_row, comp_salt, gate_keys, count, fine=False):
        # fine=True draws stay in the weak tail slots (RC4: pool partition -
        # neighbour-carrying components never touch the strong head, so
        # concentration shapes the spectrum without creating hubs)
        if rho <= 0.0:
            return priv
        mod, off = (nfine, lo_slot) if fine else (npool, 0)
        sh = hidx_t(cl_row * 131 + comp_salt, count, mod) + off
        gt = hunif_t(gate_keys, count) < rho
        return torch.where(gt, sh, priv)

    def hidx_fine(key, count):
        return hidx_t(key, count, nfine) + lo_slot

    for st in range(0, POOL, 50000):
        en = min(st + 50000, POOL)
        a_t = torch.from_numpy(a_of[st:en].astype(np.int64)).to(DEV)
        p_t = torch.from_numpy(pos[st:en]).to(DEV)
        cl_row = cl0[a_t].long()
        acc = cen[a_t].clone()
        sid = seg_of(a_t, p_t, brk)
        if cen_frame is not None:
            sco = hgauss_t(sid * 17 + 3, d_cen)
            sco = sco / sco.norm(dim=1, keepdim=True).clamp_min(1e-12)
            acc += w_loc * (sco @ cen_frame.T)
        else:
            sdir = share(hidx_t(sid, d_loc, npool), cl_row, 17, a_t * 271 + 19, d_loc)
            sco = hgauss_t(sid, d_loc)
            sco = sco / sco.norm(dim=1, keepdim=True).clamp_min(1e-12)
            for j in range(d_loc):
                acc += (w_loc * sco[:, j]).unsqueeze(1) * pool[sdir[:, j]]
        for L in range(nlev):
            key = sid * 31 + L * 7919 + (p_t >> L)
            c = hgauss_t(key, fil_dim)
            dd = share(
                hidx_fine(key, fil_dim),
                cl_row,
                L * 7 + 23,
                a_t * 271 + L * 11 + 29,
                fil_dim,
                fine=True,
            )
            amp = float(fil_scale * wp * plw[L] / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (amp * c[:, j]).unsqueeze(1) * pool[dd[:, j]]
            del c, dd
        if wb > 0.0:
            bdir = share(
                hidx_fine(sid * 100003 + 7, fil_dim),
                cl_row,
                97,
                a_t * 271 + 41,
                fil_dim,
                fine=True,
            )
            bco = hgauss_t(sid * 1009 + (p_t + 1) * 500009 + 11, fil_dim)
            bamp = float(fil_scale * wb / np.sqrt(fil_dim))
            for j in range(fil_dim):
                acc += (bamp * bco[:, j]).unsqueeze(1) * pool[bdir[:, j]]
            del bdir, bco
        if w_topic > 0.0:
            # RC6: Zipf-ladder topics. Slot level L ~ 2^-(L+1); topic id
            # uniform in M0*2^(b*L); unit direction keyed on (L, tid);
            # IDF-weighted coefficient per segment. Sharing per topic falls
            # from thousands (L=0 themes) to ~5 (the bond regime).
            for j in range(n_topics):
                u = hunif_t(sid * 1009 + j * 263 + 11, 1)[..., 0]
                Lv = torch.clamp(
                    torch.floor(-torch.log2(u.clamp_min(1e-9))),
                    0.0,
                    float(topic_levels - 1),
                ).long()
                gkey = torch.zeros_like(sid)
                for L in range(topic_levels):
                    msk = Lv == L
                    if not bool(msk.any()):
                        continue
                    ML = max(2, int(round(topic_m0 * (2.0 ** (topic_b * L)))))
                    tid = hidx_t(sid[msk] * 31 + j * 7 + 3 + L * 104729, 1, ML)[..., 0]
                    gkey[msk] = tid * 131 + L * 15485863
                c = hgauss_t(sid * 17 + j * 29 + 5, 1)[..., 0]
                amp = (
                    w_topic * (1.0 + topic_idf * Lv.float()) / float(np.sqrt(n_topics))
                )
                u_t, t_inv = torch.unique(gkey, return_inverse=True)
                tdir = hgauss_t(u_t * 65537 + 13, DIM)
                tdir = tdir / tdir.norm(dim=1, keepdim=True).clamp_min(1e-12)
                acc += (amp * c).unsqueeze(1) * tdir[t_inv]
                del tdir, u_t, t_inv
        x[st:en] = acc
        del acc
    del cen
    if p_dup > 0.0:
        # RC6 Phase B: keyed near-duplicate ladder. A gated row becomes a
        # near-copy of a keyed source row elsewhere in the corpus - the
        # low-dimensional resolved-at-density structure additive topics
        # could not supply (R81: additive bonds RAISE the TwoNN reading).
        # Depth-1 recursion; random access preserved in the package port.
        xb = normalize_t(x)
        rk = torch.arange(POOL, device=DEV, dtype=torch.int64)
        gate = hunif_t(rk * 2654435761 + 17, 1)[..., 0] < p_dup
        src = hidx_t(rk * 97 + 29, 1, POOL)[..., 0]
        a = float(alpha_dup)
        x = xb.clone()
        x[gate] = a * xb[src[gate]] + float(np.sqrt(max(0.0, 1 - a * a))) * xb[gate]
        del xb
    return normalize_t(x), a_of


def knn_t(base, q, k, bs=4096):
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


def id_twonn(d):
    r1, r2 = d[:, 0], d[:, 1]
    m = r1 > 0
    mu = r2[m] / np.maximum(r1[m], 1e-12)
    mu = mu[mu > 1.0]
    if len(mu) < 100:
        return float("nan")
    mu = mu[mu <= np.quantile(mu, 0.9)]
    return float(len(mu) / np.sum(np.log(mu)))


def sk_curve(dn):
    r = np.array([float(np.median(dn[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    return r, s


def profile_ratio(dn):
    _, s = sk_curve(dn)
    return float(s[-1] / max(s[0], 1e-9))


def eff_rank_t(v):
    xc = v - v.mean(0, keepdim=True)
    lam = torch.linalg.svdvals(xc) ** 2
    lam = lam[lam > 0].double()
    return float(lam.sum() ** 2 / (lam**2).sum())


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


def g8_pca(x, bi, qi, nnn10):
    bt = x[torch.from_numpy(bi).to(DEV)]
    qt = x[torch.from_numpy(qi).to(DEV)]
    mu = bt.mean(0, keepdim=True)
    rng = np.random.default_rng(2)
    sel = rng.choice(len(bi), min(20000, len(bi)), replace=False)
    fit = bt[torch.from_numpy(sel).to(DEV)] - mu
    _, _, Vh = torch.linalg.svd(fit, full_matrices=False)
    p = Vh[:256].T
    bp = normalize_t((bt - mu) @ p)
    qp = normalize_t((qt - mu) @ p)
    _, idxp = knn_t(bp, qp, 10)
    idxp = idxp.cpu().numpy()
    jac = [len(set(a) & set(b)) / len(set(a) | set(b)) for a, b in zip(nnn10, idxp)]
    del bt, qt, bp, qp
    return float(np.mean(jac))


def rank_anatomy(x):
    bi, qi = exch(np.arange(35000), 25000, 10000, seed=31)
    bt = x[torch.from_numpy(bi).to(DEV)]
    qsel = qi[np.random.default_rng(5).choice(len(qi), 256, replace=False)]
    qt = x[torch.from_numpy(np.sort(qsel)).to(DEV)]
    _, nn = knn_t(bt, qt, 100)
    locs = [eff_rank_t(bt[nn[i]]) for i in range(qt.shape[0])]
    glob = eff_rank_t(bt)
    del bt, qt
    return float(np.mean(locs)), glob


def kmeans_t(bt, k, iters, seed):
    rng = np.random.default_rng(seed)
    cent = bt[
        torch.from_numpy(rng.choice(bt.shape[0], k, replace=False)).to(DEV)
    ].clone()
    assign = None
    for _ in range(iters):
        sims = []
        for s in range(0, bt.shape[0], 65536):
            sims.append((bt[s : s + 65536] @ cent.T).argmax(1))
        assign = torch.cat(sims)
        cent.zero_()
        cent.index_add_(0, assign, bt)
        cnt = torch.bincount(assign, minlength=k).clamp_min(1)
        cent = cent / cnt.unsqueeze(1)
        cent = cent / cent.norm(dim=1, keepdim=True).clamp_min(1e-12)
    return cent, assign


def ann_panel(x, a_of):
    """R80 protocol: K=1024 IVF-flat over the 590k base, 10k queries."""
    bi, qi = exch(np.arange(POOL), POOL - 10000, 10000, seed=31)
    bt = x[torch.from_numpy(bi).to(DEV)]
    qt = x[torch.from_numpy(qi).to(DEV)]
    _, gt = knn_t(bt, qt, 10, bs=2048)
    a_t = torch.from_numpy(np.asarray(a_of, dtype=np.int64)).to(DEV)
    same_art = float(
        (
            a_t[torch.from_numpy(bi).to(DEV)][gt]
            == a_t[torch.from_numpy(qi).to(DEV)].unsqueeze(1)
        )
        .float()
        .mean()
    )
    cent, assign = kmeans_t(bt, 1024, 20, 7)
    cnt = torch.bincount(assign, minlength=1024).float()
    occ_cv = float(cnt.std() / cnt.mean())
    probe_rank = (qt @ cent.T).argsort(dim=1, descending=True)
    cell_rank = torch.empty_like(probe_rank)
    cell_rank.scatter_(
        1, probe_rank, torch.arange(1024, device=DEV).expand_as(probe_rank)
    )
    gt_rank = torch.gather(cell_rank, 1, assign[gt])
    rp1 = float((gt_rank < 1).float().mean())
    np95 = 1024
    for npb in range(1, 1025):
        if float((gt_rank < npb).float().mean()) >= 0.95:
            np95 = npb
            break
    del bt, qt, cent, gt, probe_rank, cell_rank
    torch.cuda.empty_cache()
    return {"np95": np95, "rp1": rp1, "occ_cv": occ_cv, "same_art": same_art}


BASE = dict(pool_alpha=0.22, brk=0.126)  # the frozen RC-3 D12 point
# RC6 Phase D (final envelope sweep): MANY WEAK topics. R83 showed the
# boosted-rare-direction form of scatter destroys geometry; real's
# cross-article closeness is ambient - many small shared features. K
# large, per-topic amplitude small, mild/no idf, denser mid universes
# (m0 32, b 0.3), slightly weakened segment dominance. Panel adds
# same-article fraction of top-10 (real ~0.66; family ~0.9).
VARIANTS = {
    "D0_d12": dict(),
    "D1_k16": dict(
        w_topic=0.40,
        n_topics=16,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.85,
    ),
    "D2_k32": dict(
        w_topic=0.40,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.85,
    ),
    "D3_k32wt55": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
    ),
    "D4_k16idf3": dict(
        w_topic=0.40,
        n_topics=16,
        topic_idf=0.3,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.85,
    ),
    "D5_k32wl50": dict(
        w_topic=0.40,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.85,
        w_loc=0.50,
    ),
    "D6_k32wt55wl50": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
        w_loc=0.50,
    ),
    "D7_k32wt65wl45": dict(
        w_topic=0.65,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.70,
        w_loc=0.45,
    ),
    "D8_k32p06": dict(
        w_topic=0.40,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.85,
        p_dup=0.06,
    ),
    "D9_k32wt55p06": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
        p_dup=0.06,
    ),
    "D10_k32wt55wl50p06": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
        w_loc=0.50,
        p_dup=0.06,
    ),
    "D11_k32b05": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.5,
        fil_scale=0.75,
    ),
    "D12_k64wt55": dict(
        w_topic=0.55,
        n_topics=64,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
    ),
    "D13_k32wt55b135": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
        brk=0.135,
    ),
    "D14_k32wt55s137": dict(
        w_topic=0.55,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.75,
        seed=137,
    ),
    "D15_k32wt65wl45p06": dict(
        w_topic=0.65,
        n_topics=32,
        topic_idf=0.0,
        topic_m0=32,
        topic_b=0.3,
        fil_scale=0.70,
        w_loc=0.45,
        p_dup=0.06,
    ),
}
ARMS = list(VARIANTS)
_i = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
mine = [ARMS[_i]] if _i < len(ARMS) else []
for name in mine:
    t0 = time.time()
    kw = {**BASE, **VARIANTS[name]}
    kw.setdefault("seed", 41)
    x, a_of = build(**kw)
    rec = {}
    bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
    d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)], x[torch.from_numpy(qi).to(DEV)], 500)
    dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
    del d, nn
    rec["g1"] = id_twonn(dn)
    cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
    rec["g6"] = float(((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12))
    bt = x[torch.from_numpy(bi).to(DEV)]
    rr = torch.randperm(bt.shape[0], device=DEV)[:4096]
    mean_d = float(
        (2.0 - 2.0 * (x[torch.from_numpy(qi[:512]).to(DEV)] @ bt[rr].T))
        .clamp_min(0)
        .sqrt()
        .mean()
    )
    rec["g5"] = mean_d / float(np.median(dn[:, 9]))
    rec["g3"], rec["g4"] = spectrum_t(bt[:50000])
    del bt
    rec["g8"] = g8_pca(x, bi, qi, nnn[:, :10])
    b6, q6 = exch(np.arange(POOL), POOL - 10000, 10000, seed=61)
    ratios, g1s = [], []
    for n_r in (25000, 50000, 100000, 200000):
        rr2 = np.random.default_rng(10000 + n_r)
        sub = b6[rr2.choice(len(b6), n_r, replace=False)]
        d5, _ = knn_t(
            x[torch.from_numpy(np.sort(sub)).to(DEV)],
            x[torch.from_numpy(q6).to(DEV)],
            500,
        )
        d5n = d5.cpu().numpy()
        ratios.append(profile_ratio(d5n))
        g1s.append(id_twonn(d5n))
        del d5
    ln_n = np.log([25000, 50000, 100000, 200000])
    rec["s3_trend"] = float(np.polyfit(ln_n, ratios, 1)[0])
    rec["s3_g1exp"] = float(np.polyfit(ln_n, np.log(g1s), 1)[0])
    vals = {}
    for Pn in (50000, 600000):
        rg = np.random.default_rng(700 + Pn // 1000)
        sup = rg.choice(Pn, 35000, replace=False)
        b3, q3 = exch(sup, 25000, 10000, seed=31)
        d3, _ = knn_t(
            x[torch.from_numpy(b3).to(DEV)], x[torch.from_numpy(q3).to(DEV)], 500
        )
        d3n = d3.cpu().numpy()
        vals[Pn] = {"ratio": profile_ratio(d3n), "g1": id_twonn(d3n)}
        del d3
    rec["r50k"] = vals[50000]["ratio"]
    rec["rspan"] = vals[50000]["ratio"] - vals[600000]["ratio"]
    rec["gspan"] = float(np.log(vals[50000]["g1"] / vals[600000]["g1"]))
    rec["rank_local"], rec["rank_global"] = rank_anatomy(x)
    rec.update(ann_panel(x, a_of))
    fl = []
    for k, v in (
        ("g1", rec["g1"]),
        ("g5", rec["g5"]),
        ("g6", rec["g6"]),
        ("g3", rec["g3"]),
        ("g4", rec["g4"]),
        ("g8", rec["g8"]),
        ("trend", rec["s3_trend"]),
        ("g1exp", rec["s3_g1exp"]),
        ("rspan", rec["rspan"]),
        ("gspan", rec["gspan"]),
    ):
        lo, hi = BANDS[k]
        fl.append(k + ("+" if lo <= v <= hi else "-"))
    print(
        "%s | g1 %5.2f g3 %5.1f g4 %4d g5 %5.3f g6 %5.3f g8 %5.3f | "
        "trend %+.3f g1exp %+.3f | r50k %5.2f rspan %+6.3f gspan %+6.3f | "
        "np95 %4d rp1 %.3f ocv %.2f sa %.2f | %s  (%.0fs)"
        % (
            name,
            rec["g1"],
            rec["g3"],
            rec["g4"],
            rec["g5"],
            rec["g6"],
            rec["g8"],
            rec["s3_trend"],
            rec["s3_g1exp"],
            rec["r50k"],
            rec["rspan"],
            rec["gspan"],
            rec["np95"],
            rec["rp1"],
            rec["occ_cv"],
            rec["same_art"],
            " ".join(fl),
            time.time() - t0,
        ),
        flush=True,
    )
    print("RESULT_JSON " + json.dumps({name: rec}), flush=True)

print("RC6D_DONE", flush=True)
