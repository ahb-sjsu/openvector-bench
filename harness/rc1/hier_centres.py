"""Give the arrangement real's cross-article profile — `R35`.

`R34` localised the last failure to one component: a uniform cloud in a fixed
subspace has a **decreasing** profile at every dimension (s(500)/s(4) = 0.87
down to 0.80) where real's cross-article regime **increases** (1.282). That is a
shape problem, so no choice of ``arr_dim`` fixes it.

Two parts:

1. **Is the structure above the article in the row index?** Take one row per
   article from real and ask whether its neighbours are article-index-local.
   They are not — median gap ~7,000 of 26,087 articles — so super-clusters must
   be assigned by **hash**, the opposite of the article level where contiguity
   is the whole mechanism (`R30`, `R31`).
2. **Calibrate a two-level centre cloud standalone.** Cheap (40k points, no 600k
   corpus), which is the discipline `R33` forced: `R32` set a parameter and
   never measured what the component delivered.

Result: s(4) 26.43 and s(500) 35.06 against 27.40 and 35.13, with G1 44.80
against 26.09 — the residual sits below k = 4. Note that only 12 of 36 arms gave
a non-collapsed s(500); the working region is narrow and ``per_super`` is swept
rather than measured, unlike the article scale of 23.

Env: HC_NA, HC_NQ, HC_DIM, HC_PARTS, HC_ARTICLE, HC_OUT.
"""

from __future__ import annotations

import glob
import itertools
import json
import os
import sys

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("HC_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    exchangeable_split,
    growth_slope,
    id_twonn,
    knn,
    normalize,
)

NA = int(os.environ.get("HC_NA", "40000"))
NQ = int(os.environ.get("HC_NQ", "10000"))
DIM = int(os.environ.get("HC_DIM", "1024"))
ARTICLE = int(os.environ.get("HC_ARTICLE", "23"))
PARTS = os.environ.get("HC_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("HC_OUT", "results/hier_centres.json")
# real's cross-article regime (`R33` s-curves, b = 1)
T_S4, T_S500, T_G1 = 27.40, 35.13, 26.09


def hier_centres(n, dim, per_super, d_loc, d_glob, w_loc, seed=5):
    """Articles grouped into super-clusters **by hash**, not by index."""
    rng = np.random.default_rng(seed)
    n_sup = max(2, int(round(n / per_super)))
    bg = np.linalg.qr(rng.standard_normal((dim, d_glob)))[0].astype(np.float32)
    bl = np.linalg.qr(rng.standard_normal((dim, d_loc)))[0].astype(np.float32)
    cs = rng.standard_normal((n_sup, d_glob)).astype(np.float32)
    cs /= np.maximum(np.linalg.norm(cs, axis=1, keepdims=True), 1e-12)
    cl = rng.standard_normal((n, d_loc)).astype(np.float32)
    cl /= np.maximum(np.linalg.norm(cl, axis=1, keepdims=True), 1e-12)
    sup = rng.integers(0, n_sup, n)
    return normalize(cs[sup] @ bg.T + np.float32(w_loc) * (cl @ bl.T))


def profile(c):
    bi, qi = exchangeable_split(np.arange(len(c)), len(c) - NQ, NQ, seed=3)
    d, _ = knn(c[bi], c[qi], max(PROFILE_KGRID))
    _, s = growth_slope(d)
    return float(s[0]), float(s[-1]), float(s[-1] / s[0]), float(id_twonn(d))


def main() -> int:
    out: dict = {}

    parts = sorted(glob.glob(PARTS))
    if parts:
        acc, got = [], 0
        for p in parts:
            a = np.load(p, mmap_mode="r")
            take = min(len(a), 600_000 - got)
            acc.append(np.asarray(a[:take]))
            got += take
            if got >= 600_000:
                break
        real = normalize(np.concatenate(acc))
        del acc
        rc = real[np.arange(0, len(real), ARTICLE)]
        bi, qi = exchangeable_split(np.arange(len(rc)), len(rc) - 5000, 5000, seed=3)
        _, nn = knn(rc[bi], rc[qi], 200)
        gap = np.abs(bi[nn] - qi[:, None])
        print("real article-centre cloud: are its neighbours article-index-local?")
        for k in (1, 4, 16, 64, 200):
            print(
                f"  k={k:3d}  median |d article| {np.median(gap[:, :k]):8.0f} "
                f"of {len(rc)}   frac<=10 {float((gap[:, :k] <= 10).mean()):.3f}"
            )
        out["real_centre_gaps"] = {
            str(k): float(np.median(gap[:, :k])) for k in (1, 4, 16, 64, 200)
        }
        del real, rc

    print("\nper_super d_loc d_glob w_loc |  s(4)   s(500)  ratio    G1     err")
    best = None
    for per, dl, dg, wl in itertools.product(
        (200, 600, 2000), (40, 52, 64), (80, 110), (0.4, 0.7)
    ):
        c = hier_centres(NA, DIM, per, dl, dg, wl)
        s4, s5, rat, g1 = profile(c)
        del c
        err = abs(s4 - T_S4) / T_S4 + abs(s5 - T_S500) / T_S500 + abs(g1 - T_G1) / T_G1
        key = f"p{per}_dl{dl}_dg{dg}_w{wl}"
        out[key] = {"s4": s4, "s500": s5, "ratio": rat, "g1": g1, "err": err}
        if best is None or err < best[0]:
            best = (err, key)
        print(
            f"  {per:5d}   {dl:3d}   {dg:4d}  {wl:.1f} | {s4:6.2f} {s5:7.2f} "
            f"{rat:6.3f} {g1:7.2f} {err:7.3f}"
        )
    print(
        f"\nTARGET (real b=1)             | {T_S4:6.2f} {T_S500:7.2f} "
        f"{T_S500 / T_S4:6.3f} {T_G1:7.2f}"
    )
    print(f"closest by combined error: {best[1]}")
    ok = sum(1 for v in out.values() if isinstance(v, dict) and v.get("s500", 0) > 20)
    print(f"{ok} arms gave a non-collapsed s(500) -- the working region is narrow")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT}")
    print("HIERCENTRES_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
