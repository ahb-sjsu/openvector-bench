"""RC-3 Phase A: baseline error bars for the frozen package family.

Four generation seeds (41, 89, 137, 271; the frozen 1009 panel already
exists in rc2_generator.json) against the ten-block bands, plus the rank
anatomy Phase B's falsifier needs:

* global eff_rank: (sum lam)^2 / sum lam^2 of the covariance of a 25k base
  sample (g3 is the same statistic at 50k; both recorded).
* local eff_rank: for 256 queries, the eff_rank of the covariance of the
  query's 100 nearest base vectors, averaged over queries.

The same anatomy is measured on two already-consumed REAL blocks (3M, 18M)
so the real-side reference (R39/R64 quoted 168/182) is re-established under
this exact implementation rather than compared across codebases.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import get_context

import numpy as np

BASEDIR = "/home/claude/ovb_scale"
PKG = BASEDIR + "/ovbpkg/openvector_bench"
os.makedirs(PKG, exist_ok=True)
for src, dst in (
    ("segment_gen.py", "segment_gen.py"),
    ("hashrng_pkg.py", "hashrng.py"),
    ("geometry.py", "geometry.py"),
    ("hubness.py", "hubness.py"),
):
    shutil.copy(BASEDIR + "/" + src, PKG + "/" + dst)
open(PKG + "/__init__.py", "w").close()
sys.path.insert(0, BASEDIR + "/ovbpkg")

from openvector_bench.segment_gen import SEGMENT_PARAMS, segment_corpus  # noqa: E402

DIM, POOL = 1024, 600000
P = {k: d for k, _, _, d in SEGMENT_PARAMS}
P["p_dup"] = 0.0
P["p_echo"] = 0.12
P["echo_k"] = 3
P["echo_win"] = 100000
P["echo_alpha"] = 0.96
P["pool_alpha"] = 0.26
P["alpha_dup"] = 0.95
OUT = BASEDIR + "/r97_p2.json"
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})
SEEDS = (41, 89, 137, 271)
REAL_PARTS = "/archive/tqp_real/wiki1024/part_%03d.npy"
REAL_ANATOMY_OFFSETS = (3_000_000, 18_000_000)

_GENSEED = {"v": None}


def _chunk(a):
    return segment_corpus(
        P,
        0,
        DIM,
        _GENSEED["v"],
        rows=np.arange(a, min(a + 50000, POOL), dtype=np.int64),
    )


def temps():
    try:
        s = subprocess.check_output(["sensors"]).decode()
        return max(
            float(ln.split("+")[1].split("\xb0")[0])
            for ln in s.splitlines()
            if "Package id" in ln
        )
    except Exception:
        return 0.0


def guard():
    while temps() > 80.0:
        print("thermal pause: cpu %.0f" % temps(), flush=True)
        time.sleep(30)


import torch  # noqa: E402

DEV = "cuda"
assert torch.cuda.is_available()


def normalize_t(t):
    return t / t.norm(dim=1, keepdim=True).clamp_min(1e-12)


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
    """local/global eff_rank on a 25k base with 256 probe queries, k=100."""
    bi, qi = exch(np.arange(35000), 25000, 10000, seed=31)
    bt = x[torch.from_numpy(bi).to(DEV)]
    qsel = qi[np.random.default_rng(5).choice(len(qi), 256, replace=False)]
    qt = x[torch.from_numpy(np.sort(qsel)).to(DEV)]
    _, nn = knn_t(bt, qt, 100)
    locs = [eff_rank_t(bt[nn[i]]) for i in range(qt.shape[0])]
    glob = eff_rank_t(bt)
    del bt, qt
    return float(np.mean(locs)), glob


def full_panel(x):
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
    rec["s3_rung_ratios"] = ratios
    rec["s3_rung_g1"] = g1s
    rec["s3_trend"] = float(np.polyfit(ln_n, ratios, 1)[0])
    rec["s3_g1exp"] = float(np.polyfit(ln_n, np.log(g1s), 1)[0])
    vals = {}
    for Pn in (50000, 100000, 200000, 400000, 600000):
        rg = np.random.default_rng(700 + Pn // 1000)
        sup = rg.choice(Pn, 35000, replace=False)
        b3, q3 = exch(sup, 25000, 10000, seed=31)
        d3, _ = knn_t(
            x[torch.from_numpy(b3).to(DEV)], x[torch.from_numpy(q3).to(DEV)], 500
        )
        d3n = d3.cpu().numpy()
        vals[Pn] = {"ratio": profile_ratio(d3n), "g1": id_twonn(d3n)}
        del d3
    rec["s3b"] = {str(k): v for k, v in vals.items()}
    rec["rspan"] = vals[50000]["ratio"] - vals[600000]["ratio"]
    rec["gspan"] = float(np.log(vals[50000]["g1"] / vals[600000]["g1"]))
    rec["rank_local"], rec["rank_global"] = rank_anatomy(x)
    return rec


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
        cent = normalize_t(cent)
    return cent, assign


def ann_panel(x):
    bi, qi = exch(np.arange(POOL), POOL - 10000, 10000, seed=31)
    bt = x[torch.from_numpy(bi).to(DEV)]
    qt = x[torch.from_numpy(qi).to(DEV)]
    _, gt = knn_t(bt, qt, 10, bs=2048)
    cent, assign = kmeans_t(bt, 1024, 20, 7)
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
    return {"np95": np95, "rp1": rp1}


out = {}
for sd in SEEDS:
    guard()
    t0 = time.time()
    _GENSEED["v"] = sd
    with get_context("fork").Pool(8) as pl:
        parts = pl.map(_chunk, list(range(0, POOL, 50000)))
    xn = np.concatenate(parts)
    x = torch.from_numpy(xn).to(DEV)
    del parts, xn
    rec = full_panel(x)
    rec.update(ann_panel(x))
    out["seed_%d" % sd] = rec
    print(
        "seed %4d | g1 %5.2f g3 %5.1f g4 %4d g5 %5.3f g6 %5.3f g8 %5.3f | "
        "trend %+.3f g1exp %+.3f | rspan %+6.3f gspan %+6.3f | "
        "rank %5.1f/%5.1f np95 %4d  (%.0fs)"
        % (
            sd,
            rec["g1"],
            rec["g3"],
            rec["g4"],
            rec["g5"],
            rec["g6"],
            rec["g8"],
            rec["s3_trend"],
            rec["s3_g1exp"],
            rec["rspan"],
            rec["gspan"],
            rec["rank_local"],
            rec["rank_global"],
            rec["np95"],
            time.time() - t0,
        ),
        flush=True,
    )
    del x
    torch.cuda.empty_cache()
    json.dump(out, open(OUT, "w"), indent=1)

for off in ():
    part, rem = divmod(off, 1_000_000)
    a = np.load(REAL_PARTS % part, mmap_mode="r")
    xr = torch.from_numpy(np.asarray(a[rem : rem + POOL], dtype=np.float32)).to(DEV)
    xr = normalize_t(xr)
    lo, gl = rank_anatomy(xr)
    out["real_%d" % off] = {"rank_local": lo, "rank_global": gl}
    print("real %8d | rank %5.1f/%5.1f" % (off, lo, gl), flush=True)
    del xr
    torch.cuda.empty_cache()

json.dump(out, open(OUT, "w"), indent=1)
print("R97_P2_DONE", flush=True)
