"""Are a row's METRIC neighbours its INDEX neighbours? — `R34`.

Any construction built as a sum of block-constant components over the row index
makes index proximity *equivalent* to metric proximity: the k nearest rows are
the k index-nearest rows, for every k. Real is under no such obligation, and
this measures whether it obeys.

It does not. There is a cliff between k = 16 and k = 32 — below it neighbours
are index-local, above it they are scattered across the corpus — and the count
of index-local neighbours saturates near 23 rather than growing with k. A row's
neighbourhood is a two-population mixture: its own article, then everything.

That excludes index-ordered constructions as a class (`R33`'s cascade among
them) and supplies the article size that produced the first ramp (`R34`).

Env: NG_POOL, NG_NQ, NG_KMAX, NG_PARTS, NG_OUT.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("NG_THREADS", "6"))

from openvector_bench.geometry import knn, normalize  # noqa: E402

POOL = int(os.environ.get("NG_POOL", "200000"))
NQ = int(os.environ.get("NG_NQ", "5000"))
KMAX = int(os.environ.get("NG_KMAX", "500"))
PARTS = os.environ.get("NG_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("NG_OUT", "results/nn_index_gap.json")
KS = (1, 2, 4, 8, 16, 32, 64, 100, 200, 500)


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
    x = normalize(np.concatenate(acc))
    del acc

    rng = np.random.default_rng(7)
    qi = np.sort(rng.choice(POOL, NQ, replace=False))
    mask = np.zeros(POOL, dtype=bool)
    mask[qi] = True
    base_idx = np.flatnonzero(~mask)
    _, nn = knn(x[base_idx], x[qi], KMAX)
    gap = np.abs(base_idx[nn] - qi[:, None])

    print("k     median|di|   frac|di|<=128   frac|di|<=1000")
    for k in KS:
        g = gap[:, :k]
        print(
            f"{k:4d}   {np.median(g):9.0f}   {float((g <= 128).mean()):13.3f}   "
            f"{float((g <= 1000).mean()):14.3f}"
        )
    print()
    for k in (4, 100, 500):
        g = gap[:, :k]
        print(
            f"k={k:3d}: mean count with |di|<=128 = "
            f"{float((g <= 128).sum(1).mean()):7.2f} of {k}   "
            f"(an index-ordered construction would give {min(k, 128)})"
        )

    res = {
        "k": list(KS),
        "median_gap": [float(np.median(gap[:, :k])) for k in KS],
        "frac_le128": [float((gap[:, :k] <= 128).mean()) for k in KS],
        "frac_le1000": [float((gap[:, :k] <= 1000).mean()) for k in KS],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {OUT}")
    print("NNGAP_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
