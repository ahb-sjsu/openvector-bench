"""R56: segmented articles -- break the SHARED component, not the variation.

`R55` falsified the breadth reading: `D_article` passed clean through real's
1.72 and `s(14)` fell monotonically, while `overlap` stayed at exactly 0.000 in
every arm.

The failure mode names the fix. Gating a *level* removes a row's variation, so
when all levels are off two rows in one article both collapse onto the article
centre and become **identical** -- `d50_same` reached 0.001. Real needs the
opposite: same-article pairs sitting at the **global** distance, which requires
breaking the *shared* component.

So an article is a sequence of **segments**, each with its own centre. Pairs in
one segment are close; pairs in different segments of the same article are
unrelated by construction, which is what produces `overlap` > 0.

Segmentation is hierarchical so it stays random-access: the segment of row `p`
is `p >> k`, where `k` is the smallest level whose keyed break-bit is set. Block
lengths are then geometric in the break rate, giving the heavy tail `R53`
measured (most runs under ~8 rows, a few far longer) without a scan over
predecessors.
"""

import json
import os
import time

import numpy as np
import torch

from hashgpu import hgauss_t, hidx_t, hunif_t, verify

# batch_probe is NOT imported here. NRP compute nodes restrict egress, so
# `pip install` hangs until the pod is killed -- that is what produced a run
# with no logs at all. The k-NN batch is instead sized by a local doubling
# search with OOM recovery, which is the same idea without a wheel.
probe = None

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
MAXLEV = 8


def normalize_t(x):
    return x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)


def seg_of(a_t, pos_t, brk):
    """Hierarchical, random-access segment id.

    Level j owns the block `pos >> j`. Row p belongs to the block at the
    smallest level whose break-bit fires; if none fires up to MAXLEV the row
    takes the coarsest block. Geometric block lengths -> heavy tail.
    """
    chosen = torch.full_like(pos_t, MAXLEV)
    found = torch.zeros_like(pos_t, dtype=torch.bool)
    for j in range(MAXLEV):
        blk = pos_t >> j
        key = a_t * 1000003 + 104729 * (j + 1) + blk
        bit = hunif_t(key, 1)[..., 0] < brk
        take = bit & (~found)
        chosen = torch.where(take, torch.full_like(chosen, j), chosen)
        found = found | bit
    # segment id: article, level, and the block index at that level
    return a_t * 1000003 + chosen * 7919 + (pos_t >> chosen)


def build(brk=0.35, fil_dim=48, nlev=6, d_loc=64, d_glob=57, w_loc=0.6,
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

    # arrangement: nested clustering over ARTICLES (R49)
    cen = torch.zeros((n_art, DIM), device=DEV)
    lw = np.array([0.72 ** L for L in range(arr_levels)], dtype=np.float32)
    lw /= np.linalg.norm(lw)
    for L in range(arr_levels):
        ncl = max(2, int(round(n_art / (27 * branch ** L))))
        cid = torch.from_numpy(rng.integers(0, ncl, n_art)).to(DEV)
        cc = rng.standard_normal((ncl, d_glob)).astype(np.float32)
        cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
        cen += float(lw[L]) * (torch.from_numpy(cc).to(DEV)[cid] @ bg.T)

    plw = np.sqrt(np.array([0.45 * (0.72 ** i) for i in range(nlev)], dtype=np.float32))
    plw /= np.linalg.norm(plw)
    a_of = np.repeat(np.arange(n_art), (b - starts))[:POOL]
    pos = np.arange(POOL) - starts[a_of]

    x = torch.empty((POOL, DIM), device=DEV)
    CH = 50000
    for st in range(0, POOL, CH):
        en = min(st + CH, POOL)
        a_t = torch.from_numpy(a_of[st:en].astype(np.int64)).to(DEV)
        p_t = torch.from_numpy(pos[st:en]).to(DEV)
        acc = cen[a_t].clone()

        # SEGMENT centre: the shared component that a break removes.
        sid = seg_of(a_t, p_t, brk)
        sdir = hidx_t(sid, d_loc, npool)
        sco = hgauss_t(sid, d_loc)
        sco = sco / sco.norm(dim=1, keepdim=True).clamp_min(1e-12)
        for j in range(d_loc):
            acc += (w_loc * sco[:, j]).unsqueeze(1) * pool[sdir[:, j]]

        # within-segment path, keyed on the SEGMENT so a break resets it too
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


_KNN_BS = [None]


def knn_batch(base, q, k):
    """Size the k-NN batch by binary search with OOM recovery.

    The first NRP pod was OOMKilled because the memory shape was hand-guessed.
    `batch_probe.probe` is the tool for that, and a larger batch also raises GPU
    utilisation -- which is most likely what reaped the R55/R56 pods at ~50 s.
    """
    if _KNN_BS[0] is not None:
        return _KNN_BS[0]
    bs = 1024
    while bs * 2 <= q.shape[0]:
        try:
            sim = q[:bs * 2] @ base.T
            torch.topk(sim, k, dim=1)
            del sim
            if DEV == "cuda":
                torch.cuda.empty_cache()
            bs *= 2
        except torch.cuda.OutOfMemoryError:
            if DEV == "cuda":
                torch.cuda.empty_cache()
            break
    bs = max(1024, int(bs * 0.75))          # headroom
    print("  sized k-NN batch %d (was a hand-guessed 2048)" % bs, flush=True)
    _KNN_BS[0] = bs
    return bs


def knn_t(base, q, k):
    od, oi = [], []
    bs = knn_batch(base, q, k)
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


ARMS = (0.10, 0.15, 0.20, 0.25)
_idx = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
MY_ARMS = (ARMS[_idx],) if _idx < len(ARMS) else ()
print("pod index %d -> brk %s" % (_idx, MY_ARMS), flush=True)
print("brk  | ratio  rms |  g1     g6   | s(4) s(14) s(53) | D_art d50s  OVERLAP",
      flush=True)
out = {}
for brk in MY_ARMS:
    t0 = time.time()
    x, a_of = build(brk=brk)
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
    din, dout = dn[same], dn[~same]
    D = float(np.percentile(din, 90) / max(np.percentile(din, 10), 1e-9))
    ovl = float((dout < np.percentile(din, 90)).mean())
    out["brk%s" % brk] = {"ratio": ratio, "rms": rms, "g1": g1, "g6": g6,
                          "D_article": D,
                          "d50_same": float(np.median(din)),
                          "d50_cross": float(np.median(dout)), "overlap": ovl,
                          "s": [float(v) for v in s]}
    print("%.2f | %5.3f %5.2f | %6.2f %6.3f | %5.1f %5.1f %5.1f | %5.2f %.3f  %.4f   (%.0fs)"
          % (brk, ratio, rms, g1, g6, s[0], s[4], s[8], D, np.median(din),
             ovl, time.time() - t0), flush=True)

    print("RESULT_JSON " + json.dumps(out), flush=True)

print("real | 4.050  0.00 |  17.23  1.696 |  8.8  16.1  28.9 |  1.72 0.884  0.1140")
print("SEG_SWEEP_DONE", flush=True)
