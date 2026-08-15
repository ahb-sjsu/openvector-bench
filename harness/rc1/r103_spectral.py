"""R102: RC-13 Phase A - principal-frame alignment, validation battery.

M1: rotation Q = V_real @ V_gen.T (variance-rank matched), V_real fitted
on TRAIN rows only (blake2b % 4 in {0,1}). M2: mean restoration at beta
in {0, 0.5, 1.0}. Candidates measured under the identical r101 protocol;
real cells reused from r101_cells.json; scored with score_rc1.
"""

import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import asdict
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
    ("costab.py", "costab.py"),
):
    shutil.copy(BASEDIR + "/" + src, PKG + "/" + dst)
open(PKG + "/__init__.py", "w").close()
sys.path.insert(0, BASEDIR + "/ovbpkg")

from openvector_bench import geometry as G  # noqa: E402
from openvector_bench.segment_gen import SEGMENT_PARAMS, segment_corpus  # noqa: E402

TARGET = "/archive/tqp_real/wiki1024"
OUT = BASEDIR + "/r103_cells.json"
CAP = 620000
_T0 = time.time()


def log(msg):
    print("[%7.0fs] %s" % (time.time() - _T0, msg), flush=True)


def part(i):
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4


def uniform_holdout(x, hold, seed):
    rng = np.random.default_rng(seed)
    hidx = np.sort(rng.choice(len(x), size=hold, replace=False))
    mask = np.zeros(len(x), dtype=bool)
    mask[hidx] = True
    return x[mask], x[~mask]


P = {k: d for k, _, _, d in SEGMENT_PARAMS}
P.update(
    p_dup=0.0,
    p_echo=0.11,
    echo_k=3,
    echo_win=100000,
    echo_alpha=0.96,
    pool_alpha=0.23,
    seg_break=0.138,
    fil_scale=0.99,
)


def _chunk(a):
    return segment_corpus(
        P, 0, 1024, 41, rows=np.arange(a, min(a + 50000, CAP), dtype=np.int64)
    )


def pca_frame(x, label):
    import torch

    xt = torch.from_numpy(np.asarray(x, dtype=np.float32)).to("cuda")
    mu = xt.mean(0, keepdim=True)
    sub = xt[torch.randperm(xt.shape[0], device="cuda")[:100000]] - mu
    _, S, Vh = torch.linalg.svd(sub, full_matrices=False)
    log("%s: top-5 singular %s" % (label, [round(float(v), 1) for v in S[:5]]))
    return Vh.T.cpu().numpy().astype(np.float32), mu[0].cpu().numpy()


def main():
    log("device=%s grid=%s subs=%d" % (G._DEV, G.N_GRID, G.SUBSAMPLES))
    corpus, real_q = G.load_target(TARGET, cap=CAP)
    parts_arr = np.fromiter((part(i) for i in range(len(corpus))), dtype=np.int64)
    train = np.asarray(corpus[parts_arr <= 1])
    nonsealed = np.asarray(corpus[parts_arr != 3])
    log(
        "train %s nonsealed %s queries %s"
        % (train.shape, nonsealed.shape, real_q.shape)
    )

    V_real, m_real = pca_frame(train, "real-train")
    m_norm = float(np.linalg.norm(m_real))
    log("real mean norm %.4f" % m_norm)

    with get_context("fork").Pool(8) as pl:
        chunks = pl.map(_chunk, list(range(0, CAP, 50000)))
    s1 = np.concatenate(chunks)
    V_gen, _ = pca_frame(s1, "s1")
    Q = (V_real @ V_gen.T).astype(np.float32)
    log(
        "rotation fitted; ||QQ^T - I||_max = %.2e"
        % float(np.abs(Q @ Q.T - np.eye(1024, dtype=np.float32)).max())
    )

    s1_rot = (s1 @ Q.T).astype(np.float32)

    def with_mean(x, beta):
        if beta == 0.0:
            return x
        y = x + np.float32(beta) * m_real[None, :]
        return y

    hold = min(G.N_QUERY * 2, len(nonsealed) // 10)
    cells = []
    # Phase B: partial spectral matching in the aligned frame. Per-direction
    # stds: real from the train PCA; gen from the rotated cloud. Scale
    # coordinates along V_real axes by (sigma_real/sigma_gen)^gamma.
    import torch

    xt = torch.from_numpy(s1_rot).to("cuda")
    coords = xt @ torch.from_numpy(V_real).to("cuda")  # (N, 1024)
    sig_gen = coords.std(0).cpu().numpy().astype(np.float64)
    tr = torch.from_numpy(train.astype(np.float32)).to("cuda")
    trc = (tr - tr.mean(0, keepdim=True)) @ torch.from_numpy(V_real).to("cuda")
    sig_real = trc.std(0).cpu().numpy().astype(np.float64)
    del tr, trc
    srat = sig_real / np.maximum(sig_gen, 1e-9)
    log(
        "spectral ratio: median %.3f  p10 %.3f  p90 %.3f"
        % (np.median(srat), np.percentile(srat, 10), np.percentile(srat, 90))
    )

    def spectral(gamma):
        sc = torch.from_numpy((srat**gamma).astype(np.float32)).to("cuda")
        y = (coords * sc) @ torch.from_numpy(V_real.T).to("cuda")
        return y.cpu().numpy().astype(np.float32) + m_real[None, :]

    variants = {
        "s1_g25": spectral(0.25),
        "s1_g50": spectral(0.50),
        "s1_g75": spectral(0.75),
        "s1_g100": spectral(1.00),
    }

    # G6 diagnostic: attractiveness dispersion real vs candidate at n=100k
    try:
        from openvector_bench import hubness as H

        for nm, x in (("real", nonsealed), ("s1_g50", variants["s1_g50"])):
            qa2, bb = uniform_holdout(x, hold, seed=7 if nm == "real" else 70)
            rng = np.random.default_rng(1)
            bi = rng.choice(len(bb), 100000, replace=False)
            base = G.normalize(bb[bi])
            q = G.normalize(qa2[:10000])
            d, idx = G.knn(base, q, 10)
            cnt = np.bincount(
                np.asarray(idx)[:, :10].ravel(), minlength=len(base)
            ).astype(float)
            log(
                "G6diag %-7s occ var/mean %.3f  raw skew %.2f  deconv %.2f"
                % (
                    nm,
                    cnt.var() / max(cnt.mean(), 1e-9),
                    float(
                        ((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12)
                    ),
                    H.attractiveness_skew(cnt),
                )
            )
    except Exception as e:
        log("G6diag failed: %r" % (e,))
    for name, x in variants.items():
        qa, base_x = uniform_holdout(x, hold, seed=70)
        for sub in range(3):
            for n in G.N_GRID:
                if n > len(base_x):
                    continue
                for battery, qset in (("A_corpus", qa), ("B_query", real_q)):
                    for c in G.measure(name, battery, base_x, qset, n, sub):
                        cells.append(asdict(c))
                    log(
                        "sub %d %-9s n=%6d %s (%d cells)"
                        % (sub, name, n, battery, len(cells))
                    )
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(cells, f, indent=1)
    log("wrote " + OUT)
    print("R103_SPECTRAL_DONE", flush=True)


if __name__ == "__main__":
    main()
