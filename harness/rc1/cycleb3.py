"""RC1_PLAN Phase D: the full audit, at OP-1 and OP-2, with generation-seed
error bars. The gate to RC-2.

First exposure of this family to three registered criteria it has never faced:

  * the §3 four-rung ladder (trend, G1 exponent, per-rung ratios; PROFILE.md §3)
  * the FULL §3b five-pool ladder — absolute per-density ratio AND G1 values
    within ±2 sd, not just the two summary spans (PROFILE.md §3b)
  * g8 pca_retention (PREREG_RC1), mirroring geometry.pca_retention exactly
    (PCA_DIM 256, rng(2) fit subset, k=10 Jaccard)

Protocol seeds are FIXED; the generation seed varies (41, 137, 271) so the
error bars isolate generation variance. Measurement is split into two pod
halves per (OP, seed) to keep pods short and GPU-dense (the R57 profile):
  half A: gates incl g8 + spectrum + §3 ladder
  half B: §3b five-pool ladder + clumped s(k) + anatomy

Operating points (Phase C hand-off, R64):
  OP1 spans-first: lp13, rho 0.3, brk 0.125, wl 0.6, dg 24, decay 0.50, mix 0.6
  OP2 gates-first: lp10, rho 0.3, brk 0.116, otherwise identical

Known deferral: the s(k) curve targets are still single-block (`R33`);
re-banding on corpus blocks 2-4 awaits Atlas headroom and is required before
any freeze. The registered §3/§3b bands used here are four-block (R24/R29).

No adjudication is pre-empted here: every value prints with its band and an
IN/out flag, and the verdict belongs to the round document.
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
REAL_S = np.array([8.82, 9.43, 11.46, 14.02, 16.08, 20.11, 23.40, 26.01,
                   28.88, 29.98, 31.29, 33.19, 34.02, 34.82, 35.53, 35.73])
MAXLEV = 8

# Registered bands (all +-2 sd, four-block variance: R24 for §3, R29 for §3b).
S3_BANDS = {"trend": (0.2536, 0.6488), "g1exp": (-0.227, -0.112),
            "rung_ratio": {25000: (1.175, 1.571), 50000: (1.504, 1.728),
                           100000: (1.749, 2.097), 200000: (2.067, 2.559)}}
S3B_BANDS = {50000: {"ratio": (3.574, 3.870), "g1": (15.11, 17.43)},
             100000: {"ratio": (2.294, 2.870), "g1": (16.30, 17.86)},
             200000: {"ratio": (1.638, 1.910), "g1": (18.80, 20.24)},
             400000: {"ratio": (1.428, 1.500), "g1": (23.14, 24.10)},
             600000: {"ratio": (1.273, 1.377), "g1": (25.54, 27.78)},
             "rspan": (2.227, 2.567), "gspan": (-0.602, -0.386)}


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


def build(brk=0.125, branch=64, d_glob=24, decay=0.50, mix=0.6, rho=0.3,
          log2_pool=13, fil_dim=48, nlev=6, d_loc=64, w_loc=0.6,
          fil_scale=1.0, arr_levels=3, size_spread=1.2, seed=41,
          arr_frames="single", arr_decay=0.72, arr_radial=0.0):
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
    lw = np.array([arr_decay ** L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    cl0 = None
    for L in range(arr_levels):
        ncl = max(2, int(round(n_art / (27 * branch ** L))))
        cid = torch.from_numpy(rng.integers(0, ncl, n_art)).to(DEV)
        if L == 0:
            cl0 = cid.clone()
        cc = rng.standard_normal((ncl, d_glob)).astype(np.float32)
        cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
        if arr_frames == "per_level":
            # every level in its OWN frame: the single-frame build confines the
            # whole arrangement to one d_glob-dim subspace, a hard ceiling on
            # coarse-scale dimension (R65's coherent failure direction)
            bgL = torch.from_numpy(np.linalg.qr(rng.standard_normal(
                (DIM, d_glob)))[0].astype(np.float32)).to(DEV)
        else:
            bgL = bg
        cen += float(lw[L]) * (torch.from_numpy(cc).to(DEV)[cid] @ bgL.T)
    if arr_radial > 0.0:
        # hyperbolic boundary layer: per-article radial multiplier
        # m = 1 + ln(U)/kappa (clipped), a continuum of coarse radii
        u = hunif_t(torch.arange(n_art, device=DEV, dtype=torch.int64) * 7 + 3,
                    1)[..., 0]
        m = (1.0 + torch.log(u.clamp_min(1e-6)) / arr_radial).clamp_min(0.15)
        cen = cen * m.unsqueeze(1)

    plw = np.sqrt(np.array([decay ** i for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]
    x = torch.empty((POOL, DIM), device=DEV)
    wp = float(np.sqrt(mix))
    wb = float(np.sqrt(max(0.0, 1.0 - mix)))

    def share(priv, cl_row, comp_salt, gate_keys, count):
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


def sk_curve(dn):
    r = np.array([float(np.median(dn[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    return r, s


def profile_ratio(dn):
    _, s = sk_curve(dn)
    return float(s[-1] / max(s[0], 1e-9))


def spectrum_t(base_t):
    xc = base_t - base_t.mean(0, keepdim=True)
    lam = torch.linalg.svdvals(xc) ** 2 / max(xc.shape[0] - 1, 1)
    lam = lam[lam > 0].double()
    frac = torch.cumsum(lam, 0) / lam.sum()
    eff = float(lam.sum() ** 2 / (lam ** 2).sum())
    d90 = int(torch.searchsorted(
        frac, torch.tensor(0.90, dtype=frac.dtype, device=frac.device)).item() + 1)
    return eff, d90


def g8_pca(x, bi, qi, nnn10):
    """geometry.pca_retention, mirrored: PCA_DIM 256, rng(2) 20k fit subset,
    k=10 Jaccard between original-space and projected-space neighbour sets."""
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
    jac = [len(set(a) & set(b)) / len(set(a) | set(b))
           for a, b in zip(nnn10, idxp)]
    del bt, qt, bp, qp
    return float(np.mean(jac))


BASE = dict(log2_pool=10, rho=0.3, arr_frames="per_level", brk=0.116)
# Seed-robustness confirmation of the two mechanism winners. V1's trend sits
# mid-band (+0.423), V2's near the lower edge (+0.277); R65 established that
# edge-adjacent single-seed results do not survive. Three generation seeds
# each; protocol seeds fixed.
VARIANTS = {
    "V1_s41": dict(d_glob=24, seed=41),   "V1_s137": dict(d_glob=24, seed=137),
    "V1_s271": dict(d_glob=24, seed=271), "V2_s41": dict(d_glob=48, seed=41),
    "V2_s137": dict(d_glob=48, seed=137), "V2_s271": dict(d_glob=48, seed=271),
    "V1_s89": dict(d_glob=24, seed=89),   "V2_s89": dict(d_glob=48, seed=89),
}
ARMS = [(name, half) for name in VARIANTS for half in ("A", "B")]
_i = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
mine = [ARMS[_i]] if _i < len(ARMS) else []
out = {}
for name, half in mine:
    t0 = time.time()
    x, a_of = build(**{**BASE, **VARIANTS[name]})
    key = "%s_%s" % (name, half)
    rec = {}

    if half == "A":
        # gates, k=500 so g1 uses the registered protocol depth
        bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
        d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)],
                      x[torch.from_numpy(qi).to(DEV)], 500)
        dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
        del d, nn
        rec["g1"] = id_twonn(dn)
        cnt = np.bincount(nnn[:, :10].ravel(),
                          minlength=len(bi)).astype(np.float64)
        rec["g6"] = float(((cnt - cnt.mean()) ** 3).mean()
                          / max(cnt.std() ** 3, 1e-12))
        bt = x[torch.from_numpy(bi).to(DEV)]
        rr = torch.randperm(bt.shape[0], device=DEV)[:4096]
        mean_d = float((2.0 - 2.0 * (x[torch.from_numpy(qi[:512]).to(DEV)]
                                     @ bt[rr].T)).clamp_min(0).sqrt().mean())
        rec["g5"] = mean_d / float(np.median(dn[:, 9]))
        rec["g3"], rec["g4"] = spectrum_t(bt[:50000])
        del bt
        rec["g8"] = g8_pca(x, bi, qi, nnn[:, :10])
        # §3 four-rung ladder: 600k pool, 10k holdout, uniform rungs
        b6, q6 = exch(np.arange(POOL), POOL - 10000, 10000, seed=61)
        ratios, g1s = [], []
        for n_r in (25000, 50000, 100000, 200000):
            rr2 = np.random.default_rng(10000 + n_r)
            sub = b6[rr2.choice(len(b6), n_r, replace=False)]
            d5, _ = knn_t(x[torch.from_numpy(np.sort(sub)).to(DEV)],
                          x[torch.from_numpy(q6).to(DEV)], 500)
            d5n = d5.cpu().numpy()
            ratios.append(profile_ratio(d5n))
            g1s.append(id_twonn(d5n))
            del d5
        ln_n = np.log([25000, 50000, 100000, 200000])
        rec["s3_rung_ratios"] = ratios
        rec["s3_rung_g1"] = g1s
        rec["s3_trend"] = float(np.polyfit(ln_n, ratios, 1)[0])
        rec["s3_g1exp"] = float(np.polyfit(ln_n, np.log(g1s), 1)[0])
        tb = S3_BANDS
        flags = ["trend " + ("IN" if tb["trend"][0] <= rec["s3_trend"] <= tb["trend"][1] else "out"),
                 "g1exp " + ("IN" if tb["g1exp"][0] <= rec["s3_g1exp"] <= tb["g1exp"][1] else "out")]
        for n_r, rat in zip((25000, 50000, 100000, 200000), ratios):
            lo, hi = tb["rung_ratio"][n_r]
            flags.append("r%dk %s" % (n_r // 1000, "IN" if lo <= rat <= hi else "out"))
        print("%s | g1 %5.2f g3 %5.1f g4 %4d g5 %5.3f g6 %5.3f g8 %5.3f | "
              "S3 trend %+.3f g1exp %+.3f | %s  (%.0fs)"
              % (key, rec["g1"], rec["g3"], rec["g4"], rec["g5"], rec["g6"],
                 rec["g8"], rec["s3_trend"], rec["s3_g1exp"], " ".join(flags),
                 time.time() - t0), flush=True)
    else:
        # §3b five-pool ladder, registered protocol: n=25k fixed, per-pool holdout
        vals = {}
        for P in (50000, 100000, 200000, 400000, 600000):
            rg = np.random.default_rng(700 + P // 1000)
            sup = rg.choice(P, 35000, replace=False)
            b3, q3 = exch(sup, 25000, 10000, seed=31)
            d3, _ = knn_t(x[torch.from_numpy(b3).to(DEV)],
                          x[torch.from_numpy(q3).to(DEV)], 500)
            d3n = d3.cpu().numpy()
            vals[P] = {"ratio": profile_ratio(d3n), "g1": id_twonn(d3n)}
            del d3
        rec["s3b"] = {str(k): v for k, v in vals.items()}
        rec["rspan"] = vals[50000]["ratio"] - vals[600000]["ratio"]
        rec["gspan"] = float(np.log(vals[50000]["g1"] / vals[600000]["g1"]))
        # clumped s(k) + anatomy
        rng = np.random.default_rng(20_100)
        b2, q2 = exch(clumped(POOL, 35000, 100, rng), 25000, 10000)
        d2, n2 = knn_t(x[torch.from_numpy(b2).to(DEV)],
                       x[torch.from_numpy(q2).to(DEV)], 500)
        dm, nm = d2.cpu().numpy(), n2.cpu().numpy()
        del d2, n2
        _, s = sk_curve(dm)
        rec["s"] = [float(v) for v in s]
        rec["rms_singleblock"] = float(np.sqrt(np.mean((s - REAL_S) ** 2)))
        same = a_of[b2[nm]] == a_of[q2][:, None]
        din, dout = dm[same], dm[~same]
        rec["D_article"] = float(np.percentile(din, 90)
                                 / max(np.percentile(din, 10), 1e-9))
        rec["overlap"] = float((dout < np.percentile(din, 90)).mean())
        fl = []
        for P in (50000, 100000, 200000, 400000, 600000):
            rb = S3B_BANDS[P]["ratio"]
            gb = S3B_BANDS[P]["g1"]
            fl.append("%dk r%s g%s" % (P // 1000,
                      "IN" if rb[0] <= vals[P]["ratio"] <= rb[1] else "X",
                      "IN" if gb[0] <= vals[P]["g1"] <= gb[1] else "X"))
        rs = S3B_BANDS["rspan"]
        gs = S3B_BANDS["gspan"]
        fl.append("rspan " + ("IN" if rs[0] <= rec["rspan"] <= rs[1] else "out"))
        fl.append("gspan " + ("IN" if gs[0] <= rec["gspan"] <= gs[1] else "out"))
        print("%s | rspan %+6.3f gspan %+6.3f | %s | s14 %5.1f s53 %5.1f "
              "rms1b %5.2f  (%.0fs)"
              % (key, rec["rspan"], rec["gspan"], " ".join(fl), s[4], s[8],
                 rec["rms_singleblock"], time.time() - t0), flush=True)
    del x
    out[key] = rec
    print("RESULT_JSON " + json.dumps(out), flush=True)

print("PHASED_DONE", flush=True)

