"""R101: the ORIGINAL PREREG section-5 battery on validation-side rows.

S1 (the admission-shaped candidate, R100) vs real under the registered
round-9 protocol: all 8 gates including the never-modern-measured G2
(ball growth) and G7 (local-ID IQR), batteries A and B, the (n, k) grid,
5 subsamples, sealed rows (blake2b(i) % 4 == 3) excluded exactly as
step1_targets_v3 did. Scored with score_rc1 (the registered admission
arithmetic). This is validation-stage: it spends nothing sealed and
informs the seal decision.
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
OUT = BASEDIR + "/r101_cells.json"
CAP = 620000
_T0 = time.time()


def log(msg):
    print("[%7.0fs] %s" % (time.time() - _T0, msg), flush=True)


def sealed(i):
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


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
_h = hashlib.sha256(segment_corpus(P, 6000, 1024, 41).tobytes()).hexdigest()
log("S1 identity (seed 41, 6k): " + _h[:16])


def _chunk(a):
    return segment_corpus(
        P, 0, 1024, 41, rows=np.arange(a, min(a + 50000, CAP), dtype=np.int64)
    )


def main():
    log(
        "device=%s n_grid=%s k_grid=%s subs=%d nq=%d"
        % (G._DEV, G.N_GRID, G.K_GRID, G.SUBSAMPLES, G.N_QUERY)
    )
    corpus, real_q = G.load_target(TARGET, cap=CAP)
    keep = np.fromiter((i for i in range(len(corpus)) if not sealed(i)), dtype=np.int64)
    corpus = np.asarray(corpus[keep])
    log(
        "non-sealed real pool %s; real queries %s"
        % (corpus.shape, None if real_q is None else real_q.shape)
    )
    hold = min(G.N_QUERY * 2, len(corpus) // 10)
    corpus_q, corpus_base = uniform_holdout(corpus, hold, seed=7)

    with get_context("fork").Pool(8) as pl:
        parts = pl.map(_chunk, list(range(0, CAP, 50000)))
    s1 = np.concatenate(parts)
    log("S1 corpus %s" % (s1.shape,))
    s1_qa, s1_base = uniform_holdout(s1, hold, seed=70)

    cells = []
    for sub in range(G.SUBSAMPLES):
        for name, base_x, qa, qb in (
            ("real", corpus_base, corpus_q, real_q),
            ("s1", s1_base, s1_qa, real_q),
        ):
            for n in G.N_GRID:
                if n > len(base_x):
                    continue
                for battery, qset in (("A_corpus", qa), ("B_query", qb)):
                    if qset is None:
                        continue
                    for c in G.measure(name, battery, base_x, qset, n, sub):
                        cells.append(asdict(c))
                    log(
                        "sub %d %-5s n=%6d %s  (%d cells)"
                        % (sub, name, n, battery, len(cells))
                    )
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(cells, f, indent=1)
    log("wrote " + OUT)
    print("R101_VALBATTERY_DONE", flush=True)


if __name__ == "__main__":
    main()
