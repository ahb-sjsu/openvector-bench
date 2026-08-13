"""Row ordering, not shared structure, decides whether density is a variable.

`R29` found that the filament family spans ~0 on the `PROFILE.md` §3b density
ladder despite having shared thread structure. The cause is
`filament_gen.py:126`, `owner = rng.integers(0, n_thread, n)`: thread membership
is uniform over the row index and `n_thread` is fixed by the generation size, so
a prefix of P rows holds every thread thinned proportionally and the expected
co-thread count in a draw of n is `n/n_thread` regardless of P.

Real is ordered by article -- adjacent rows are passages of the same article --
so a prefix holds proportionally fewer distinct articles and subsampling thins
the group inventory. This driver measures both halves:

1. real's index correlation (mean cosine by row gap) against a random baseline;
2. the §3b ladder for a filament variant with contiguous ownership,
   `owner(i) = i // points_per_thread`, optionally with lognormal group sizes.

Contiguous ownership turns the span from +0.014 into +2.5 to +4.5. It does not
fix the family: the log G1 span keeps the wrong sign and the ratio ladder is
non-monotone in every arm measured (`R30`).

Env: DO_N, DO_NQ, DO_POOLS, DO_DIM, DO_PARTS, DO_OUT, DO_PPT, DO_FILDIM,
DO_ARRDIM, DO_SIZES.
"""

from __future__ import annotations

import glob
import itertools
import json
import os
import sys
import time

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("DO_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

N_FIX = int(os.environ.get("DO_N", "25000"))
NQ = int(os.environ.get("DO_NQ", "10000"))
POOLS = json.loads(os.environ.get("DO_POOLS", "[50000,100000,200000,400000,600000]"))
DIM = int(os.environ.get("DO_DIM", "1024"))
PARTS = os.environ.get("DO_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("DO_OUT", "results/density_ordering.json")
PPT = json.loads(os.environ.get("DO_PPT", "[48,96]"))
FILDIM = json.loads(os.environ.get("DO_FILDIM", "[48]"))
ARRDIM = int(os.environ.get("DO_ARRDIM", "40"))
SIZES = json.loads(os.environ.get("DO_SIZES", '["fixed"]'))
PMAX = max(POOLS)
TGT_R, TGT_G = 2.397, -0.494  # PROFILE.md §3b


def ladder(full: np.ndarray, tag: str) -> dict:
    rec: dict[str, dict] = {}
    for pool_n in POOLS:
        pool = full[:pool_n]
        hr = np.random.default_rng(7)
        m = np.zeros(pool_n, dtype=bool)
        m[hr.choice(pool_n, NQ, replace=False)] = True
        q, body = pool[m], pool[~m]
        r2 = np.random.default_rng(10_000 + N_FIX)
        d, _ = knn(
            body[r2.choice(len(body), N_FIX, replace=False)], q, max(PROFILE_KGRID)
        )
        rec[str(pool_n)] = {
            "density": N_FIX / pool_n,
            "ratio": profile_ratio(d),
            "g1": float(id_twonn(d)),
        }
    rs = [rec[str(p)]["ratio"] for p in POOLS]
    gs = [rec[str(p)]["g1"] for p in POOLS]
    sp = rs[0] - rs[-1]
    gsp = float(np.log(gs[0] / gs[-1]))
    mono = all(rs[i] >= rs[i + 1] for i in range(len(rs) - 1))
    print(f"  {tag:22s} ratios {[round(v, 2) for v in rs]}", flush=True)
    print(f"  {tag:22s} G1     {[round(v, 1) for v in gs]}", flush=True)
    print(
        f"  {tag:22s} SPAN r {sp:+.3f} (tgt {TGT_R:+.3f})  g {gsp:+.3f} "
        f"(tgt {TGT_G:+.3f})  monotone={mono}\n",
        flush=True,
    )
    return {"per_density": rec, "ratio_span": sp, "logg1_span": gsp, "monotone": mono}


def filament_ordered(
    ppt,
    fil_dim,
    arr_dim,
    fs,
    n,
    dim,
    seed,
    sizes="fixed",
    log2_basis=13.0,
    chunk=50_000,
    size_sd=0.8,
) -> np.ndarray:
    """Filaments with CONTIGUOUS group ownership.

    ``sizes='fixed'`` gives hard blocks of ``ppt`` rows; ``'lognorm'`` gives
    lognormal group lengths of the same mean, on the reasoning that real's index
    correlation decays smoothly over ~100 rows rather than in hard blocks. The
    lognormal variant measured *worse* (`R30`); it is kept so the result is
    reproducible rather than because it helps.
    """
    rng = np.random.default_rng(seed)
    if sizes == "fixed":
        n_thread = max(2, int(round(n / ppt)))
        bounds = np.arange(1, n_thread + 1, dtype=np.int64) * int(round(ppt))
    else:
        est = int(n / ppt * 1.6) + 16
        ln = rng.lognormal(np.log(ppt) - 0.5 * size_sd**2, size_sd, est)
        bounds = np.cumsum(np.maximum(1, np.round(ln)).astype(np.int64))
        bounds = np.append(bounds[bounds < n], n)
        n_thread = len(bounds)
    n_basis = max(fil_dim * 2, int(round(2**log2_basis)))
    basis_a = np.linalg.qr(rng.standard_normal((dim, arr_dim)))[0].astype(np.float32)
    cc = rng.standard_normal((n_thread, arr_dim)).astype(np.float32)
    cc /= np.maximum(np.linalg.norm(cc, axis=1, keepdims=True), 1e-12)
    basis_pool = rng.standard_normal((n_basis, dim)).astype(np.float32) / np.sqrt(
        dim, dtype=np.float32
    )
    thread_idx = rng.integers(0, n_basis, (n_thread, fil_dim))
    x = np.empty((n, dim), dtype=np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        own = np.minimum(
            np.searchsorted(bounds, np.arange(s, e), side="right"), n_thread - 1
        )
        acc = cc[own] @ basis_a.T
        u = rng.standard_normal((e - s, fil_dim)).astype(np.float32)
        sel = thread_idx[own]
        for j in range(fil_dim):
            acc += (np.float32(fs) * u[:, j])[:, None] * basis_pool[sel[:, j]]
        x[s:e] = acc
    return normalize(x)


def main() -> int:
    out: dict[str, dict] = {}

    # (1) Is real actually ordered by article?
    acc, got = [], 0
    for p in sorted(glob.glob(PARTS)):
        a = np.load(p, mmap_mode="r")
        take = min(len(a), PMAX - got)
        acc.append(np.asarray(a[:take]))
        got += take
        if got >= PMAX:
            break
    if acc:
        real = normalize(np.concatenate(acc))
        del acc
        adj = float(np.mean(np.sum(real[:200_000] * real[1:200_001], axis=1)))
        rr = np.random.default_rng(5)
        i = rr.integers(0, PMAX, 200_000)
        j = rr.integers(0, PMAX, 200_000)
        rnd = float(np.mean(np.sum(real[i] * real[j], axis=1)))
        reach = {
            str(g): float(
                np.mean(np.sum(real[:100_000] * real[g : 100_000 + g], axis=1))
            )
            for g in (1, 2, 4, 8, 16, 32, 64, 128)
        }
        print(
            f"REAL ORDERING: adjacent cos {adj:.4f}   random cos {rnd:.4f}", flush=True
        )
        print("  cos by gap:", {k: round(v, 4) for k, v in reach.items()}, flush=True)
        out["real_ordering"] = {
            "adjacent_cos": adj,
            "random_cos": rnd,
            "cos_by_gap": reach,
        }
        del real

    # (2) The §3b ladder under contiguous ownership.
    for ppt, fd, sizes in itertools.product(PPT, FILDIM, SIZES):
        tag = f"pt{ppt}_fd{fd}_{sizes}"
        t0 = time.time()
        xf = filament_ordered(ppt, fd, ARRDIM, 0.25, PMAX, DIM, 41, sizes=sizes)
        print(f"  {tag} generated in {time.time() - t0:.0f}s", flush=True)
        out[tag] = ladder(xf, tag)
        del xf
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)

    print(
        f"REAL TARGET      RATIO SPAN {TGT_R:+.3f} +- 0.085   "
        f"logG1 SPAN {TGT_G:+.3f} +- 0.054",
        flush=True,
    )
    print(f"wrote {OUT}", flush=True)
    print("DENSITY_ORDERING_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
