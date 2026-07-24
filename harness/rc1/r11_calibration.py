"""Round-11 PRE-FREEZE calibration sweep (results/PREREG_ROUND11.md, draft).

Maps the ``local_centers`` dial (m, p, n_shell) -> (S_k count skew, count_max,
Robin Hood index) of the battery-A reverse-neighbour count distribution, AT the
round-10 pool (base pool 420k = max(N_GRID) + 220k) AND on grid-subsampled
ladders n in N_GRID drawn from that pool with the grid's own sampling operator
(``measure``'s rng convention) — the mandatory pool+subsample rule. The
prereg's failure clause is exactly this transfer: if ladder thinning takes the
planted counts out of band, that is reported as the sampling-operator lesson
recurring, not tuned away.

One underlying round-10 instance (fit_v10 operating point, nonparametric
spectral target installed) is generated ONCE and re-overlaid per cell — the
primitive is a post-hoc overlay by construction, so the sweep isolates the
dial. Real-corpus reference counts (step-1 sealed filter + uniform-holdout
conventions) are measured under the same protocol. Calibration only: no gates
are scored, the prereg stays unfrozen, no admission runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np

from openvector_bench import geometry as G
from openvector_bench.generator_search import (
    QUERY_FRAC,
    hier_dupq_corpus,
    local_centers,
    set_spectrum_target,
)

R11 = os.environ.get("R11_DIR", "/home/claude/r11")
PARAMS_PATH = os.environ.get("R11_PARAMS", f"{R11}/fit_v10_result.json")
SPECTRUM = os.environ.get("R11_SPECTRUM", f"{R11}/spectrum_target_wiki1024.json")
TARGET = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("R11_OUT", f"{R11}/r11_calibration.json")

POOL = max(G.N_GRID) + 220_000  # step-3 pool: thinning factors match the grid
M_ROWS = int(round(POOL / (1.0 - QUERY_FRAC)))
HOLD = min(G.N_QUERY * 2, POOL // 10)
DIM, SEED = 1024, 0
MASS_CAP = 0.10  # overlay may claim at most 10% of the pool's base rows
RADIUS, CENTER_JIT = 0.15, 0.05  # spec defaults; the sweep dials (m, p, n_shell)
SUBS = (0, 1)  # ladder subsample draws; the pool scope is a single structure
GRID = [(m, p, ns) for m in (4, 16, 64) for p in (2, 8, 32) for ns in (512, 2048, 8192)]

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - _T0:7.0f}s] {msg}", flush=True)


def sealed(i: int) -> bool:
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def uniform_holdout_mask(n: int, hold: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mask = np.zeros(n, dtype=bool)
    mask[rng.choice(n, size=hold, replace=False)] = True
    return mask


def count_stats(idx: np.ndarray, n_rows: int, k: int, pmask: np.ndarray | None) -> dict:
    """The three dial responses of PREREG_ROUND11 for one (structure, k)."""
    counts = np.bincount(idx[:, :k].ravel(), minlength=n_rows).astype(np.float64)
    mean, s = counts.mean(), counts.std()
    out = {
        "s_k": float(((counts - mean) ** 3).mean() / max(s**3, 1e-12)),
        "count_max": int(counts.max()),
        "rh": float(0.5 * np.abs(counts - mean).sum() / max(counts.sum(), 1e-12)),
        "count_mean": float(mean),
    }
    if pmask is not None and pmask.any():
        pc = counts[pmask]
        out |= {
            "planted_rows": int(pmask.sum()),
            "planted_max": int(pc.max()),
            "planted_mean": float(pc.mean()),
        }
    return out


def measure_counts(
    name: str, base_pool: np.ndarray, q_pool: np.ndarray, planted=None
) -> list[dict]:
    """Pool scope + grid-subsampled ladders, all under measure()'s operator."""
    rows: list[dict] = []
    scopes = [("pool", len(base_pool), (0,))] + [
        (f"n{n}", n, SUBS) for n in G.N_GRID if n <= len(base_pool)
    ]
    for scope, n, subs in scopes:
        for sub in subs:
            rng = np.random.default_rng(10_000 * sub + n)
            bi = rng.choice(len(base_pool), size=n, replace=False)
            base = G.normalize(base_pool[bi])
            qi = rng.choice(
                len(q_pool), size=min(G.N_QUERY, len(q_pool)), replace=False
            )
            _, idx = G.knn(base, G.normalize(q_pool[qi]), G.KMAX)
            pmask = np.isin(bi, planted) if planted is not None else None
            for k in G.K_GRID:
                rows.append(
                    {"corpus": name, "scope": scope, "n": n, "sub": sub, "k": k}
                    | count_stats(idx, n, k, pmask)
                )
        log(f"{name:24s} {scope:8s} done ({len(rows)} rows)")
    return rows


def main() -> None:
    set_spectrum_target(SPECTRUM)
    params = json.load(open(PARAMS_PATH, encoding="utf-8"))["params"]
    log(f"grid n={G.N_GRID} k={G.K_GRID} pool={POOL} instance={M_ROWS}")

    log("generating the round-10 pool instance (fit_v10 point, once)")
    x0 = hier_dupq_corpus(params, M_ROWS, DIM, SEED)
    base_blk = x0[: M_ROWS - int(round(M_ROWS * QUERY_FRAC))]
    hmask = uniform_holdout_mask(len(base_blk), HOLD, seed=70)  # step-3 convention
    log(f"instance {x0.shape}; base block {base_blk.shape}; holdout {HOLD}")

    cells: list[dict] = []
    meta = {
        "params_path": PARAMS_PATH,
        "pool": POOL,
        "instance_rows": M_ROWS,
        "dim": DIM,
        "seed": SEED,
        "radius": RADIUS,
        "center_jit": CENTER_JIT,
        "mass_cap": MASS_CAP,
        "skipped": [],
    }

    def flush() -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "cells": cells}, f, indent=1)

    # Baseline: the round-10 instance with the primitive OFF.
    qa, bp = base_blk[hmask], base_blk[~hmask]
    for row in measure_counts("r10_baseline", bp, qa):
        cells.append({"m": 0, "p": 0, "n_shell": 0} | row)
    flush()

    for m, p, ns in GRID:
        total = m * (p + ns)
        if total > MASS_CAP * len(base_blk):
            meta["skipped"].append({"m": m, "p": p, "n_shell": ns, "rows": total})
            log(f"skip m={m} p={p} n_shell={ns}: {total} rows > mass cap")
            continue
        y, planted = local_centers(
            base_blk,
            len(base_blk),
            m=m,
            n_planted=p,
            n_shell=ns,
            radius=RADIUS,
            center_jit=CENTER_JIT,
            rng=np.random.default_rng(777_000 + SEED),
            return_rows=True,
        )
        pmask_blk = np.zeros(len(base_blk), dtype=bool)
        pmask_blk[planted] = True
        qa, bp = y[hmask], y[~hmask]
        planted_pool = np.flatnonzero(pmask_blk[~hmask])
        name = f"lc_m{m}_p{p}_s{ns}"
        log(
            f"{name}: overlay {total} rows, {len(planted_pool)}/{len(planted)} "
            f"planted rows survive the battery-A holdout"
        )
        for row in measure_counts(name, bp, qa, planted=planted_pool):
            cells.append({"m": m, "p": p, "n_shell": ns} | row)
        flush()

    # Real-corpus reference under the same count protocol (step-1 conventions:
    # sealed rows excluded, uniform battery-A holdout, seed 7).
    del x0, base_blk, y, qa, bp
    corpus, _ = G.load_target(TARGET, cap=max(G.N_GRID) * 3)
    keep = np.fromiter((i for i in range(len(corpus)) if not sealed(i)), dtype=np.int64)
    corpus = np.asarray(corpus[keep])
    rmask = uniform_holdout_mask(len(corpus), min(G.N_QUERY * 2, len(corpus) // 10), 7)
    log(f"real non-sealed pool {corpus.shape}")
    for row in measure_counts("real", corpus[~rmask], corpus[rmask]):
        cells.append({"m": None, "p": None, "n_shell": None} | row)
    flush()

    log(f"wrote {OUT} ({len(cells)} rows)")
    print("R11_CALIBRATION_DONE", flush=True)


if __name__ == "__main__":
    main()
