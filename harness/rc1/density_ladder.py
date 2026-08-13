"""The registered density ladder — `PROFILE.md` §3b, target values.

Row count is held FIXED while the pool varies. This is the only way to separate
the two effects the §3 rung ladder confounds: along that ladder a rung of n rows
drawn from a fixed 600k pool sits at density `n/600k`, so density and row count
move together and the registered `trend` is their sum.

Four independent contiguous 600k blocks at different corpus offsets (the `R24`
design), so the quoted uncertainty is real block-to-block variance rather than a
single-draw point estimate.

**The holdout is drawn from within each pool.** Drawing it once from the largest
pool and slicing the base leaves the queries spanning the whole corpus while the
base spans only its head — the non-exchangeable split of `R23`, which inflates
G1 roughly 2x at the smallest pool and does so monotonically in pool size. The
artifact therefore reads as a clean density trend; it was committed and caught
during this measurement (`R29`).

Env: DL_N, DL_NQ, DL_POOLS, DL_OFFSETS, DL_PARTS, DL_OUT.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("DL_THREADS", "6"))

from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

N_FIX = int(os.environ.get("DL_N", "25000"))
NQ = int(os.environ.get("DL_NQ", "10000"))
POOLS = json.loads(os.environ.get("DL_POOLS", "[50000,100000,200000,400000,600000]"))
OFFSETS = json.loads(os.environ.get("DL_OFFSETS", "[0,10000000,20000000,30000000]"))
PARTS = os.environ.get("DL_PARTS", "/archive/tqp_real/wiki1024/part_*.npy")
OUT = os.environ.get("DL_OUT", "results/density_ladder.json")


def main() -> int:
    parts = sorted(glob.glob(PARTS))
    if not parts:
        print(f"no parts matched {PARTS}", file=sys.stderr)
        return 1
    sizes = [np.load(p, mmap_mode="r").shape[0] for p in parts]
    cum = np.cumsum([0] + sizes)
    print("corpus rows:", cum[-1], flush=True)

    def load(off: int, cnt: int) -> np.ndarray:
        out, need, pos = [], cnt, off
        for i, p in enumerate(parts):
            s, e = cum[i], cum[i + 1]
            if e <= pos or need <= 0:
                continue
            a = np.load(p, mmap_mode="r")
            lo = max(0, pos - s)
            take = min(int(e - max(pos, s)), need)
            out.append(np.asarray(a[lo : lo + take]))
            need -= take
            pos += take
            if need <= 0:
                break
        return normalize(np.concatenate(out))

    blk = max(POOLS)
    blocks: dict[str, dict] = {}
    for bi, off in enumerate(OFFSETS):
        if off + blk > cum[-1]:
            print(f"block {bi} offset {off} exceeds corpus; skipping", flush=True)
            continue
        t0 = time.time()
        full = load(off, blk)
        rec: dict[str, dict] = {}
        for pool_n in POOLS:
            pool = full[:pool_n]
            hr = np.random.default_rng(7)
            m = np.zeros(pool_n, dtype=bool)
            m[hr.choice(pool_n, NQ, replace=False)] = True
            q, body = pool[m], pool[~m]
            r2 = np.random.default_rng(10_000 + N_FIX)
            bi_ = r2.choice(len(body), N_FIX, replace=False)
            d, _ = knn(body[bi_], q, max(PROFILE_KGRID))
            mu = d[:, 1] / np.maximum(d[:, 0], 1e-12)
            rec[str(pool_n)] = {
                "density": N_FIX / pool_n,
                "ratio": profile_ratio(d),
                "g1": float(id_twonn(d)),
                "mu_med": float(np.median(mu)),
                "mu_frac": float((mu > 1.5).mean()),
            }
            r_ = rec[str(pool_n)]
            print(
                f"  block{bi} off {off:9d} pool {pool_n:6d} "
                f"dens {r_['density']:.4f}  ratio {r_['ratio']:.3f}  "
                f"G1 {r_['g1']:6.2f}  mu {r_['mu_med']:.4f}",
                flush=True,
            )
        blocks[str(off)] = rec
        print(f"block {bi} done ({time.time() - t0:.0f}s)", flush=True)
        del full

    agg: dict[str, dict] = {}
    for pool_n in POOLS:
        k = str(pool_n)
        rs = [blocks[b][k]["ratio"] for b in blocks]
        gs = [blocks[b][k]["g1"] for b in blocks]
        ms = [blocks[b][k]["mu_med"] for b in blocks]
        agg[k] = {
            "density": N_FIX / pool_n,
            "ratio": float(np.mean(rs)),
            "ratio_sd": float(np.std(rs, ddof=1)),
            "g1": float(np.mean(gs)),
            "g1_sd": float(np.std(gs, ddof=1)),
            "mu_med": float(np.mean(ms)),
        }

    # Fixed-endpoint contrasts. NOT a fitted slope: the response is strongly
    # convex, so a slope would depend on which pools were chosen -- the span
    # dependence that disqualified `beta` (PROFILE.md §1).
    lo, hi = str(max(POOLS)), str(min(POOLS))
    rspan = [blocks[b][hi]["ratio"] - blocks[b][lo]["ratio"] for b in blocks]
    gspan = [float(np.log(blocks[b][hi]["g1"] / blocks[b][lo]["g1"])) for b in blocks]
    res = {
        "n_fixed": N_FIX,
        "nq": NQ,
        "pools": POOLS,
        "offsets": OFFSETS,
        "blocks": blocks,
        "per_density": agg,
        "ratio_span": {
            "mean": float(np.mean(rspan)),
            "sd": float(np.std(rspan, ddof=1)),
        },
        "logg1_span": {
            "mean": float(np.mean(gspan)),
            "sd": float(np.std(gspan, ddof=1)),
        },
    }

    print("\nPER-DENSITY (mean +- sd over blocks)", flush=True)
    for pool_n in POOLS:
        a = agg[str(pool_n)]
        print(
            f"  dens {a['density']:.4f}  ratio {a['ratio']:.3f} +- "
            f"{a['ratio_sd']:.3f}   G1 {a['g1']:6.2f} +- {a['g1_sd']:.2f}",
            flush=True,
        )
    print(
        f"\nratio span = {res['ratio_span']['mean']:+.3f} +- "
        f"{res['ratio_span']['sd']:.3f}",
        flush=True,
    )
    print(
        f"logG1 span = {res['logg1_span']['mean']:+.3f} +- "
        f"{res['logg1_span']['sd']:.3f}",
        flush=True,
    )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("DENSITY_LADDER_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
