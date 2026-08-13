"""Two checks before building anything else on R27.

`R27_DUPLICATE_STRUCTURE.md` is the first construction in twenty-two rounds to
match the profile trend (+0.995 against +0.978). It also rests on a single seed
at reduced rungs, and it carries an unresolved prerequisite. Building three more
experiments on that is how the R19b -> R20 waste happened, so both are settled
here first.

## Check 1 — random access (a prerequisite, not a detail)

`DISTRIBUTION.md`'s entire architecture needs row *i* emitted cheaply from *i*
alone. Recursive duplication is exactly the row-to-row dependence that puts
that in doubt: if row *i* copies an earlier row, emitting it means walking its
ancestry to a root.

Define `source(i) = splitmix64(i) mod i` for non-root rows. That builds a
**random recursive tree**, whose expected depth is O(log n) — but "expected
O(log n)" is a claim about an idealisation, and what matters is the actual
depth distribution at 1e12, including the tail. A p99 of 28 is fine; a p99 of
5000 is not.

Cost model, measured rather than assumed: emitting one row costs
`depth` hash steps plus `depth * dim` accumulate operations, against
`bitmap_gen`'s ~1200 coordinate writes. The bound that matters is ~10 MB/s/core
— below that, regeneration is slower than fetching bytes and
`DISTRIBUTION.md` §3's source ordering inverts (the failure that killed the
encoder route).

## Check 2 — does R27 replicate?

The two best arms re-run across several seeds. R27 reported one seed each. If
the trend match is a fluke of seed 21 it should show up immediately as a wide
spread; the registered block-to-block sd for real's own trend is 0.099, so
anything comparable is fine and anything much larger is not.

Env: DF_SEEDS, DF_NS, DF_NQ, DF_DIM, DF_OUT, DF_SAMPLES.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("DF_THREADS", "6"))

from openvector_bench.bitmap_gen import _U64, _sm64  # noqa: E402
from openvector_bench.geometry import (  # noqa: E402
    PROFILE_KGRID,
    id_twonn,
    knn,
    normalize,
    profile_ratio,
)

DIM = int(os.environ.get("DF_DIM", "1024"))
NS = json.loads(os.environ.get("DF_NS", "[5000, 10000, 20000]"))
NQ = int(os.environ.get("DF_NQ", "2000"))
SEEDS = json.loads(os.environ.get("DF_SEEDS", "[21, 22, 23, 24]"))
SAMPLES = int(os.environ.get("DF_SAMPLES", "20000"))
OUT = os.environ.get("DF_OUT", "results/dup_feasibility.json")
TARGETS = os.environ.get("DF_TARGETS", "results/small_rung_targets.json")


# --------------------------------------------------------------------------- #
# Check 1: ancestry depth of the hash-defined recursive tree                   #
# --------------------------------------------------------------------------- #
def source_of(i: np.ndarray, n_roots: int) -> np.ndarray:
    """source(i) = splitmix64(i) mod i, or -1 for a root. Pure function of i."""
    out = np.full(len(i), -1, dtype=np.int64)
    nonroot = i >= n_roots
    if nonroot.any():
        idx = i[nonroot].astype(np.uint64)
        out[nonroot] = (_sm64(idx ^ _U64(0x5DEECE66D)) % idx).astype(np.int64)
    return out


def depth_stats(n_total: int, n_roots: int, samples: int) -> dict:
    rng = np.random.default_rng(3)
    cur = rng.integers(n_roots, n_total, size=samples).astype(np.int64)
    depth = np.zeros(samples, dtype=np.int64)
    alive = np.ones(samples, dtype=bool)
    steps = 0
    while alive.any() and steps < 10_000:
        s = source_of(cur[alive], n_roots)
        depth[alive] += 1
        cur[alive] = s
        alive[alive] = s >= n_roots
        steps += 1
    return {
        "n_total": int(n_total),
        "mean": float(depth.mean()),
        "p50": float(np.percentile(depth, 50)),
        "p99": float(np.percentile(depth, 99)),
        "max": int(depth.max()),
        "ln_n": float(np.log(n_total)),
    }


# --------------------------------------------------------------------------- #
# Check 2: replication of R27's best arms                                      #
# --------------------------------------------------------------------------- #
def build(n: int, dim: int, rng, base_dim: int, frac: float, sigma: float):
    n_base = max(1, int(round(n * (1.0 - frac))))
    basis = np.linalg.qr(rng.standard_normal((dim, base_dim)))[0].astype(np.float32)
    x = np.empty((n, dim), dtype=np.float32)
    x[:n_base] = rng.standard_normal((n_base, base_dim)).astype(np.float32) @ basis.T
    filled, block = n_base, max(256, n_base // 8)
    while filled < n:
        take = min(block, n - filled)
        src = rng.integers(0, filled, take)
        x[filled : filled + take] = x[src] + np.float32(sigma) * rng.standard_normal(
            (take, dim)
        ).astype(np.float32)
        filled += take
    return x


def arm(name: str, base_dim: int, frac: float, sigma: float) -> dict:
    trends, g1means, per_seed = [], [], []
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        nmax = max(NS)
        x = normalize(build(nmax + NQ, DIM, rng, base_dim, frac, sigma))
        q = x[nmax:]
        ratios, g1s = [], []
        for n in NS:
            r2 = np.random.default_rng(sd * 7 + n)
            bi = r2.choice(nmax, size=n, replace=False)
            d, _ = knn(x[bi], q, max(PROFILE_KGRID))
            ratios.append(profile_ratio(d))
            g1s.append(float(id_twonn(d)))
        tr = float(np.polyfit(np.log(NS), ratios, 1)[0])
        trends.append(tr)
        g1means.append(float(np.mean(g1s)))
        per_seed.append({"seed": sd, "ratios": ratios, "trend": tr, "g1": g1s})
        print(
            f"  {name} seed {sd}: ratios {[round(r,3) for r in ratios]} "
            f"trend {tr:+.3f} G1 {[round(g,1) for g in g1s]}",
            flush=True,
        )
    out = {
        "per_seed": per_seed,
        "trend_mean": float(np.mean(trends)),
        "trend_sd": float(np.std(trends, ddof=1)) if len(trends) > 1 else 0.0,
        "g1_mean": float(np.mean(g1means)),
    }
    print(
        f"  -> {name}: trend {out['trend_mean']:+.3f} +/- {out['trend_sd']:.3f}, "
        f"mean G1 {out['g1_mean']:.1f}",
        flush=True,
    )
    return out


def main() -> int:
    res: dict = {}

    print("=== Check 1: ancestry depth of source(i) = hash(i) mod i ===", flush=True)
    depths = {}
    for n_total in (10**6, 10**9, 10**12):
        d = depth_stats(n_total, n_roots=1000, samples=SAMPLES)
        depths[str(n_total)] = d
        print(
            f"  n=1e{int(np.log10(n_total)):2d}  mean depth {d['mean']:6.2f}  "
            f"p50 {d['p50']:4.0f}  p99 {d['p99']:5.0f}  max {d['max']:5d}  "
            f"(ln n = {d['ln_n']:.1f})",
            flush=True,
        )
    res["depth"] = depths

    d12 = depths[str(10**12)]
    ops = d12["p99"] * DIM  # accumulate ops per row at the tail
    bmp = 1200  # bitmap_gen coordinate writes per row
    rows_per_s = 1e9 / max(ops, 1)  # ~1e9 simple ops/s/core
    mb_s = rows_per_s * DIM * 4 / 1e6
    print(
        f"\n  cost at p99 depth: {ops:.0f} ops/row vs bitmap_gen ~{bmp} "
        f"-> ~{rows_per_s:,.0f} rows/s/core = {mb_s:.0f} MB/s/core",
        flush=True,
    )
    print(
        "  bound is ~10 MB/s/core (below it, fetching beats regeneration)", flush=True
    )
    ok = mb_s > 10.0
    print(f"  RANDOM ACCESS: {'VIABLE' if ok else 'NOT VIABLE'}", flush=True)
    res["random_access_viable"] = bool(ok)
    res["mb_per_s_per_core"] = float(mb_s)

    print("\n=== Check 2: does R27 replicate across seeds? ===", flush=True)
    tg = json.load(open(TARGETS))
    t_ratios = [tg[str(n)]["ratio"] for n in NS if str(n) in tg]
    t_trend = float(np.polyfit(np.log([n for n in NS if str(n) in tg]), t_ratios, 1)[0])
    t_g1 = float(np.mean([tg[str(n)]["g1"] for n in NS if str(n) in tg]))
    print(
        f"target trend {t_trend:+.3f}, mean G1 {t_g1:.1f} "
        f"(real's own block-to-block trend sd is 0.099)\n",
        flush=True,
    )
    t0 = time.time()
    res["arms"] = {
        "lowdim20_f0.6_s0.15": arm("lowdim20 f0.6 s0.15", 20, 0.6, 0.15),
        "lowdim40_f0.6_s0.3": arm("lowdim40 f0.6 s0.3", 40, 0.6, 0.3),
    }
    print(f"\n({time.time()-t0:.0f}s)", flush=True)
    res["target_trend"] = t_trend
    res["target_g1"] = t_g1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("DUP_FEASIBILITY_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
