"""Factorial (n, pool) grid — separates the row-count effect from the density one.

`PROFILE.md` §3's rung ladder varies n at a fixed pool, so density and row count
move together and `trend` is their sum. A factorial design in both breaks the
confound. Fits

    ratio  ~ a + b*log(n) + c*log(density)
    log G1 ~ a + b*log(n) + c*log(density)

and reports each partial with its standard error.

The fitted slopes are diagnostic only. They are **not** the registered
statistic — the response is strongly convex in log density, so a linear
coefficient depends on the pools chosen. `PROFILE.md` §3b registers per-density
values and a fixed-endpoint contrast instead; see `density_ladder.py`.

Env: DG_NS, DG_POOLS, DG_NQ, DG_PARTS, DG_OUT.
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
    os.environ.setdefault(_v, os.environ.get("DG_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

NS = json.loads(os.environ.get("DG_NS", "[25000,50000,100000]"))
POOLS = json.loads(os.environ.get("DG_POOLS", "[200000,400000,600000]"))
NQ = int(os.environ.get("DG_NQ", "10000"))
PARTS = os.environ.get("DG_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("DG_OUT", "results/density_grid.json")


def main() -> int:
    pmax = max(POOLS)
    parts = sorted(glob.glob(PARTS))
    if not parts:
        print(f"no parts matched {PARTS}", file=sys.stderr)
        return 1
    acc, got = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        take = min(len(a), pmax - got)
        acc.append(np.asarray(a[:take]))
        got += take
        if got >= pmax:
            break
    full = normalize(np.concatenate(acc))
    del acc
    print("loaded", full.shape, flush=True)

    rows = []
    for pool_n, n in itertools.product(POOLS, NS):
        t0 = time.time()
        # Holdout from within THIS pool. A single holdout over the largest pool
        # makes the split non-exchangeable for smaller ones and inflates G1
        # smoothly with pool size, which reads as a density effect (`R23`,
        # `R29`).
        pool = full[:pool_n]
        hr = np.random.default_rng(7)
        m = np.zeros(pool_n, dtype=bool)
        m[hr.choice(pool_n, NQ, replace=False)] = True
        q, body = pool[m], pool[~m]
        r2 = np.random.default_rng(10_000 + n)
        d, _ = knn(body[r2.choice(len(body), n, replace=False)], q, max(PROFILE_KGRID))
        mu = d[:, 1] / np.maximum(d[:, 0], 1e-12)
        rec = {
            "pool": pool_n,
            "n": n,
            "density": n / pool_n,
            "ratio": profile_ratio(d),
            "g1": float(id_twonn(d)),
            "mu_med": float(np.median(mu)),
            "mu_frac": float((mu > 1.5).mean()),
        }
        rows.append(rec)
        print(
            f"pool {pool_n:6d} n {n:6d} dens {rec['density']:.4f}  "
            f"ratio {rec['ratio']:.3f}  G1 {rec['g1']:6.2f}  "
            f"mu {rec['mu_med']:.4f}  ({time.time() - t0:.0f}s)",
            flush=True,
        )

    ln = np.log([r["n"] for r in rows])
    ld = np.log([r["density"] for r in rows])
    a_mat = np.column_stack([np.ones_like(ln), ln, ld])

    def fit(y):
        c, *_ = np.linalg.lstsq(a_mat, y, rcond=None)
        resid = y - a_mat @ c
        dof = len(y) - a_mat.shape[1]
        cov = float((resid**2).sum() / dof) * np.linalg.inv(a_mat.T @ a_mat)
        return (
            [float(v) for v in c],
            [float(np.sqrt(cov[i, i])) for i in range(a_mat.shape[1])],
            float(np.sqrt((resid**2).mean())),
        )

    cr, sr, rr = fit(np.array([r["ratio"] for r in rows]))
    cg, sg, rg = fit(np.log([r["g1"] for r in rows]))
    res = {
        "grid": rows,
        "nq": NQ,
        "ratio": {
            "const": cr[0],
            "d_dlogn": cr[1],
            "d_dlogdens": cr[2],
            "sd": {"d_dlogn": sr[1], "d_dlogdens": sr[2]},
            "rms_resid": rr,
        },
        "logg1": {
            "const": cg[0],
            "d_dlogn": cg[1],
            "d_dlogdens": cg[2],
            "sd": {"d_dlogn": sg[1], "d_dlogdens": sg[2]},
            "rms_resid": rg,
        },
    }
    print(
        f"\nratio  = {cr[0]:+.3f} {cr[1]:+.4f}(+-{sr[1]:.4f})*log n "
        f"{cr[2]:+.4f}(+-{sr[2]:.4f})*log dens   rms {rr:.4f}",
        flush=True,
    )
    print(
        f"log G1 = {cg[0]:+.3f} {cg[1]:+.4f}(+-{sg[1]:.4f})*log n "
        f"{cg[2]:+.4f}(+-{sg[2]:.4f})*log dens   rms {rg:.4f}",
        flush=True,
    )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("DENSITY_GRID_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
