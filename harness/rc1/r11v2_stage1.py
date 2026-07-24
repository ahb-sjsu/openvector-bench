"""Round-11 v2 PRE-FREEZE stage 1: the OPERATING-POINT MOVE (PREREG_ROUND11 v2).

The v1 calibration (results/ROUND11_CALIBRATION.md) measured the un-planted
fit_v10 baseline out of the G6 band HIGH in 12/12 ladder cells (S_k ratio
1.19-1.68, count_max ratio 1.25-2.14) and the local_centers overlay is
monotone-up, so no dial region can land in band from that floor. v2 change 1
is therefore a joint operating-point move: reduce the generator's EMERGENT
cloud/hub mass (the cloud_mass / cloud_tail knobs that own battery-A corpus-
side hub mass) until the un-planted ladder statistics sit at or below band,
without breaking the G3/G4/G5 spot-checks (G1 recorded alongside - the
round-10 joint constraint). Fit AT the pool, evaluate on grid-subsampled
ladders (the round-10 rule); pool values are diagnostics only.

Phases (one run, restart-safe via the output JSON):
  R. Real-corpus reference under the identical count protocol, ladders
     n in N_GRID with FIVE subsample draws (stage 2 needs 5-draw spreads
     for freeze-candidates) + the pool scope. Written to r11v2_real_ref.json.
  S. Candidate search: a small grid over (cloud_mass, cloud_tail) around the
     fit_v10 point (fit_v10 itself is the control), each measured at
     n in {25k, 200k}, one draw, all k - a cheap 6-cell proxy.
  V. Verification: every candidate whose proxy cells are all at/below band
     (capped at 3, else the least-overshooting one) re-measured on the FULL
     ladder (4 n x 3 k), >= 3 draws, + pool diagnostics + G1/G3/G4/G5.

If no candidate reaches band without breaking G3/G4/G5, that is the v2
second failure clause (joint-constraint infeasibility at the fit_v10 family
level) - reported, not forced. Calibration only: nothing here freezes the
prereg, no gates are scored, no admission runs, the sealed rows stay sealed.
"""

from __future__ import annotations

import json
import os
import time

import numpy as np

from openvector_bench import geometry as G
from openvector_bench.generator_search import (
    QUERY_FRAC,
    hier_dupq_corpus,
    set_spectrum_target,
)

R11V2 = os.environ.get("R11V2_DIR", "/home/claude/r11v2")
PARAMS_PATH = os.environ.get("R11V2_PARAMS", f"{R11V2}/fit_v10_result.json")
SPECTRUM = os.environ.get("R11V2_SPECTRUM", f"{R11V2}/spectrum_target_wiki1024.json")
TARGET = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("R11V2_OUT", f"{R11V2}/r11v2_stage1.json")
REAL_REF = os.environ.get("R11V2_REAL", f"{R11V2}/r11v2_real_ref.json")

POOL = max(G.N_GRID) + 220_000  # step-3 pool: thinning factors match the grid
M_ROWS = int(round(POOL / (1.0 - QUERY_FRAC)))
HOLD = min(G.N_QUERY * 2, POOL // 10)
DIM, SEED = 1024, 0
SUBS_SEARCH = (0,)  # proxy draws per ladder n during the search
SUBS_VERIFY = (0, 1, 2)  # draws for the verified operating point
SUBS_REAL = (0, 1, 2, 3, 4)  # stage-2 freeze-candidates need 5-draw spreads
NS_SEARCH = (25_000, 200_000)  # proxy ladder ends
# Equivalence bands (RC-1 PREREG v2 par.5): S_k in [0.85, 1.15] x real,
# count_max in [0.80, 1.20] x real. "At or below band" = ratio <= the top.
BAND_SK_HI, BAND_CMAX_HI = 1.15, 1.20
SPOT_BAND = (0.85, 1.15)  # G3/G4/G5 spot-check band

# The search grid: the two knobs that own emergent battery-A cloud/hub mass.
# fit_v10 (cloud_mass 0.2026, cloud_tail 1.0005) is candidate 0 = the control.
CAND_GRID: list[dict[str, float]] = [
    {},  # fit_v10 control (v1 baseline reproduced)
    {"cloud_mass": 0.15},
    {"cloud_mass": 0.10},
    {"cloud_mass": 0.05},
    {"cloud_mass": 0.0},
    {"cloud_tail": 0.5},
    {"cloud_mass": 0.15, "cloud_tail": 0.5},
    {"cloud_mass": 0.10, "cloud_tail": 0.5},
    {"cloud_mass": 0.05, "cloud_tail": 0.5},
]
# A follow-up wave (e.g. the non-cloud hub-mass knobs, if the cloud wave
# cannot reach band) is passed as JSON without editing the committed grid;
# the wave actually run is recorded in the output's meta.grid either way.
if os.environ.get("R11V2_GRID"):
    CAND_GRID = json.loads(os.environ["R11V2_GRID"])

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - _T0:7.0f}s] {msg}", flush=True)


def sealed(i: int) -> bool:
    import hashlib

    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def uniform_holdout_mask(n: int, hold: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mask = np.zeros(n, dtype=bool)
    mask[rng.choice(n, size=hold, replace=False)] = True
    return mask


def fast_spectrum(x: np.ndarray) -> tuple[float, int]:
    """geometry.spectrum's numbers via covariance eigvals (SVD of 50k x 1024
    rows is minutes on CPU; the 1024x1024 covariance path is seconds)."""
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


def measure_counts(
    name: str,
    base_pool: np.ndarray,
    q_pool: np.ndarray,
    *,
    ns=tuple(G.N_GRID),
    subs=(0,),
    with_pool: bool = False,
) -> list[dict]:
    """Ladder scopes under measure()'s own operator + G1/G3/G4/G5 per scope."""
    rows: list[dict] = []
    scopes = ([("pool", len(base_pool), (0,))] if with_pool else []) + [
        (f"n{n}", n, subs) for n in ns if n <= len(base_pool)
    ]
    for scope, n, ss in scopes:
        for sub in ss:
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
                    {"corpus": name, "scope": scope, "n": n, "sub": sub, "k": k}
                    | count_stats(idx, n, k)
                    | {
                        "g1_id_twonn": g1,
                        "g3_eff_rank": eff,
                        "g4_dims90": d90,
                        "g5_relative_contrast": G.relative_contrast(d, base, q, k),
                    }
                )
        log(f"{name:26s} {scope:8s} done ({len(rows)} rows)")
    return rows


def real_lookup(real_rows: list[dict]) -> dict:
    return {(r["scope"], r["sub"], r["k"]): r for r in real_rows}


def cand_name(over: dict[str, float]) -> str:
    if not over:
        return "op_fit_v10"
    return "op_" + "_".join(f"{k.replace('cloud_', 'c')}{v:g}" for k, v in over.items())


def band_report(rows: list[dict], real: dict, name: str) -> dict:
    """Per-cell ratios to the real reference at the same (scope, sub, k)."""
    cells, worst = [], 0.0
    ok_all, spots_ok = True, True
    for r in rows:
        if r["corpus"] != name or r["scope"] == "pool":
            continue
        ref = real.get((r["scope"], r["sub"], r["k"]))
        if ref is None:
            continue
        sk_ratio = r["s_k"] / max(ref["s_k"], 1e-12)
        cm_ratio = r["count_max"] / max(ref["count_max"], 1e-12)
        spot = {
            g: r[g] / max(ref[g], 1e-12)
            for g in ("g3_eff_rank", "g4_dims90", "g5_relative_contrast")
        }
        g1_ratio = r["g1_id_twonn"] / max(ref["g1_id_twonn"], 1e-12)
        in_band = sk_ratio <= BAND_SK_HI and cm_ratio <= BAND_CMAX_HI
        spot_in = all(SPOT_BAND[0] <= v <= SPOT_BAND[1] for v in spot.values())
        ok_all &= in_band
        spots_ok &= spot_in
        worst = max(worst, sk_ratio / BAND_SK_HI, cm_ratio / BAND_CMAX_HI)
        cells.append(
            {
                "scope": r["scope"],
                "sub": r["sub"],
                "k": r["k"],
                "sk_ratio": round(sk_ratio, 3),
                "cmax_ratio": round(cm_ratio, 3),
                "g1_ratio": round(g1_ratio, 3),
                **{g: round(v, 3) for g, v in spot.items()},
                "count_in_band": bool(in_band),
                "spots_in_band": bool(spot_in),
            }
        )
    return {
        "candidate": name,
        "cells": cells,
        "all_counts_at_or_below_band": bool(ok_all),
        "all_spots_in_band": bool(spots_ok),
        "worst_overshoot": round(worst, 3),
    }


def main() -> None:
    set_spectrum_target(SPECTRUM)
    base_params = json.load(open(PARAMS_PATH, encoding="utf-8"))["params"]
    log(f"grid n={G.N_GRID} k={G.K_GRID} pool={POOL} instance={M_ROWS}")

    # ---- Phase R: real reference (5 draws; reused by stages 2 and 3) ------
    if os.path.exists(REAL_REF):
        real_rows = json.load(open(REAL_REF, encoding="utf-8"))["rows"]
        log(f"real reference reused from {REAL_REF} ({len(real_rows)} rows)")
    else:
        corpus, _ = G.load_target(TARGET, cap=max(G.N_GRID) * 3)
        keep = np.fromiter(
            (i for i in range(len(corpus)) if not sealed(i)), dtype=np.int64
        )
        corpus = np.asarray(corpus[keep])
        rmask = uniform_holdout_mask(
            len(corpus), min(G.N_QUERY * 2, len(corpus) // 10), 7
        )
        log(f"real non-sealed pool {corpus.shape}")
        real_rows = measure_counts(
            "real", corpus[~rmask], corpus[rmask], subs=SUBS_REAL, with_pool=True
        )
        with open(REAL_REF, "w", encoding="utf-8") as f:
            json.dump(
                {"meta": {"target": TARGET, "subs": SUBS_REAL}, "rows": real_rows},
                f,
                indent=1,
            )
        del corpus
    real = real_lookup(real_rows)

    # ---- Phase S: candidate search on the proxy ladder ends ---------------
    cells: list[dict] = []
    meta = {
        "params_path": PARAMS_PATH,
        "pool": POOL,
        "instance_rows": M_ROWS,
        "dim": DIM,
        "seed": SEED,
        "grid": CAND_GRID,
        "bands": {"s_k_hi": BAND_SK_HI, "cmax_hi": BAND_CMAX_HI, "spot": SPOT_BAND},
    }

    def flush(extra: dict | None = None) -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"meta": meta | (extra or {}), "cells": cells}, f, indent=1)

    reports = []
    for over in CAND_GRID:
        name = cand_name(over)
        params = base_params | over
        log(f"{name}: generating pool instance")
        x = hier_dupq_corpus(params, M_ROWS, DIM, SEED)
        base_blk = x[: M_ROWS - int(round(M_ROWS * QUERY_FRAC))]
        hmask = uniform_holdout_mask(len(base_blk), HOLD, seed=70)
        rows = measure_counts(
            name, base_blk[~hmask], base_blk[hmask], ns=NS_SEARCH, subs=SUBS_SEARCH
        )
        cells.extend({"overrides": over, "phase": "search"} | r for r in rows)
        rep = band_report(rows, real, name)
        rep["overrides"] = over
        reports.append(rep)
        log(
            f"{name}: counts_ok={rep['all_counts_at_or_below_band']} "
            f"spots_ok={rep['all_spots_in_band']} worst={rep['worst_overshoot']}"
        )
        flush({"search_reports": reports})
        del x, base_blk

    # ---- Phase V: full-ladder verification of the band-reaching points ----
    passing = [
        r
        for r in reports
        if r["all_counts_at_or_below_band"] and r["all_spots_in_band"]
    ]
    if passing:
        chosen = sorted(passing, key=lambda r: r["worst_overshoot"], reverse=True)[:3]
        # closest-to-band first among passers: prefer the least mass removed
    else:
        chosen = sorted(reports, key=lambda r: r["worst_overshoot"])[:1]
        log("NO candidate reached band on the proxy - verifying the closest only")
    verify_reports = []
    for rep in chosen:
        over = rep["overrides"]
        name = cand_name(over)
        params = base_params | over
        log(f"VERIFY {name}: regenerating pool instance")
        x = hier_dupq_corpus(params, M_ROWS, DIM, SEED)
        base_blk = x[: M_ROWS - int(round(M_ROWS * QUERY_FRAC))]
        hmask = uniform_holdout_mask(len(base_blk), HOLD, seed=70)
        rows = measure_counts(
            name + "_verify",
            base_blk[~hmask],
            base_blk[hmask],
            subs=SUBS_VERIFY,
            with_pool=True,
        )
        cells.extend({"overrides": over, "phase": "verify"} | r for r in rows)
        vrep = band_report(rows, real, name + "_verify")
        vrep["overrides"] = over
        verify_reports.append(vrep)
        log(
            f"VERIFY {name}: counts_ok={vrep['all_counts_at_or_below_band']} "
            f"spots_ok={vrep['all_spots_in_band']} worst={vrep['worst_overshoot']}"
        )
        flush({"search_reports": reports, "verify_reports": verify_reports})
        del x, base_blk

    log(f"wrote {OUT} ({len(cells)} rows)")
    print("R11V2_STAGE1_DONE", flush=True)


if __name__ == "__main__":
    main()
