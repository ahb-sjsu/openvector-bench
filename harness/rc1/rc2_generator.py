"""R67 on Atlas: the frozen generator's ONE evaluation (RC2_FREEZE.md §2).

Generates the frozen corpus (segment_corpus, frozen defaults, seed 1009,
600k x 1024) with the actual package code across 12 workers — legal because
the generator is random-access; bit-identity with a direct emission is
asserted on a probe range — then runs the full registered panel on GPU 1,
identical to the held-out real-side protocol (rc2_real.py).
"""

import hashlib
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
for src, dst in (("segment_gen.py", "segment_gen.py"),
                 ("hashrng_pkg.py", "hashrng.py"),
                 ("geometry.py", "geometry.py"),
                 ("hubness.py", "hubness.py")):
    shutil.copy(BASEDIR + "/" + src, PKG + "/" + dst)
open(PKG + "/__init__.py", "w").close()
sys.path.insert(0, BASEDIR + "/ovbpkg")

from openvector_bench.segment_gen import (SEGMENT_PARAMS, _articles,
                                          segment_corpus)

DIM, POOL, SEED = 1024, 600000, 1009
P = {k: d for k, _, _, d in SEGMENT_PARAMS}
OUT = BASEDIR + "/rc2_generator.json"
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})


def _chunk(a):
    return segment_corpus(P, 0, DIM, SEED,
                          rows=np.arange(a, min(a + 50000, POOL),
                                         dtype=np.int64))


def temps():
    try:
        s = subprocess.check_output(["sensors"]).decode()
        return max(float(l.split("+")[1].split("\xb0")[0])
                   for l in s.splitlines() if "Package id" in l)
    except Exception:
        return 0.0


t0 = time.time()
# frozen-identity check first: the 6k reference hash must reproduce
ref = segment_corpus(P, 6000, DIM, SEED)
h = hashlib.sha256(ref.tobytes()).hexdigest()
assert h == ("80d94f61cdc304d886ed97cc55805b966ac31ec8f529ea41977f7174"
             "065c5f57"), "frozen hash mismatch: " + h
print("frozen corpus_6k hash verified: %s" % h[:16], flush=True)

with get_context("fork").Pool(8) as pl:
    parts = pl.map(_chunk, list(range(0, POOL, 50000)))
xn = np.concatenate(parts)
probe = np.arange(150000, 150100, dtype=np.int64)
assert np.array_equal(segment_corpus(P, 0, DIM, SEED, rows=probe),
                      xn[150000:150100]), "parallel emission mismatch"
print("corpus %dx%d in %.0fs, cpu pkg %.0fC"
      % (xn.shape[0], DIM, time.time() - t0, temps()), flush=True)
a_of, _, _ = _articles(np.arange(POOL, dtype=np.int64))

import torch  # after generation: keep the fork clean of CUDA

DEV = "cuda"
assert torch.cuda.is_available()
x = torch.from_numpy(xn).to(DEV)
x = x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)  # already unit; exact


def normalize_t(t):
    return t / t.norm(dim=1, keepdim=True).clamp_min(1e-12)


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


rec = {"seed": SEED, "hash6k": h}
t0 = time.time()
bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)],
              x[torch.from_numpy(qi).to(DEV)], 500)
dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
del d, nn
rec["g1"] = id_twonn(dn)
cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
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

vals = {}
for Pn in (50000, 100000, 200000, 400000, 600000):
    rg = np.random.default_rng(700 + Pn // 1000)
    sup = rg.choice(Pn, 35000, replace=False)
    b3, q3 = exch(sup, 25000, 10000, seed=31)
    d3, _ = knn_t(x[torch.from_numpy(b3).to(DEV)],
                  x[torch.from_numpy(q3).to(DEV)], 500)
    d3n = d3.cpu().numpy()
    vals[Pn] = {"ratio": profile_ratio(d3n), "g1": id_twonn(d3n)}
    del d3
rec["s3b"] = {str(k): v for k, v in vals.items()}
rec["rspan"] = vals[50000]["ratio"] - vals[600000]["ratio"]
rec["gspan"] = float(np.log(vals[50000]["g1"] / vals[600000]["g1"]))

rng = np.random.default_rng(20_100)
b2, q2 = exch(clumped(POOL, 35000, 100, rng), 25000, 10000)
d2, n2 = knn_t(x[torch.from_numpy(b2).to(DEV)],
               x[torch.from_numpy(q2).to(DEV)], 500)
dm, nm = d2.cpu().numpy(), n2.cpu().numpy()
del d2, n2
_, s = sk_curve(dm)
rec["s_clumped"] = [float(v) for v in s]
same = a_of[b2[nm]] == a_of[q2][:, None]
din = dm[same]
rec["D_article"] = float(np.percentile(din, 90)
                         / max(np.percentile(din, 10), 1e-9))
rec["overlap"] = float((dm[~same] < np.percentile(din, 90)).mean())

json.dump(rec, open(OUT, "w"), indent=1)
print("FROZEN | g1 %5.2f g3 %5.1f g4 %4d g5 %5.3f g6 %5.3f g8 %5.3f | "
      "trend %+.3f g1exp %+.3f | rspan %+6.3f gspan %+6.3f | s14 %5.1f "
      "s53 %5.1f  (%.0fs)"
      % (rec["g1"], rec["g3"], rec["g4"], rec["g5"], rec["g6"], rec["g8"],
         rec["s3_trend"], rec["s3_g1exp"], rec["rspan"], rec["gspan"],
         s[4], s[8], time.time() - t0), flush=True)
print("RC2_GENERATOR_DONE", flush=True)
