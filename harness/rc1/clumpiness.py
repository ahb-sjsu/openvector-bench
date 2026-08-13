"""Is the §3b density effect really an ADJACENCY effect?

`R29` registered a density ladder; `R30` found that a generator only responds to
density if its latent groups are contiguous in row index, but could not
reproduce the sign of real's G1 response. If thinning works by removing
same-article neighbours, the same effect should be reachable **without changing
density**: hold the span and the row count fixed and vary only how clumped the
sample is.

Two ladders, measured under one split construction:

1. **clumped** -- pool 600k, n 25k, span fixed. The support is drawn as runs of
   ``b`` contiguous rows spread over the whole corpus; only ``b`` varies.
2. **window** -- the density ladder re-expressed, same n and same split, with a
   contiguous window ``W`` varying.

They trace the same curve, so density is not the mechanism (`R31`).

Both use :func:`openvector_bench.geometry.exchangeable_split`. Drawing queries
as a global holdout while the base is clumped makes the split non-exchangeable
as ``b`` grows and inflates G1 to 60.9, smooth and monotone, pointing at the
opposite conclusion. That is `R23`'s defect and it has now recurred three times;
choosing the support first and partitioning it is the fix.

Env: CL_N, CL_NQ, CL_POOL, CL_BS, CL_WINDOWS, CL_PARTS, CL_OUT.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("CL_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    exchangeable_split,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

N_FIX = int(os.environ.get("CL_N", "25000"))
NQ = int(os.environ.get("CL_NQ", "10000"))
POOL = int(os.environ.get("CL_POOL", "600000"))
BS = json.loads(os.environ.get("CL_BS", "[1,2,5,10,25,50,100,250,1000,5000]"))
WINDOWS = json.loads(
    os.environ.get("CL_WINDOWS", "[35000,50000,100000,200000,400000,600000]")
)
PARTS = os.environ.get("CL_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("CL_OUT", "results/clumpiness.json")
NEED = N_FIX + NQ


def clumped_support(n_rows: int, need: int, b: int, rng) -> np.ndarray:
    """``need`` indices drawn as runs of ``b`` contiguous rows."""
    nb = int(np.ceil(need / b)) + 8
    starts = rng.choice(max(1, n_rows - b), size=nb, replace=False)
    idx = np.unique((starts[:, None] + np.arange(b)[None, :]).ravel())
    while len(idx) < need:
        idx = np.unique(
            np.concatenate(
                [idx, rng.choice(n_rows, need - len(idx) + 64, replace=False)]
            )
        )
    return np.sort(rng.permutation(idx)[:need])


def measure(x: np.ndarray, bi: np.ndarray, qi: np.ndarray) -> dict:
    gaps = np.diff(bi)
    d, _ = knn(x[bi], x[qi], max(PROFILE_KGRID))
    mu = d[:, 1] / np.maximum(d[:, 0], 1e-12)
    return {
        "ratio": profile_ratio(d),
        "g1": float(id_twonn(d)),
        "mu_med": float(np.median(mu)),
        "median_gap": float(np.median(gaps)),
        "frac_gap1": float((gaps == 1).mean()),
    }


def main() -> int:
    acc, got = [], 0
    for p in sorted(glob.glob(PARTS)):
        a = np.load(p, mmap_mode="r")
        take = min(len(a), POOL - got)
        acc.append(np.asarray(a[:take]))
        got += take
        if got >= POOL:
            break
    if not acc:
        print(f"no parts matched {PARTS}", file=sys.stderr)
        return 1
    full = normalize(np.concatenate(acc))
    del acc

    out: dict[str, dict] = {}
    print("CLUMPED: span FIXED at pool, n fixed; only block size varies", flush=True)
    rec: dict[str, dict] = {}
    for b in BS:
        rng = np.random.default_rng(20_000 + b)
        sup = clumped_support(len(full), NEED, b, rng)
        bi, qi = exchangeable_split(sup, N_FIX, NQ, seed=31)
        r = measure(full, bi, qi)
        r["block"] = b
        rec[str(b)] = r
        print(
            f"  b {b:5d}  ratio {r['ratio']:.3f}  G1 {r['g1']:6.2f}  "
            f"mu {r['mu_med']:.4f}  med_gap {r['median_gap']:5.1f}  "
            f"gap1 {r['frac_gap1']:.3f}",
            flush=True,
        )
    out["real_clumped"] = rec

    print(
        "\nWINDOW: the density ladder re-expressed, same split construction", flush=True
    )
    rec = {}
    for w in WINDOWS:
        rng = np.random.default_rng(700 + w // 1000)
        bi, qi = exchangeable_split(
            rng.choice(w, NEED, replace=False), N_FIX, NQ, seed=31
        )
        r = measure(full, bi, qi)
        r["window"] = w
        r["mean_gap"] = w / NEED
        rec[str(w)] = r
        print(
            f"  window {w:6d}  mean_gap {r['mean_gap']:5.1f}  "
            f"ratio {r['ratio']:.3f}  G1 {r['g1']:6.2f}  "
            f"mu {r['mu_med']:.4f}",
            flush=True,
        )
    out["real_window"] = rec

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("CLUMPINESS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
