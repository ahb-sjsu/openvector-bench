"""Do real embeddings have a preferred scale?

**Exploratory, not a registered round.** A claim about the TARGET, not about any
generator, so nothing here touches the RC-2 seal.

## The question

R19/R20 closed the round-8 lineage because real intrinsic dimension FALLS across
the ladder (26.64 -> 18.42, 25k -> 200k) and no level parameter bends a trend.
The bit-address probe (2026-08-08) then found that a self-similar cascade cannot
produce a falling ID either: truncate it and the fall is a finite-depth artifact
going as 1/(L - log_B n); remove the truncation and self-similarity forces ID
flat. Those are the same constraint twice.

If that argument is right it implies something checkable about the DATA: real
embedding geometry is **not scale-free** -- there is a characteristic scale.
Any admissible generator must then contain an explicit preferred scale rather
than a cascade, which is a hard constraint on the search space and worth
knowing before another family is designed.

## The confound this is built to avoid

G1 falling with n is NOT by itself evidence of scale-dependent geometry: TwoNN
is finite-sample biased, and the bitmap family produced a G1 that moved with n
for purely estimator reasons. So n is held FIXED and dimension is resolved
against RADIUS instead:

    s(r) = d log k / d log r(k)      (local slope of the k-NN growth curve)

For a set that is locally d-dimensional and self-similar over a range of
scales, s is CONSTANT over that range. Systematic variation of s with r is
scale-dependence, measured at one n, with no n-drift to confound it.

Two readings:

1. **Shape.** Is real's s(r) flat, and flat relative to controls measured
   through the identical estimator and radius grid? ``null_gaussian`` and a
   deep bit-cascade (L=60, self-similar by construction) are the flat
   references; any bend they share with real is an artifact of the method.
2. **Collapse.** Curves from n = 25k/50k/100k plotted against r rather than k.
   If dimension is a function of scale alone they lie on ONE curve, and G1's
   n-drift is then geometry (different n probes different r) rather than bias.
   If they do not collapse, n matters beyond scale and the bias reading stands.

Reading 2 is the one that decides whether R19/R20's premise was even sound.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.bitmap_gen import BITMAP_PARAMS, bitmap_corpus  # noqa: E402
from openvector_bench.geometry import (  # noqa: E402
    knn,
    normalize,
    null_gaussian,
    null_lowrank,
    spectrum,
)

TARGET = os.environ.get("SP_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("SP_OUT", "/home/claude/ovb_scale/scale_probe.json")
NS = json.loads(os.environ.get("SP_NS", "[25000, 50000, 100000]"))
NQ = int(os.environ.get("SP_NQ", "10000"))
KMAX = int(os.environ.get("SP_KMAX", "500"))
SEED = int(os.environ.get("SP_SEED", "11"))

# Log-spaced k grid: the radius decades we can actually resolve.
KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})


def load_real(path: str, cap: int) -> np.ndarray:
    import glob

    parts = sorted(glob.glob(os.path.join(path, "part_*.npy")))
    out, got = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        take = min(len(a), cap - got)
        out.append(np.asarray(a[:take]))
        got += take
        if got >= cap:
            break
    return np.concatenate(out)


def curve(base: np.ndarray, q: np.ndarray) -> dict:
    """r(k) and the local growth slope s(k) = dlog k / dlog r."""
    d, _ = knn(base, q, KMAX)
    r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
    lk, lr = np.log(np.array(KGRID, dtype=float)), np.log(r)
    # central differences in log-log = local correlation dimension at radius r
    s = np.gradient(lk, lr)
    # Levina-Bickel MLE at each k, same neighbour structure (cross-check with
    # different bias behaviour than the growth slope).
    lb = []
    for k in KGRID:
        tk, tj = d[:, k - 1 : k], d[:, : k - 1]
        good = (tj > 0).all(1) & (tk[:, 0] > 0)
        lb.append(
            float(
                np.median(1.0 / np.maximum(np.log(tk[good] / tj[good]).mean(1), 1e-12))
            )
        )
    return {
        "k": KGRID,
        "r": r.tolist(),
        "s": s.tolist(),
        "id_lb": lb,
        "s_min": float(np.min(s)),
        "s_max": float(np.max(s)),
        "s_ratio": float(np.max(s) / max(np.min(s), 1e-9)),
        # slope of s against log r: 0 == scale-free over the measured range
        "ds_dlogr": float(np.polyfit(lr, s, 1)[0]),
    }


def main() -> int:
    pool = max(NS) + NQ
    print(f"loading {pool} real rows from {TARGET}", flush=True)
    real = load_real(TARGET, pool)
    print(f"real {real.shape}", flush=True)

    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(real))
    real = real[perm]
    eff, _ = spectrum(normalize(real[:50000]))
    rank = max(2, int(round(eff)))
    print(f"effective rank {eff:.1f} -> null_lowrank rank {rank}", flush=True)

    bm = dict(zip([s[0] for s in BITMAP_PARAMS], [s[3] for s in BITMAP_PARAMS]))
    bm.update(
        log2_branch=1.0,
        scale_decay=1.0,
        noise=0.0,
        m0_frac=0.015,
        depth=60.0,
        dim_decay=0.0,
    )

    variants: dict[str, np.ndarray] = {
        "real": real,
        "null_gaussian": null_gaussian(real, SEED),
        "null_lowrank": null_lowrank(real, SEED, rank),
        "bitmap_L60": bitmap_corpus(bm, pool, real.shape[1], SEED),
    }

    results: dict[str, dict] = {}
    for name, x in variants.items():
        xn = normalize(x)
        q = xn[-NQ:]
        results[name] = {}
        for n in NS:
            c = curve(xn[:n], q)
            results[name][str(n)] = c
            print(
                f"{name:14s} n={n:6d} s range {c['s_min']:.1f}-{c['s_max']:.1f} "
                f"(x{c['s_ratio']:.2f}) ds/dlogr={c['ds_dlogr']:+.2f} "
                f"r {c['r'][0]:.3f}..{c['r'][-1]:.3f}",
                flush=True,
            )

    # Collapse: interpolate s onto a shared log-r grid and measure the spread
    # between the three n. Small spread == dimension is a function of scale.
    collapse: dict[str, float] = {}
    for name, per_n in results.items():
        lo = max(np.log(per_n[str(n)]["r"][0]) for n in NS)
        hi = min(np.log(per_n[str(n)]["r"][-1]) for n in NS)
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            collapse[name] = float("nan")
            continue
        grid = np.linspace(lo, hi, 24)
        curves = [
            np.interp(grid, np.log(per_n[str(n)]["r"]), per_n[str(n)]["s"]) for n in NS
        ]
        st = np.std(np.vstack(curves), axis=0)
        mn = np.mean(np.vstack(curves), axis=0)
        collapse[name] = float(np.mean(st / np.maximum(np.abs(mn), 1e-9)))
        print(
            f"collapse {name:14s} mean rel spread across n = {collapse[name]:.3f}",
            flush=True,
        )

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "ns": NS,
                    "nq": NQ,
                    "kmax": KMAX,
                    "kgrid": KGRID,
                    "seed": SEED,
                    "target": TARGET,
                },
                "results": results,
                "collapse": collapse,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("SCALE_PROBE_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
