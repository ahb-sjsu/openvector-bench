"""R67: port-fidelity check of the FROZEN package generator (RC1_PLAN, pre-RC-2).

The freeze candidate is `openvector_bench.segment_corpus` at its frozen
defaults, seed 1009 (never used in tuning). The audited numbers (`R66` V1)
came from the harness form, which differs in article-length law
(lognormal-cumsum vs geometric hierarchical blocks) and keying. This round
verifies the package port reproduces V1's panel within generation-seed noise
BEFORE the freeze is declared. In-sample targets; not the RC-2 one-shot.

Arm 0 = half A (gates incl g8 + section 3 ladder), arm 1 = half B
(section 3b five-pool + clumped s(k) + anatomy). The corpus is generated
in-pod by the actual package code (multiprocess over row chunks — legal
because the generator is random-access; bit-identity with serial generation
is asserted on a spot chunk).
"""

import json
import os
import shutil
import sys
import time
from multiprocessing import get_context

import numpy as np
import torch  # noqa: E402  (after generation: fork-clean CUDA)

os.makedirs("/tmp/ovb/openvector_bench", exist_ok=True)
for f in ("hashrng.py", "geometry.py", "segment_gen.py", "hubness.py"):
    shutil.copy("/code/" + f, "/tmp/ovb/openvector_bench/" + f)
open("/tmp/ovb/openvector_bench/__init__.py", "w").close()
sys.path.insert(0, "/tmp/ovb")

from openvector_bench.segment_gen import (  # noqa: E402
    SEGMENT_PARAMS,
    _hier_block,
    segment_corpus,
)  # noqa: E402

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("device=" + DEV, flush=True)

DIM, POOL, SEED = 1024, 600000, 1009
P = {k: d for k, _, _, d in SEGMENT_PARAMS}
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

S3_BANDS = {
    "trend": (0.2536, 0.6488),
    "g1exp": (-0.227, -0.112),
    "rung_ratio": {
        25000: (1.175, 1.571),
        50000: (1.504, 1.728),
        100000: (1.749, 2.097),
        200000: (2.067, 2.559),
    },
}
S3B_BANDS = {
    50000: {"ratio": (3.574, 3.870), "g1": (15.11, 17.43)},
    100000: {"ratio": (2.294, 2.870), "g1": (16.30, 17.86)},
    200000: {"ratio": (1.638, 1.910), "g1": (18.80, 20.24)},
    400000: {"ratio": (1.428, 1.500), "g1": (23.14, 24.10)},
    600000: {"ratio": (1.273, 1.377), "g1": (25.54, 27.78)},
    "rspan": (2.227, 2.567),
    "gspan": (-0.602, -0.386),
}


def _chunk(a):
    return segment_corpus(
        P, 0, DIM, SEED, rows=np.arange(a, min(a + 50000, POOL), dtype=np.int64)
    )


def gen_corpus():
    t0 = time.time()
    starts = list(range(0, POOL, 50000))
    with get_context("fork").Pool(4) as pl:
        parts = pl.map(_chunk, starts)
    x = np.concatenate(parts)
    # spot-assert bit-identity of the parallel emission with a direct call
    probe = np.arange(150000, 150100, dtype=np.int64)
    assert np.array_equal(
        segment_corpus(P, 0, DIM, SEED, rows=probe), x[150000:150100]
    ), "parallel emission mismatch"
    print(
        "corpus %dx%d in %.0fs (%.2f MB/s total)"
        % (x.shape[0], DIM, time.time() - t0, x.nbytes / 1e6 / (time.time() - t0)),
        flush=True,
    )
    zero = np.zeros(POOL, dtype=np.int64)
    a_of = _hier_block(zero, np.arange(POOL, dtype=np.int64), P["art_break"], salt=11)
    return torch.from_numpy(x).to(DEV), a_of


def normalize_t(x):
    return x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)


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


_i = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
if _i > 1:
    print("R67_DONE", flush=True)
    sys.exit(0)
x, a_of = gen_corpus()
key = "FROZEN_%s" % ("A" if _i == 0 else "B")
rec = {}
t0 = time.time()

if _i == 0:
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
    tb = S3_BANDS
    flags = [
        "trend "
        + ("IN" if tb["trend"][0] <= rec["s3_trend"] <= tb["trend"][1] else "out"),
        "g1exp "
        + ("IN" if tb["g1exp"][0] <= rec["s3_g1exp"] <= tb["g1exp"][1] else "out"),
    ]
    for n_r, rat in zip((25000, 50000, 100000, 200000), ratios):
        lo, hi = tb["rung_ratio"][n_r]
        flags.append("r%dk %s" % (n_r // 1000, "IN" if lo <= rat <= hi else "out"))
    print(
        "%s | g1 %5.2f g3 %5.1f g4 %4d g5 %5.3f g6 %5.3f g8 %5.3f | "
        "S3 trend %+.3f g1exp %+.3f | %s  (%.0fs)"
        % (
            key,
            rec["g1"],
            rec["g3"],
            rec["g4"],
            rec["g5"],
            rec["g6"],
            rec["g8"],
            rec["s3_trend"],
            rec["s3_g1exp"],
            " ".join(flags),
            time.time() - t0,
        ),
        flush=True,
    )
else:
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
    rng = np.random.default_rng(20_100)
    b2, q2 = exch(clumped(POOL, 35000, 100, rng), 25000, 10000)
    d2, n2 = knn_t(
        x[torch.from_numpy(b2).to(DEV)], x[torch.from_numpy(q2).to(DEV)], 500
    )
    dm, nm = d2.cpu().numpy(), n2.cpu().numpy()
    del d2, n2
    _, s = sk_curve(dm)
    rec["s"] = [float(v) for v in s]
    rec["rms_singleblock"] = float(np.sqrt(np.mean((s - REAL_S) ** 2)))
    same = a_of[b2[nm]] == a_of[q2][:, None]
    din = dm[same]
    dout = dm[~same]
    rec["D_article"] = float(np.percentile(din, 90) / max(np.percentile(din, 10), 1e-9))
    rec["overlap"] = float((dout < np.percentile(din, 90)).mean())
    fl = []
    for Pn in (50000, 100000, 200000, 400000, 600000):
        rb = S3B_BANDS[Pn]["ratio"]
        gb = S3B_BANDS[Pn]["g1"]
        fl.append(
            "%dk r%s g%s"
            % (
                Pn // 1000,
                "IN" if rb[0] <= vals[Pn]["ratio"] <= rb[1] else "X",
                "IN" if gb[0] <= vals[Pn]["g1"] <= gb[1] else "X",
            )
        )
    rs, gs = S3B_BANDS["rspan"], S3B_BANDS["gspan"]
    fl.append("rspan " + ("IN" if rs[0] <= rec["rspan"] <= rs[1] else "out"))
    fl.append("gspan " + ("IN" if gs[0] <= rec["gspan"] <= gs[1] else "out"))
    print(
        "%s | rspan %+6.3f gspan %+6.3f | %s | s14 %5.1f s53 %5.1f "
        "rms1b %5.2f  (%.0fs)"
        % (
            key,
            rec["rspan"],
            rec["gspan"],
            " ".join(fl),
            s[4],
            s[8],
            rec["rms_singleblock"],
            time.time() - t0,
        ),
        flush=True,
    )

print("RESULT_JSON " + json.dumps({key: rec}), flush=True)
print("R67_DONE", flush=True)
