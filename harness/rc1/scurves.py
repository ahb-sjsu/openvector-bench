"""The full s(k) and r(k) curves, not just the ratio — `R33`.

`R32` left the ramp as the single discrepancy but had only ever measured its
summary, ``s(500)/s(4)``. One number is consistent with several very different
curve shapes, which imply different constructions.

Measures both real regimes (`R31`'s clumping extremes, b = 1 and b = 100) and a
generator arm under one split construction, so the curves are comparable.

The result corrected `R31`'s framing: the two regimes **converge** at large k
(35.13 vs 35.73 at k = 500), so real is one ~36-dimensional cloud carrying a
~9-dimensional local structure, not two nested manifolds of dimension 15 and 26.
Those were TwoNN values, and TwoNN reads the k = 1,2 scale.

Env: SC_N, SC_NQ, SC_POOL, SC_BS, SC_PARTS, SC_OUT.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("SC_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    exchangeable_split,
    growth_slope,
    id_twonn,
    knn,
    normalize,
)

N_FIX = int(os.environ.get("SC_N", "25000"))
NQ = int(os.environ.get("SC_NQ", "10000"))
POOL = int(os.environ.get("SC_POOL", "600000"))
BS = json.loads(os.environ.get("SC_BS", "[1,100]"))
PARTS = os.environ.get("SC_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("SC_OUT", "results/scurves.json")
NEED = N_FIX + NQ


def clumped_support(n_rows: int, need: int, b: int, rng) -> np.ndarray:
    nb = int(np.ceil(need / b)) + 8
    st = rng.choice(max(1, n_rows - b), size=nb, replace=False)
    idx = np.unique((st[:, None] + np.arange(b)[None, :]).ravel())
    while len(idx) < need:
        idx = np.unique(np.concatenate(
            [idx, rng.choice(n_rows, need - len(idx) + 64, replace=False)]))
    return np.sort(rng.permutation(idx)[:need])


def curve(x: np.ndarray, bi: np.ndarray, qi: np.ndarray) -> dict:
    d, _ = knn(x[bi], x[qi], max(PROFILE_KGRID))
    r, s = growth_slope(d)
    return {"k": list(PROFILE_KGRID), "r": [float(v) for v in r],
            "s": [float(v) for v in s], "g1": float(id_twonn(d))}


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
    real = normalize(np.concatenate(acc))
    del acc

    out = {}
    for b in BS:
        rng = np.random.default_rng(20_000 + b)
        bi, qi = exchangeable_split(
            clumped_support(POOL, NEED, b, rng), N_FIX, NQ, seed=31)
        out[f"real_b{b}"] = curve(real, bi, qi)

    print("   k |" + "".join(f"  r {n:>10s}" for n in out)
          + " |" + "".join(f"  s {n:>10s}" for n in out))
    for i, k in enumerate(PROFILE_KGRID):
        rr = "".join(f"{out[n]['r'][i]:13.4f}" for n in out)
        ss = "".join(f"{out[n]['s'][i]:13.2f}" for n in out)
        print(f"{k:4d} |{rr} |{ss}")
    for n, v in out.items():
        s = v["s"]
        print(f"{n:12s} s(4) {s[0]:6.2f}  s(500) {s[-1]:6.2f}  "
              f"ratio {s[-1] / s[0]:6.3f}  G1 {v['g1']:6.2f}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT}")
    print("SCURVES_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
