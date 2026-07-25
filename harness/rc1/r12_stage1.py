"""Round-12 PRE-FREEZE stage 1: mechanism anatomy sweeps (PREREG_ROUND12, draft).

Two independent sweeps of the decoupled concentration mechanisms, under the
r11v2 instruments and against the committed 5-draw real reference
(results/r11v2_real_ref.json — the scoring instrument of ROUND11_PREFREEZE):

  Sweep G — the GRADIENT mechanism (grad_decay, grad_span, grad_shape) mapped
    to (G1, G3, G5) with the old concentration architecture REMOVED
    (cloud_mass = dup_mass = 0). Must be COUNT-QUIET: S_k within draw noise
    of the mechanism-off control at every ladder cell.
  Sweep O — the RENEWAL occupancy law (occ_tail, dens_span at occ_mix = 1)
    mapped to (S_k, count_max, Δslope). Must be ID-QUIET: G1 within draw
    noise of the control.

The architecture-removed baseline ({} overrides) is the shared control and is
measured first. Ladder scopes use measure-style grid subsampling (the SAME
operator and seeds as r11v2_stage1: rng(10_000*sub + n)), so ratios against
the real reference are cell-aligned. Δslope per k = d log10(S_k)/d log10(n)
minus real's, fit across the ladder means.

Calibration only: nothing here freezes the prereg, no gates are scored, no
admission runs, the sealed rows stay untouched. Reduced-pool/ladder screening
runs (env overrides) are disclosed in the output meta and are not calibration
evidence — the freeze-candidate sweep runs the full grid ladder on NRP.

Env: R12_DIR (out dir), R12_PARAMS (fitted params JSON; default the committed
fit_v9_result.json — fit_v10 lives in pod scratch and its result file is not
committed), R12_REAL (real reference), R12_OUT, R12_NS, R12_SUBS, R12_POOL,
R12_GRID_G / R12_GRID_O (JSON grids).
"""

from __future__ import annotations

import json
import os
import time

import numpy as np

from openvector_bench import geometry as G
from openvector_bench.generator_search import (
    QUERY_FRAC,
    hier_r12_corpus,
    set_spectrum_target,
)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R12 = os.environ.get("R12_DIR", os.path.join(REPO, "results"))
PARAMS_PATH = os.environ.get(
    "R12_PARAMS", os.path.join(REPO, "results", "fit_v9_result.json")
)
SPECTRUM = os.environ.get(
    "R12_SPECTRUM", os.path.join(REPO, "results", "spectrum_target_wiki1024.json")
)
REAL_REF = os.environ.get(
    "R12_REAL", os.path.join(REPO, "results", "r11v2_real_ref.json")
)
OUT = os.environ.get("R12_OUT", os.path.join(R12, "r12_stage1.json"))

NS = tuple(
    int(s) for s in os.environ.get("R12_NS", ",".join(map(str, G.N_GRID))).split(",")
)
SUBS = tuple(int(s) for s in os.environ.get("R12_SUBS", "0,1").split(","))
POOL = int(os.environ.get("R12_POOL", max(NS) + 220_000))
M_ROWS = int(round(POOL / (1.0 - QUERY_FRAC)))
HOLD = min(G.N_QUERY * 2, POOL // 10)
DIM, SEED = 1024, 0

# The round-12 operating point: the old concentration architecture is removed
# by configuration — a REPLACEMENT at the family level (PREREG_ROUND12).
ARCH_OFF = {"cloud_mass": 0.0, "dup_mass": 0.0}

GRID_G: list[dict[str, float]] = [
    {},  # architecture-removed control (both mechanisms off) — measured once
    {"grad_decay": 0.2},
    {"grad_decay": 0.4},
    {"grad_decay": 0.6},
    {"grad_span": 6.0},
    {"grad_span": 15.0},
    {"grad_decay": 0.4, "grad_span": 10.0},
    {"grad_decay": 0.4, "grad_span": 10.0, "grad_shape": 2.0},
]
GRID_O: list[dict[str, float]] = [
    {"occ_mix": 1.0, "occ_tail": 1.3},
    {"occ_mix": 1.0, "occ_tail": 1.8},
    {"occ_mix": 1.0, "occ_tail": 2.5},
    {"occ_mix": 1.0, "occ_tail": 1.8, "dens_span": 0.3},
    {"occ_mix": 1.0, "occ_tail": 1.8, "dens_span": 0.6},
    {"occ_mix": 1.0, "occ_tail": 1.3, "dens_span": 0.6},
]
# Round-12 v2 (P-A'): the cascade sweep — drift is the target statistic.
# First entry is the sweep's own control (level dial on, cascade off).
GRID_C: list[dict[str, float]] = [
    {"grad_decay": 0.5},
    {"grad_decay": 0.5, "cascade_frac": 0.3},
    {"grad_decay": 0.5, "cascade_frac": 0.5},
    {"grad_decay": 0.5, "cascade_frac": 0.7},
    {"grad_decay": 0.5, "cascade_frac": 0.5, "cascade_smin": 0.005},
    {"grad_decay": 0.5, "cascade_frac": 0.5, "cascade_smin": 0.06},
    {"grad_decay": 0.5, "cascade_frac": 0.5, "cascade_alpha": 1.6},
    {"cascade_frac": 0.5},  # cascade alone — drift isolation without the dial
]
if os.environ.get("R12_GRID_G"):
    GRID_G = json.loads(os.environ["R12_GRID_G"])
if os.environ.get("R12_GRID_O"):
    GRID_O = json.loads(os.environ["R12_GRID_O"])
if os.environ.get("R12_GRID_C"):
    GRID_C = json.loads(os.environ["R12_GRID_C"])

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - _T0:7.0f}s] {msg}", flush=True)


def uniform_holdout_mask(n: int, hold: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mask = np.zeros(n, dtype=bool)
    mask[rng.choice(n, size=hold, replace=False)] = True
    return mask


def fast_spectrum(x: np.ndarray) -> tuple[float, int]:
    xc = (x - x.mean(0, keepdims=True)).astype(np.float64)
    lam = np.linalg.eigvalsh((xc.T @ xc) / max(len(xc) - 1, 1))[::-1]
    lam = lam[lam > 0]
    frac = np.cumsum(lam) / lam.sum()
    return (
        float(lam.sum() ** 2 / (lam**2).sum()),
        int(np.searchsorted(frac, 0.90) + 1),
    )


def count_stats(idx: np.ndarray, n_rows: int, k: int) -> dict:
    counts = np.bincount(idx[:, :k].ravel(), minlength=n_rows).astype(np.float64)
    mean, s = counts.mean(), counts.std()
    return {
        "s_k": float(((counts - mean) ** 3).mean() / max(s**3, 1e-12)),
        "count_max": int(counts.max()),
        "rh": float(0.5 * np.abs(counts - mean).sum() / max(counts.sum(), 1e-12)),
        "count_mean": float(mean),
    }


def measure_counts(name: str, base_pool: np.ndarray, q_pool: np.ndarray) -> list[dict]:
    """Ladder scopes under the r11v2 subsample operator (rng 10_000*sub + n)."""
    rows: list[dict] = []
    for n in (nn for nn in NS if nn <= len(base_pool)):
        for sub in SUBS:
            rng = np.random.default_rng(10_000 * sub + n)
            bi = rng.choice(len(base_pool), size=n, replace=False)
            base = G.normalize(base_pool[bi])
            qi = rng.choice(
                len(q_pool), size=min(G.N_QUERY, len(q_pool)), replace=False
            )
            q = G.normalize(q_pool[qi])
            d, idx = G.knn(base, q, G.KMAX)
            eff, d90 = fast_spectrum(base[: min(50_000, len(base))])
            g1 = G.id_twonn(d)
            for k in G.K_GRID:
                rows.append(
                    {"corpus": name, "scope": f"n{n}", "n": n, "sub": sub, "k": k}
                    | count_stats(idx, n, k)
                    | {
                        "g1_id_twonn": g1,
                        "g3_eff_rank": eff,
                        "g4_dims90": d90,
                        "g5_relative_contrast": G.relative_contrast(d, base, q, k),
                    }
                )
        log(f"{name:28s} n{n} done ({len(rows)} rows)")
    return rows


def _mean_by_nk(rows: list[dict], name: str, field: str) -> dict:
    """{(n, k): mean over subs} for one corpus and field."""
    acc: dict = {}
    for r in rows:
        if r["corpus"] != name:
            continue
        acc.setdefault((r["n"], r["k"]), []).append(r[field])
    return {key: float(np.mean(v)) for key, v in acc.items()}


def slope_per_k(means: dict, k: int) -> float | None:
    """d log10(field) / d log10(n) across the ladder, least squares."""
    pts = sorted((n, v) for (n, kk), v in means.items() if kk == k and v > 0)
    if len(pts) < 2:
        return None
    ln = np.log10([p[0] for p in pts])
    lv = np.log10([p[1] for p in pts])
    return float(np.polyfit(ln, lv, 1)[0])


def summarize(rows: list[dict], name: str, control: str, real: dict) -> dict:
    """Per-setting summary: ratios to real and to the control, Δslopes."""
    out: dict = {"setting": name, "cells": []}
    for r in rows:
        if r["corpus"] != name:
            continue
        ref = real.get((r["scope"], r["sub"], r["k"]))
        if ref is None:
            continue
        out["cells"].append(
            {
                "scope": r["scope"],
                "sub": r["sub"],
                "k": r["k"],
                "sk_vs_real": round(r["s_k"] / max(ref["s_k"], 1e-12), 3),
                "cmax_vs_real": round(r["count_max"] / max(ref["count_max"], 1e-12), 3),
                "g1_vs_real": round(
                    r["g1_id_twonn"] / max(ref["g1_id_twonn"], 1e-12), 3
                ),
                "g3_vs_real": round(
                    r["g3_eff_rank"] / max(ref["g3_eff_rank"], 1e-12), 3
                ),
                "g5_vs_real": round(
                    r["g5_relative_contrast"] / max(ref["g5_relative_contrast"], 1e-12),
                    3,
                ),
            }
        )
    sk_m = _mean_by_nk(rows, name, "s_k")
    sk_c = _mean_by_nk(rows, control, "s_k")
    g1_m = _mean_by_nk(rows, name, "g1_id_twonn")
    g1_c = _mean_by_nk(rows, control, "g1_id_twonn")
    out["vs_control"] = {
        f"n{n}_k{k}": {
            "sk_ratio": round(sk_m[(n, k)] / max(sk_c.get((n, k), 0), 1e-12), 3),
            "g1_ratio": round(g1_m[(n, k)] / max(g1_c.get((n, k), 0), 1e-12), 3),
        }
        for (n, k) in sorted(sk_m)
        if (n, k) in sk_c
    }
    real_means: dict = {}
    real_g1_means: dict = {}
    for (scope, sub, k), r in real.items():
        if scope.startswith("n"):
            real_means.setdefault((int(scope[1:]), k), []).append(r["s_k"])
            real_g1_means.setdefault((int(scope[1:]), k), []).append(r["g1_id_twonn"])
    real_sk = {key: float(np.mean(v)) for key, v in real_means.items()}
    real_g1 = {key: float(np.mean(v)) for key, v in real_g1_means.items()}
    out["dslope_sk_per_k"] = {
        f"k{k}": (
            None
            if slope_per_k(sk_m, k) is None or slope_per_k(real_sk, k) is None
            else round(slope_per_k(sk_m, k) - slope_per_k(real_sk, k), 3)
        )
        for k in G.K_GRID
    }
    # G1 drift vs real (P-A' target statistic; G1 is k-independent, use k0).
    k0 = G.K_GRID[0]
    s_cand, s_real = slope_per_k(g1_m, k0), slope_per_k(real_g1, k0)
    out["dslope_g1"] = (
        None if s_cand is None or s_real is None else round(s_cand - s_real, 3)
    )
    return out


def main() -> None:
    set_spectrum_target(SPECTRUM)
    base_params = json.load(open(PARAMS_PATH, encoding="utf-8"))["params"]
    real_rows = json.load(open(REAL_REF, encoding="utf-8"))["rows"]
    real = {(r["scope"], r["sub"], r["k"]): r for r in real_rows}
    log(f"ladder ns={NS} subs={SUBS} pool={POOL} instance={M_ROWS}")

    meta = {
        "prereg": "results/PREREG_ROUND12.md (draft; stage-1 pre-freeze sweep)",
        "params_path": PARAMS_PATH,
        "real_ref": REAL_REF,
        "arch_off": ARCH_OFF,
        "ns": NS,
        "subs": SUBS,
        "pool": POOL,
        "instance_rows": M_ROWS,
        "dim": DIM,
        "seed": SEED,
        "grid_g": GRID_G,
        "grid_o": GRID_O,
        "grid_c": GRID_C,
        "screening": bool(
            os.environ.get("R12_NS")
            or os.environ.get("R12_POOL")
            or os.environ.get("R12_SUBS")
        ),
        "n_query": G.N_QUERY,
    }
    cells: list[dict] = []
    summaries: dict[str, list] = {"G": [], "O": [], "C": []}

    def flush() -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "summaries": summaries, "cells": cells}, f)

    def run(tag: str, over: dict[str, float]) -> str:
        name = tag + (
            "_" + "_".join(f"{k}{v:g}" for k, v in over.items()) if over else "_ctrl"
        )
        params = base_params | ARCH_OFF | over
        log(f"{name}: generating pool instance ({M_ROWS} rows)")
        x = hier_r12_corpus(params, M_ROWS, DIM, SEED)
        base_blk = x[: M_ROWS - int(round(M_ROWS * QUERY_FRAC))]
        hmask = uniform_holdout_mask(len(base_blk), HOLD, seed=70)
        rows = measure_counts(name, base_blk[~hmask], base_blk[hmask])
        cells.extend({"overrides": over, "sweep": tag} | r for r in rows)
        del x, base_blk
        return name

    # Shared control: architecture removed, both mechanisms off.
    ctrl = run("ctrl", {})
    flush()
    for over in [g for g in GRID_G if g]:
        name = run("G", over)
        summaries["G"].append(summarize(cells, name, ctrl, real))
        flush()
    for over in GRID_O:
        name = run("O", over)
        summaries["O"].append(summarize(cells, name, ctrl, real))
        flush()
    # Sweep C: the cascade. Its first grid entry is its OWN control (the
    # level-dial point, cascade off) — count-quietness and drift are read
    # against that, not the bare-architecture control.
    if GRID_C:
        ctrl_c = run("C", GRID_C[0])
        summaries["C"].append(summarize(cells, ctrl_c, ctrl_c, real))
        flush()
        for over in GRID_C[1:]:
            name = run("C", over)
            summaries["C"].append(summarize(cells, name, ctrl_c, real))
            flush()
    summaries["G"].insert(0, summarize(cells, ctrl, ctrl, real))
    flush()
    log(f"wrote {OUT} ({len(cells)} rows)")
    print("R12_STAGE1_DONE", flush=True)


if __name__ == "__main__":
    main()
