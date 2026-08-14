"""R80: ANN-behaviour characterization - frozen generator vs real, open protocol.

Does the frozen RC-3 generator predict real's ANN index behaviour despite
its two known geometric misses (dims90 +15%, G1-vs-n exponent shallow)?
Identical IVF-flat pipelines per corpus: k-means (K=1024, 20 iters, seed
7) on the 590k base, 10k exchangeable queries, exact GT top-10, then

  * recall@10 vs nprobe in {1,2,4,8,16,32,64} (cell-membership recall -
    exactly IVF-flat recall at that probe depth),
  * expected scan fraction per nprobe (mean probed-cell mass),
  * cell occupancy: CV, skew, max-cell share, top-10-cell share,
  * query margins: median (r2-r1)/r1 and (r10-r1)/r1.

Corpora: real blocks 3M/13M/23M (consumed tuning blocks - the sealed set
is untouched) and the frozen package generator at seeds 2027 and 41.
Runs on Atlas GPU 1. NOT the sealed ANN prediction test: this is an open
characterization to decide whether the geometric gate binds for ANN use.
"""

import json
import os
import shutil
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
K_CELLS, KM_ITERS, KM_SEED = 1024, 20, 7
NPROBES = (1, 2, 4, 8, 16, 32, 64)
P = {k: d for k, _, _, d in SEGMENT_PARAMS}
OUT = BASEDIR + "/rc6_ann.json"
REAL_PARTS = "/archive/tqp_real/wiki1024/part_%03d.npy"

_GENSEED = {"v": None}


def _chunk(a):
    return segment_corpus(
        P,
        0,
        DIM,
        _GENSEED["v"],
        rows=np.arange(a, min(a + 50000, POOL), dtype=np.int64),
    )


def gen_corpus(seed):
    _GENSEED["v"] = seed
    with get_context("fork").Pool(8) as pl:
        parts = pl.map(_chunk, list(range(0, POOL, 50000)))
    return np.concatenate(parts)


import torch  # noqa: E402

DEV = "cuda"
assert torch.cuda.is_available()


def load_real(off):
    part, rem = divmod(off, 1_000_000)
    a = np.load(REAL_PARTS % part, mmap_mode="r")
    return np.array(a[rem : rem + POOL], dtype=np.float32)


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


def kmeans(bt, k, iters, seed):
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


def characterize(xn, name):
    t0 = time.time()
    x = normalize_t(torch.from_numpy(xn).to(DEV))
    bi, qi = exch(np.arange(POOL), POOL - 10000, 10000, seed=31)
    bt = x[torch.from_numpy(bi).to(DEV)]
    qt = x[torch.from_numpy(qi).to(DEV)]
    d, gt = knn_t(bt, qt, 10)
    dn = d.cpu().numpy()
    rec = {
        "margin_nn": float(
            np.median((dn[:, 1] - dn[:, 0]) / np.maximum(dn[:, 0], 1e-9))
        ),
        "margin_10": float(
            np.median((dn[:, 9] - dn[:, 0]) / np.maximum(dn[:, 0], 1e-9))
        ),
    }

    cent, assign = kmeans(bt, K_CELLS, KM_ITERS, KM_SEED)
    cnt = torch.bincount(assign, minlength=K_CELLS).cpu().numpy().astype(float)
    frac = cnt / cnt.sum()
    rec["occ_cv"] = float(cnt.std() / cnt.mean())
    rec["occ_skew"] = float(
        ((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12)
    )
    rec["occ_max_share"] = float(frac.max())
    rec["occ_top10_share"] = float(np.sort(frac)[-10:].sum())

    qcell_sim = qt @ cent.T
    gt_cells = assign[gt]  # (10k, 10) cell of each true nn
    probe_rank = qcell_sim.argsort(dim=1, descending=True)
    rec["recall"] = {}
    rec["scan_frac"] = {}
    cell_rank = torch.empty_like(probe_rank)
    cell_rank.scatter_(
        1, probe_rank, torch.arange(K_CELLS, device=DEV).expand_as(probe_rank)
    )
    gt_cell_rank = torch.gather(cell_rank, 1, gt_cells)  # rank of each nn's cell
    frac_t = torch.from_numpy(frac).to(DEV).float()
    probed_mass = frac_t[probe_rank]  # (10k, K) mass by rank
    cum_mass = probed_mass.cumsum(1)
    for npb in NPROBES:
        rec["recall"][npb] = float((gt_cell_rank < npb).float().mean())
        rec["scan_frac"][npb] = float(cum_mass[:, npb - 1].mean())
    # probe depth for 95% recall per query set
    need = None
    for npb in range(1, K_CELLS + 1):
        if float((gt_cell_rank < npb).float().mean()) >= 0.95:
            need = npb
            break
    rec["nprobe_at_r95"] = need
    del x, bt, qt, cent
    torch.cuda.empty_cache()
    print(
        "%s | occ cv %5.2f skew %5.2f max %.4f top10 %.3f | "
        "m1 %.4f m10 %.4f | r@10: "
        % (
            name,
            rec["occ_cv"],
            rec["occ_skew"],
            rec["occ_max_share"],
            rec["occ_top10_share"],
            rec["margin_nn"],
            rec["margin_10"],
        )
        + " ".join("p%d %.3f" % (npb, rec["recall"][npb]) for npb in NPROBES)
        + " | np@95 %s  (%.0fs)" % (rec["nprobe_at_r95"], time.time() - t0),
        flush=True,
    )
    return rec


out = {}
for off in (3_000_000, 13_000_000, 23_000_000):
    out["real_%d" % off] = characterize(load_real(off), "real_%dM " % (off // 10**6))
    json.dump(out, open(OUT, "w"), indent=1)
for sd in (2027, 41):
    t0 = time.time()
    xn = gen_corpus(sd)
    print("generated seed %d in %.0fs" % (sd, time.time() - t0), flush=True)
    out["gen_%d" % sd] = characterize(xn, "gen_s%d " % sd)
    json.dump(out, open(OUT, "w"), indent=1)
print("RC6_ANN_DONE", flush=True)
