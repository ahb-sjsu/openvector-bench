"""Round-11 v2 PRE-FREEZE stage 2: SUBSAMPLE-AWARE dial calibration.

Implements PREREG_ROUND11 v2's calibration section on the MOVED operating
point (stage 1, r11v2_stage1.py): the local_centers dial (m, p, n_shell) is
calibrated per ladder n UNDER THE GRID'S OWN SUBSAMPLE OPERATOR - never on
the pool alone (the v1 sweep's pool-calibrated statistic swung 56.7x -> 2.5x
-> 30.4x along one ladder; pool values are diagnostics only and are not even
measured here, the v1 sweep already mapped them).

Per v2, a dial setting is ADMISSIBLE only if all three hold:
  1. Retention floor: expected surviving planted rows per draw at the
     smallest ladder n >= FLOOR (proposed 8; the author sets the final value
     at freeze) - m*p*(1 - HOLD/|base|)*(n/|pool|) at n = min(N_GRID).
  2. Ladder stability: |Delta slope| <= 0.05/decade between the setting's
     mean-S_k log10-slope across the ladder and the real reference's, at
     every k (the mandatory-gate convention: G6 gates every cell).
  3. Variance: the between-draw S_k-ratio spread (max - min over draws) must
     not exceed the equivalence-band width (1.15 - 0.85 = 0.30) at any
     (n, k).
>= 2 draws per (setting, n); any admissible setting whose mean S_k ratio
lands in [0.85, 1.15] in >= 10/12 ladder cells is flagged freeze-candidate
and re-measured at 5 draws (the v2 disclosure requirement), against the
5-draw real reference from stage 1.

G1 (TwoNN) is recorded per (scope, sub) for every dial cell - the stage-3
anatomy pass reads its dial response from this file. Calibration only:
nothing freezes, no gates are scored, no admission runs, sealed rows remain
sealed.
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
    local_centers,
    set_spectrum_target,
)

R11V2 = os.environ.get("R11V2_DIR", "/home/claude/r11v2")
PARAMS_PATH = os.environ.get("R11V2_PARAMS", f"{R11V2}/fit_v10_result.json")
SPECTRUM = os.environ.get("R11V2_SPECTRUM", f"{R11V2}/spectrum_target_wiki1024.json")
OP_MOVE = os.environ.get("R11V2_OP", f"{R11V2}/op_move.json")
REAL_REF = os.environ.get("R11V2_REAL", f"{R11V2}/r11v2_real_ref.json")
OUT = os.environ.get("R11V2_OUT", f"{R11V2}/r11v2_stage2.json")

POOL = max(G.N_GRID) + 220_000
M_ROWS = int(round(POOL / (1.0 - QUERY_FRAC)))
HOLD = min(G.N_QUERY * 2, POOL // 10)
DIM, SEED = 1024, 0
MASS_CAP = 0.10  # overlay may claim at most 10% of the pool's base rows
RADIUS, CENTER_JIT = 0.15, 0.05  # spec defaults, as in the v1 sweep
SUBS = (0, 1)  # >= 2 draws per (setting, n)
SUBS_FREEZE = (0, 1, 2, 3, 4)  # 5 draws for freeze-candidates
RETENTION_FLOOR = 8.0  # proposed-for-author; see PREREG_ROUND11 v2
DSLOPE_MAX = 0.05  # |Delta slope| per decade, candidate vs real
BAND = (0.85, 1.15)
SPREAD_MAX = BAND[1] - BAND[0]  # between-draw S_k-ratio spread ceiling
FREEZE_MIN_CELLS = 10  # of the 12 ladder cells, mirroring the >=10/12 rule

# Dial grid, mass-capped in-loop. The v1 grid's m=4 arm cannot reach the
# retention floor (4*32*0.0595 = 7.6 < 8) and its s8192 arm is where the v1
# variance blow-up lived; this grid concentrates where the floor is
# satisfiable and the shell response is grid-visible.
GRID = [
    (m, p, ns)
    for m in (8, 16, 32, 64)
    for p in (4, 8, 16, 32)
    for ns in (256, 512, 1024, 2048)
]

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - _T0:7.0f}s] {msg}", flush=True)


def uniform_holdout_mask(n: int, hold: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mask = np.zeros(n, dtype=bool)
    mask[rng.choice(n, size=hold, replace=False)] = True
    return mask


def count_stats(idx: np.ndarray, n_rows: int, k: int, pmask: np.ndarray | None) -> dict:
    counts = np.bincount(idx[:, :k].ravel(), minlength=n_rows).astype(np.float64)
    mean, s = counts.mean(), counts.std()
    out = {
        "s_k": float(((counts - mean) ** 3).mean() / max(s**3, 1e-12)),
        "count_max": int(counts.max()),
        "rh": float(0.5 * np.abs(counts - mean).sum() / max(counts.sum(), 1e-12)),
        "count_mean": float(mean),
    }
    if pmask is not None:
        out["planted_rows"] = int(pmask.sum())
        if pmask.any():
            pc = counts[pmask]
            out |= {"planted_max": int(pc.max()), "planted_mean": float(pc.mean())}
    return out


def measure_ladders(
    name: str,
    base_pool: np.ndarray,
    q_pool: np.ndarray,
    planted: np.ndarray | None,
    subs,
) -> list[dict]:
    """Grid-subsampled ladders only, under measure()'s own operator."""
    rows: list[dict] = []
    for n in G.N_GRID:
        if n > len(base_pool):
            continue
        for sub in subs:
            rng = np.random.default_rng(10_000 * sub + n)
            bi = rng.choice(len(base_pool), size=n, replace=False)
            base = G.normalize(base_pool[bi])
            qi = rng.choice(
                len(q_pool), size=min(G.N_QUERY, len(q_pool)), replace=False
            )
            q = G.normalize(q_pool[qi])
            d, idx = G.knn(base, q, G.KMAX)
            g1 = G.id_twonn(d)
            pmask = np.isin(bi, planted) if planted is not None else None
            for k in G.K_GRID:
                rows.append(
                    {"corpus": name, "scope": f"n{n}", "n": n, "sub": sub, "k": k}
                    | count_stats(idx, n, k, pmask)
                    | {
                        "g1_id_twonn": g1,
                        "g5_relative_contrast": G.relative_contrast(d, base, q, k),
                    }
                )
        log(f"{name:22s} n{n:<7d} done ({len(rows)} rows)")
    return rows


def summarize(rows: list[dict], real: dict, m: int, p: int, ns: int) -> dict:
    """The v2 admissibility verdict for one dial setting."""
    per_nk: dict[tuple[int, int], dict] = {}
    for r in rows:
        ref = real.get((r["scope"], r["sub"], r["k"]))
        if ref is None:
            continue
        cell = per_nk.setdefault(
            (r["n"], r["k"]), {"ratios": [], "cmax": [], "pl": [], "sk_raw": []}
        )
        cell["ratios"].append(r["s_k"] / max(ref["s_k"], 1e-12))
        cell["cmax"].append(r["count_max"] / max(ref["count_max"], 1e-12))
        cell["pl"].append(r.get("planted_rows", 0))
        cell["sk_raw"].append(r["s_k"])
    n_min = min(G.N_GRID)
    pool_base = POOL - HOLD  # 400k rows the ladder draws from
    exp_surv = m * p * (pool_base / POOL) * (n_min / pool_base)
    retention_ok = exp_surv >= RETENTION_FLOOR
    cells, spread_ok, in_band_cells = [], True, 0
    slopes: dict[int, float] = {}
    for k in G.K_GRID:
        ln_n, ln_sk, ln_sk_real = [], [], []
        for n in G.N_GRID:
            c = per_nk.get((n, k))
            if c is None:
                continue
            mean_r = float(np.mean(c["ratios"]))
            spread = float(np.max(c["ratios"]) - np.min(c["ratios"]))
            spread_ok &= spread <= SPREAD_MAX
            in_band = BAND[0] <= mean_r <= BAND[1]
            in_band_cells += int(in_band)
            # ladder slope inputs: candidate + real mean S_k (raw values, so
            # the criterion matches the RC-1 growth-exponent convention)
            sk_cand = float(np.mean(c["sk_raw"]))
            sk_real = float(
                np.mean(
                    [
                        real[(f"n{n}", s, k)]["s_k"]
                        for s in range(5)
                        if (f"n{n}", s, k) in real
                    ]
                )
            )
            ln_n.append(np.log10(n))
            ln_sk.append(np.log10(max(sk_cand, 1e-12)))
            ln_sk_real.append(np.log10(max(sk_real, 1e-12)))
            cells.append(
                {
                    "n": n,
                    "k": k,
                    "sk_ratio_mean": round(mean_r, 3),
                    "sk_ratio_spread": round(spread, 3),
                    "cmax_ratio_mean": round(float(np.mean(c["cmax"])), 3),
                    "planted_surv_mean": round(float(np.mean(c["pl"])), 2),
                    "in_band": bool(in_band),
                }
            )
        if len(ln_n) >= 2:
            slope_c = float(np.polyfit(ln_n, ln_sk, 1)[0])
            slope_r = float(np.polyfit(ln_n, ln_sk_real, 1)[0])
            slopes[k] = round(slope_c - slope_r, 4)
    stability_ok = bool(slopes) and all(abs(v) <= DSLOPE_MAX for v in slopes.values())
    admissible = bool(retention_ok and stability_ok and spread_ok)
    return {
        "m": m,
        "p": p,
        "n_shell": ns,
        "expected_surv_at_nmin": round(exp_surv, 2),
        "retention_ok": bool(retention_ok),
        "dslope_per_k": slopes,
        "stability_ok": bool(stability_ok),
        "spread_ok": bool(spread_ok),
        "admissible": admissible,
        "in_band_cells": in_band_cells,
        "freeze_candidate": bool(admissible and in_band_cells >= FREEZE_MIN_CELLS),
        "cells": cells,
    }


def main() -> None:
    set_spectrum_target(SPECTRUM)
    base_params = json.load(open(PARAMS_PATH, encoding="utf-8"))["params"]
    op = json.load(open(OP_MOVE, encoding="utf-8"))
    params = base_params | op["overrides"]
    real_rows = json.load(open(REAL_REF, encoding="utf-8"))["rows"]
    real = {(r["scope"], r["sub"], r["k"]): r for r in real_rows}
    log(f"moved operating point {op['name']}: overrides {op['overrides']}")

    log("generating the moved-OP pool instance (once)")
    x0 = hier_dupq_corpus(params, M_ROWS, DIM, SEED)
    base_blk = x0[: M_ROWS - int(round(M_ROWS * QUERY_FRAC))]
    hmask = uniform_holdout_mask(len(base_blk), HOLD, seed=70)
    log(f"instance {x0.shape}; base block {base_blk.shape}; holdout {HOLD}")

    cells: list[dict] = []
    summaries: list[dict] = []
    meta = {
        "op_move": op,
        "pool": POOL,
        "instance_rows": M_ROWS,
        "dim": DIM,
        "seed": SEED,
        "radius": RADIUS,
        "center_jit": CENTER_JIT,
        "mass_cap": MASS_CAP,
        "retention_floor_proposed": RETENTION_FLOOR,
        "dslope_max": DSLOPE_MAX,
        "band": BAND,
        "spread_max": SPREAD_MAX,
        "skipped": [],
    }

    def flush() -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(
                {"meta": meta, "summaries": summaries, "cells": cells}, f, indent=1
            )

    # Baseline (dial off) at 5 draws: the moved floor's own spread.
    qa, bp = base_blk[hmask], base_blk[~hmask]
    for row in measure_ladders("moved_baseline", bp, qa, None, SUBS_FREEZE):
        cells.append({"m": 0, "p": 0, "n_shell": 0} | row)
    flush()

    for m, p, ns in GRID:
        total = m * (p + ns)
        if total > MASS_CAP * len(base_blk):
            meta["skipped"].append({"m": m, "p": p, "n_shell": ns, "rows": total})
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
            f"planted survive the holdout"
        )
        rows = measure_ladders(name, bp, qa, planted_pool, SUBS)
        cells.extend({"m": m, "p": p, "n_shell": ns} | r for r in rows)
        summaries.append(summarize(rows, real, m, p, ns))
        flush()
        del y

    # Freeze-candidates: extend to 5 draws and re-verdict.
    for s in [s for s in summaries if s["freeze_candidate"]][:5]:
        m, p, ns = s["m"], s["p"], s["n_shell"]
        name = f"lc_m{m}_p{p}_s{ns}"
        log(f"freeze-candidate {name}: extending to {len(SUBS_FREEZE)} draws")
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
        extra = measure_ladders(
            name, bp, qa, planted_pool, tuple(set(SUBS_FREEZE) - set(SUBS))
        )
        cells.extend({"m": m, "p": p, "n_shell": ns} | r for r in extra)
        all_rows = [
            r
            for r in cells
            if r.get("m") == m
            and r.get("p") == p
            and r.get("n_shell") == ns
            and r["corpus"] == name
        ]
        s5 = summarize(all_rows, real, m, p, ns)
        s5["draws"] = len(SUBS_FREEZE)
        summaries.append(s5)
        flush()
        del y

    log(f"wrote {OUT} ({len(cells)} rows, {len(summaries)} summaries)")
    print("R11V2_STAGE2_DONE", flush=True)


if __name__ == "__main__":
    main()
