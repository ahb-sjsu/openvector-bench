"""R55: the gated-mixture sweep on an NRP A10.

Moved off Atlas after R54's thermal event. Needs only the generator and
R52/R53's measured constants, not the Wikipedia corpus.

The first pod was killed by NRP after 36 s under the >40% GPU-utilisation rule:
hashing in numpy on the CPU left the GPU idle through the build. The hash is
therefore on the GPU here, and correctness is kept the only honest way -- numpy
remains the reference and `hashgpu.verify` asserts bit-equality at startup,
aborting the run on any mismatch (R48).
"""
import json
import time

import numpy as np
import torch

from hashgpu import hgauss_t, hidx_t, hunif_t, verify

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("device=" + DEV + " " + (torch.cuda.get_device_name(0) if DEV == "cuda" else ""),
      flush=True)
verify(DEV)

DIM, ART_MEAN, POOL = 1024, 23, 600000
N_FIX, NQ = 25000, 10000
NEED = N_FIX + NQ
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})
REAL_S = np.array([8.82, 9.43, 11.46, 14.02, 16.08, 20.11, 23.40, 26.01,
                   28.88, 29.98, 31.29, 33.19, 34.02, 34.82, 35.53, 35.73])


def normalize_t(x):
    return x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)


def build(gate=1.0, fil_dim=48, nlev=6, d_loc=64, d_glob=57, w_loc=0.6,
          fil_scale=1.0, arr_levels=3, branch=8, size_spread=1.2,
          log2_pool=13, seed=41):
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
    for L in range(arr_levels):
        per = 27 * (branch ** L)
        ncl = max(2, int(round(n_art / per)))
        cid = torch.from_numpy(rng.integers(0, ncl, n_art)).to(DEV)
        cc = rng.standard_normal((ncl, d_glob)).astype(np.float32)
        cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
        cen += float(lw[L]) * (torch.from_numpy(cc).to(DEV)[cid] @ bg.T)

    cl = rng.standard_normal((n_art, d_loc)).astype(np.float32)
    cl /= np.maximum(np.linalg.norm(cl, axis=1, keepdims=True), 1e-12)
    clt = torch.from_numpy(cl).to(DEV)
    sd = torch.from_numpy(rng.integers(0, npool, (n_art, d_loc))).to(DEV)
    for j in range(d_loc):
        cen += (w_loc * clt[:, j]).unsqueeze(1) * pool[sd[:, j]]

    plw = np.sqrt(np.array([0.45 * (0.72 ** i) for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]
    maxpos = int((b - starts).max())
    aa_np = a_of
    x = torch.empty((POOL, DIM), device=DEV)
    CH = 50000
    for st in range(0, POOL, CH):
        en = min(st + CH, POOL)
        a_c = aa_np[st:en]
        acc = cen[torch.from_numpy(a_c).to(DEV)].clone()
        for L in range(nlev):
            blk = torch.from_numpy(pos[st:en] >> L).to(DEV)
            a_t = torch.from_numpy(a_c.astype(np.int64)).to(DEV)
            key = a_t * 1000003 + L * 7919 + blk
            c = hgauss_t(key, fil_dim)
            dd = hidx_t(key, fil_dim, npool)
            amp = float(fil_scale * plw[L] / np.sqrt(fil_dim))
            w = amp * (hunif_t(key, 1)[..., 0] < gate).float() if gate < 1.0 else None
            for j in range(fil_dim):
                wj = (w * c[:, j]) if w is not None else (amp * c[:, j])
                acc += wj.unsqueeze(1) * pool[dd[:, j]]
            del c, dd
        x[st:en] = acc
        del acc
    del cen
    return normalize_t(x), a_of


def knn_t(base, q, k):
    out_d, out_i = [], []
    for s in range(0, q.shape[0], 2048):
        sim = q[s:s + 2048] @ base.T
        dv, iv = torch.topk(sim, k, dim=1)
        out_d.append((2.0 - 2.0 * dv).clamp_min(0).sqrt())
        out_i.append(iv)
    return torch.cat(out_d), torch.cat(out_i)


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


print("gate |   g1     g6   | ratio  rms | s(4) s(14) s(53) | D_art d50s  d50x  ovl",
      flush=True)
out = {}
for gate in (1.0, 0.7, 0.5, 0.3, 0.15):
    t0 = time.time()
    x, a_of = build(gate=gate)
    rng = np.random.default_rng(20_100)
    bi, qi = exch(clumped(POOL, NEED, 100, rng), N_FIX, NQ)
    d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)],
                  x[torch.from_numpy(qi).to(DEV)], max(KG))
    dn = d.cpu().numpy()
    nnn = nn.cpu().numpy()
    del x, d, nn
    if DEV == "cuda":
        torch.cuda.empty_cache()

    r = np.array([float(np.median(dn[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    ratio = float(s[-1] / max(s[0], 1e-9))
    rms = float(np.sqrt(np.mean((s - REAL_S) ** 2)))
    mu = dn[:, 1] / np.maximum(dn[:, 0], 1e-12)
    g1 = float(np.log(2.0) / np.mean(np.log(np.maximum(mu, 1.0 + 1e-9))))
    cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
    g6 = float(((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12))
    same = a_of[bi[nnn]] == a_of[qi][:, None]
    din = dn[same]
    dout = dn[~same]
    D = float(np.percentile(din, 90) / max(np.percentile(din, 10), 1e-9))
    ovl = float((dout < np.percentile(din, 90)).mean())
    out["gate%s" % gate] = {"g1": g1, "g6": g6, "ratio": ratio, "rms": rms,
                            "D_article": D, "d50_same": float(np.median(din)),
                            "d50_cross": float(np.median(dout)), "overlap": ovl,
                            "s": [float(v) for v in s]}
    print("%.2f | %6.2f %6.3f | %5.3f %5.2f | %5.1f %5.1f %5.1f | %5.2f %.3f %.3f %.3f   (%.0fs)"
          % (gate, g1, g6, ratio, rms, s[0], s[4], s[8], D,
             np.median(din), np.median(dout), ovl, time.time() - t0), flush=True)

print("real |  17.23  1.696 | 4.050  0.00 |  8.8  16.1  28.9 |  1.72 0.884 1.099 0.114")
print("RESULT_JSON " + json.dumps(out), flush=True)
print("NRP_SWEEP_DONE", flush=True)
