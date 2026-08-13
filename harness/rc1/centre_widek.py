"""Locate the super-cluster scale by measurement — `R36`.

`R35` reproduced real's cross-article profile but rested on ``per_super`` found
by sweeping, in a working region where 24 of 36 arms collapsed. That is the
failure mode of `R28` and `R30`, so the parameter is anchored here before use.

The article scale came from a k-NN gap cliff in *index* space. Above the article
there is no index locality (`R35`), so the analogue must be geometric: if
article centres cluster at some scale M, the centre cloud's ``s(k)`` turns over
near k = M. It does, at **k ~ 110 articles**.

Env: CW_ARTICLE, CW_POOL, CW_NQ, CW_KMAX, CW_PARTS, CW_OUT.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("CW_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    exchangeable_split,
    id_twonn,
    knn,
    normalize,
)

ARTICLE = int(os.environ.get("CW_ARTICLE", "23"))
POOL = int(os.environ.get("CW_POOL", "600000"))
NQ = int(os.environ.get("CW_NQ", "5000"))
KMAX = int(os.environ.get("CW_KMAX", "4000"))
PARTS = os.environ.get("CW_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("CW_OUT", "results/centre_widek.json")


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
    rc = real[np.arange(0, POOL, ARTICLE)]
    del real
    print(f"article-centre cloud: {len(rc)} centres (one per {ARTICLE} rows)")

    bi, qi = exchangeable_split(np.arange(len(rc)), len(rc) - NQ, NQ, seed=3)
    d, _ = knn(rc[bi], rc[qi], KMAX)
    kg = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 26)})
    r = np.array([float(np.median(d[:, k - 1])) for k in kg])
    s = np.gradient(np.log(np.array(kg, dtype=float)), np.log(r))

    print("\n    k      r(k)     s(k)")
    for k_, r_, s_ in zip(kg, r, s):
        print(f"{k_:6d}   {r_:.4f}   {s_:7.2f}")
    peak = int(kg[int(np.argmax(s))])
    print(f"\nprofile peaks at k = {peak} articles -> the super-cluster scale")
    print(f"G1 of the centre cloud: {id_twonn(d):.2f}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "k": kg,
                "r": [float(v) for v in r],
                "s": [float(v) for v in s],
                "peak_k": peak,
                "g1": float(id_twonn(d)),
                "n_centres": int(len(rc)),
                "article": ARTICLE,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}")
    print("CENTREWIDEK_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
