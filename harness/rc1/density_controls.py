"""Density-ladder controls — `PROFILE.md` §3b discriminating power.

The claim under test is structural, not empirical: for a generator whose rows
are **i.i.d.**, density is not a variable. n rows drawn from a pool of 50,000
and from a pool of 600,000 are identically distributed, so both §3b spans are
exactly zero and no parameter setting changes that. Real embeddings have a ratio
span of +2.397 +- 0.085.

The controls measure that prediction rather than assume it, and add an
instance-structured family (filaments) as the contrasting case.

The converse does not hold: shared structure is **necessary but not
sufficient**. A filament arm at 4 points per thread also spans ~0, because at
G1 ~ 140 the threads are not resolvable against ambient noise -- the structure
exists but does not govern the local geometry. See `R29`.

Env: DC_N, DC_NQ, DC_POOLS, DC_DIM, DC_PARTS, DC_OUT, DC_FAMILIES.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("DC_THREADS", "6"))

from openvector_bench.filament_gen import (  # noqa: E402
    FILAMENT_POOL_PARAMS,
    filament_pool_corpus,
)
from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

N_FIX = int(os.environ.get("DC_N", "25000"))
NQ = int(os.environ.get("DC_NQ", "10000"))
POOLS = json.loads(os.environ.get("DC_POOLS", "[50000,100000,200000,400000,600000]"))
DIM = int(os.environ.get("DC_DIM", "1024"))
PARTS = os.environ.get("DC_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("DC_OUT", "results/density_controls.json")
FAMILIES = json.loads(
    os.environ.get("DC_FAMILIES", '["iid_gaussian","exactcov_gaussian","filament"]')
)
PMAX = max(POOLS)


def ladder(full: np.ndarray, tag: str) -> dict:
    """The §3b ladder: fixed row count, varying pool, per-pool holdout."""
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
        r_ = rec[str(pool_n)]
        print(
            f"  {tag:16s} pool {pool_n:6d} dens {r_['density']:.4f}  "
            f"ratio {r_['ratio']:.3f}  G1 {r_['g1']:6.2f}",
            flush=True,
        )
    lo, hi = str(max(POOLS)), str(min(POOLS))
    sp = rec[hi]["ratio"] - rec[lo]["ratio"]
    gs = float(np.log(rec[hi]["g1"] / rec[lo]["g1"]))
    print(f"  {tag:16s} RATIO SPAN {sp:+.3f}   logG1 SPAN {gs:+.3f}\n", flush=True)
    return {"per_density": rec, "ratio_span": sp, "logg1_span": gs}


def load_real(count: int) -> np.ndarray:
    acc, got = [], 0
    for p in sorted(glob.glob(PARTS)):
        a = np.load(p, mmap_mode="r")
        take = min(len(a), count - got)
        acc.append(np.asarray(a[:take]))
        got += take
        if got >= count:
            break
    return normalize(np.concatenate(acc))


def main() -> int:
    rng = np.random.default_rng(3)
    out: dict[str, dict] = {}

    if "iid_gaussian" in FAMILIES:
        x = normalize(rng.standard_normal((PMAX, DIM)).astype(np.float32))
        out["iid_gaussian"] = ladder(x, "iid_gaussian")
        del x

    if "exactcov_gaussian" in FAMILIES:
        # i.i.d. rows carrying real's exact mean and covariance (the `R25`
        # control). Anisotropy is not the mechanism, and here the reason is
        # structural: i.i.d. rows cannot see the pool size.
        real = load_real(PMAX)
        mu = real.mean(0)
        cov = np.cov(real.T.astype(np.float64))
        chol = np.linalg.cholesky(cov + 1e-8 * np.eye(DIM))
        g = rng.standard_normal((PMAX, DIM)).astype(np.float64) @ chol.T + mu
        del real
        out["exactcov_gaussian"] = ladder(
            normalize(g.astype(np.float32)), "exactcov_gauss"
        )
        del g

    if "filament" in FAMILIES:
        for pt in (4.0, 48.0):
            p = dict(
                zip(
                    [s[0] for s in FILAMENT_POOL_PARAMS],
                    [s[3] for s in FILAMENT_POOL_PARAMS],
                )
            )
            p.update(
                points_per_thread=pt,
                fil_dim=48,
                arrange_dim=40,
                fil_scale=0.25,
                log2_basis=13.0,
                dup_frac=0.01,
                dup_cos=0.95,
            )
            t0 = time.time()
            xf = filament_pool_corpus(p, PMAX, DIM, 41)
            print(f"  filament pt{pt} generated in {time.time() - t0:.0f}s", flush=True)
            out[f"filament_pt{pt}"] = ladder(xf, f"filament_pt{pt}")
            del xf

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(
        "REAL TARGET      RATIO SPAN +2.397 +- 0.085   " "logG1 SPAN -0.494 +- 0.054",
        flush=True,
    )
    print(f"wrote {OUT}", flush=True)
    print("DENSITY_CONTROLS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
