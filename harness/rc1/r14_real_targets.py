"""Real targets in the budget-invariant forms (PREREG_ROUND14 stage 0).

The amended admission rule evaluates G6 as ``attractiveness_skew`` rather
than raw ``s_k``, and the round-11 reference stores only summary statistics,
so the invariant targets cannot be recovered from it by re-expression the way
the count targets were. They have to be measured once, on real data.

Measured at CONSTANT rho across the ladder, because the whole point of the
invariant forms is that a slope then belongs to the corpus rather than to the
budget. Sealed rows are excluded by the same rule the reference build uses.
Nothing is scored and no candidate appears.

Output is the target file round 14's query-model search fits against.

Env: R14T_OUT, R14T_REAL_DIR, R14T_NS, R14T_RHO, R14T_KS, R14T_SEEDS.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.hubness import (  # noqa: E402
    attractiveness_skew,
    hub_excess,
    rho,
    tail_excess,
)

OUT = os.environ.get("R14T_OUT", "results/r14_real_invariant_targets.json")
REAL_DIR = os.environ.get("R14T_REAL_DIR", "/archive/tqp_real/wiki1024")
NS = json.loads(os.environ.get("R14T_NS", "[12500, 25000, 50000]"))
RHO = float(os.environ.get("R14T_RHO", "4.0"))
KS = json.loads(os.environ.get("R14T_KS", "[10, 30]"))
SEEDS = json.loads(os.environ.get("R14T_SEEDS", "[0, 1, 2]"))


def log(m: str) -> None:
    print(m, flush=True)


def sealed(i: int) -> bool:
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def load_pool(n_rows: int, rng) -> np.ndarray:
    """Rows sampled across parts, sealed rows excluded.

    Across parts rather than from the head, because the corpus's row order is
    topically clustered and a head slice is a different query marginal.
    """
    parts = sorted(glob.glob(os.path.join(REAL_DIR, "part_*.npy")))
    per = max(1, n_rows // len(parts))
    out, taken = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        idx = np.sort(rng.choice(len(a), size=min(per * 2, len(a)), replace=False))
        keep = np.array([i for i in idx if not sealed(int(i))], dtype=np.int64)
        if len(keep):
            out.append(np.asarray(a[keep], dtype=np.float32))
            taken += len(keep)
        if taken >= n_rows:
            break
    return np.concatenate(out)[:n_rows]


def main() -> None:
    log("R14 REAL TARGETS — invariant forms at constant rho")
    n_max = max(NS)
    rng = np.random.default_rng(20260807)
    pool = load_pool(int(n_max * 1.6), rng)
    base_pool, q_pool = pool[:n_max], pool[n_max:]
    log(f"base pool {base_pool.shape}, query pool {q_pool.shape}")

    cells = []
    for k in KS:
        for n in NS:
            nq = min(len(q_pool), max(50, int(round(RHO * n / k))))
            for sd in SEEDS:
                r = np.random.default_rng(10_000 * sd + n + k)
                b = normalize(base_pool[r.choice(len(base_pool), n, replace=False)])
                q = normalize(q_pool[r.choice(len(q_pool), nq, replace=False)])
                _, idx = knn(b, q, k)
                c = np.bincount(idx[:, :k].ravel(), minlength=n).astype(float)
                cells.append(
                    {
                        "k": k,
                        "n": n,
                        "nq": nq,
                        "seed": sd,
                        "rho": rho(nq, k, n),
                        "attractiveness_skew": attractiveness_skew(c),
                        "tail_excess_1pct": tail_excess(c, n, 0.01),
                        "hub_excess": hub_excess(c.max(), c.mean(), n),
                        "s_k_raw": float(
                            ((c - c.mean()) ** 3).mean() / max(c.std() ** 3, 1e-12)
                        ),
                        "zero_frac": float((c == 0).mean()),
                    }
                )
            sel = [x for x in cells if x["k"] == k and x["n"] == n]
            log(
                f"  k={k:3d} n={n:6d} rho={sel[0]['rho']:.2f} "
                f"attr_skew={np.nanmean([x['attractiveness_skew'] for x in sel]):.3f} "
                f"(sd {np.nanstd([x['attractiveness_skew'] for x in sel]):.3f})  "
                f"tail_exc={np.mean([x['tail_excess_1pct'] for x in sel]):.3f}"
            )

    targets = {}
    for k in KS:
        for n in NS:
            sel = [x for x in cells if x["k"] == k and x["n"] == n]
            targets[f"k{k}_n{n}"] = {
                "rho": sel[0]["rho"],
                "attractiveness_skew": {
                    "mean": float(np.nanmean([x["attractiveness_skew"] for x in sel])),
                    "sd": float(np.nanstd([x["attractiveness_skew"] for x in sel])),
                },
                "tail_excess_1pct": {
                    "mean": float(np.mean([x["tail_excess_1pct"] for x in sel])),
                    "sd": float(np.std([x["tail_excess_1pct"] for x in sel])),
                },
                "hub_excess": {
                    "mean": float(np.mean([x["hub_excess"] for x in sel])),
                    "sd": float(np.std([x["hub_excess"] for x in sel])),
                },
            }

    def slope(xs, ys):
        x = np.log10(np.asarray(xs, float))
        y = np.asarray(ys, float)
        ok = np.isfinite(y)
        return float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float("nan")

    slopes = {}
    for k in KS:
        for stat in ("attractiveness_skew", "tail_excess_1pct", "hub_excess"):
            slopes[f"{stat}_k{k}"] = slope(
                NS, [targets[f"k{k}_n{n}"][stat]["mean"] for n in NS]
            )
    log("\nladder slopes at constant rho (corpus, not budget):")
    for name, v in slopes.items():
        log(f"  {name:28s} {v:+.4f}/decade")

    out = {
        "meta": {
            "prereg": "results/PREREG_ROUND14.md stage 0 — invariant targets",
            "real": REAL_DIR,
            "rho_held_constant": RHO,
            "ns": NS,
            "ks": KS,
            "seeds": SEEDS,
            "sealed_rows": "excluded (blake2b(i) % 4 == 3)",
            "note": "targets only; nothing scored, no candidate measured",
        },
        "cells": cells,
        "targets": targets,
        "ladder_slopes": slopes,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R14_REAL_TARGETS_DONE")


if __name__ == "__main__":
    main()
