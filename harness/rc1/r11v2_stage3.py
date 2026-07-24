"""Round-11 v2 PRE-FREEZE stage 3: G1 / ANATOMY pass (PREREG_ROUND11 v2).

The v1 sweep mapped only the count family; G1 (TwoNN) and the origin-shell
centrality claim behind P-B were untested at corpus level. This pass
measures, over the moved operating point + representative dial settings
(chosen from the stage-2 admissible region, plus one v1-style heavy setting
as a mechanism contrast) and the real corpus, at grid-subsampled scales:

  - G1 (TwoNN ID) under the grid operator (the same estimator geometry.py
    gates on),
  - turboquant-pro's hub anatomy (PYTHONPATH=/home/claude/turboquant-pro):
    the mechanism / centrality fields of ``hub_anatomy`` - count skew and
    max, corr(count, centrality), per-hub central-type fraction, mechanism
    verdict - the instrument whose confusion-matrix fixtures ground the
    origin-shell argument,
  - the planted rows' own centrality percentile in the subsampled corpus
    (the origin-shell claim, tested directly: planted hubs should sit at
    population-typical centrality, not in the central tail),
  - the planted share of the top-1% hub set (are the measured hubs the
    planted rows at all, at ladder scale?).

Settings come from ``anatomy_settings.json`` (written after the stage-2
read-out). Calibration only: nothing freezes, no gates are scored, no
admission runs, sealed rows remain sealed.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.environ.get("TQP_PATH", "/home/claude/turboquant-pro"))

from openvector_bench import geometry as G
from openvector_bench.generator_search import (
    QUERY_FRAC,
    hier_dupq_corpus,
    local_centers,
    set_spectrum_target,
)
from turboquant_pro.anatomy import hub_anatomy  # noqa: E402

R11V2 = os.environ.get("R11V2_DIR", "/home/claude/r11v2")
PARAMS_PATH = os.environ.get("R11V2_PARAMS", f"{R11V2}/fit_v10_result.json")
SPECTRUM = os.environ.get("R11V2_SPECTRUM", f"{R11V2}/spectrum_target_wiki1024.json")
OP_MOVE = os.environ.get("R11V2_OP", f"{R11V2}/op_move.json")
SETTINGS = os.environ.get("R11V2_SETTINGS", f"{R11V2}/anatomy_settings.json")
TARGET = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("R11V2_OUT", f"{R11V2}/r11v2_stage3.json")

POOL = max(G.N_GRID) + 220_000
M_ROWS = int(round(POOL / (1.0 - QUERY_FRAC)))
HOLD = min(G.N_QUERY * 2, POOL // 10)
DIM, SEED = 1024, 0
RADIUS, CENTER_JIT = 0.15, 0.05
K_ANATOMY = 10
SCALES = (25_000, 100_000)  # ladder ends where anatomy is affordable
_ANATOMY_KEEP = (
    "count_skew",
    "count_max",
    "top_hub_mass_share",
    "robin_hood_index",
    "frac_above_2k",
    "corr_count_centrality",
    "corr_count_neg_dk",
    "hub_vs_all_median_centrality",
    "hub_frac_central",
    "hub_frac_dense_noncentral",
    "mechanism",
)

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


def anatomy_at_scales(
    name: str, base_pool: np.ndarray, q_pool: np.ndarray, planted
) -> list[dict]:
    rows: list[dict] = []
    for n in SCALES:
        sub = 0
        rng = np.random.default_rng(10_000 * sub + n)
        bi = rng.choice(len(base_pool), size=n, replace=False)
        base = G.normalize(base_pool[bi])
        qi = rng.choice(len(q_pool), size=min(G.N_QUERY, len(q_pool)), replace=False)
        q = G.normalize(q_pool[qi])
        # G1 + the count/planted view from one knn (the anatomy call redoes
        # the q->base knn internally; the base->base pass inside hub_anatomy
        # dominates the cost either way).
        d, idx = G.knn(base, q, K_ANATOMY)
        g1 = G.id_twonn(d)
        counts = np.bincount(idx[:, :K_ANATOMY].ravel(), minlength=len(base)).astype(
            np.float64
        )
        row = {"corpus": name, "n": n, "sub": sub, "k": K_ANATOMY, "g1_id_twonn": g1}
        central = -np.linalg.norm(base - base.mean(0), axis=1)
        hub_thr = np.quantile(counts, 0.99)
        if planted is not None:
            pmask = np.isin(bi, planted)
            row["planted_rows_surviving"] = int(pmask.sum())
            if pmask.any():
                # origin-shell claim: centrality percentile of planted rows
                pct = (central[:, None] < central[None, pmask]).mean(0)
                row |= {
                    "planted_centrality_pctile_mean": float(pct.mean()),
                    "planted_centrality_pctile_minmax": [
                        float(pct.min()),
                        float(pct.max()),
                    ],
                    "planted_count_max": float(counts[pmask].max()),
                    "planted_count_mean": float(counts[pmask].mean()),
                    "planted_frac_of_top1pct_hubs": float(
                        pmask[counts >= hub_thr].sum()
                        / max((counts >= hub_thr).sum(), 1)
                    ),
                }
        log(f"{name} n{n}: anatomy (base->base is the slow part)")
        anat = hub_anatomy(base, q, k=K_ANATOMY)
        row["anatomy"] = {f: anat[f] for f in _ANATOMY_KEEP}
        rows.append(row)
        log(
            f"{name} n{n}: g1={g1:.1f} skew={anat['count_skew']:.2f} "
            f"cmax={anat['count_max']:.0f} mech={anat['mechanism']} "
            f"frac_central={anat['hub_frac_central']:.2f}"
        )
    return rows


def main() -> None:
    set_spectrum_target(SPECTRUM)
    base_params = json.load(open(PARAMS_PATH, encoding="utf-8"))["params"]
    op = json.load(open(OP_MOVE, encoding="utf-8"))
    params = base_params | op["overrides"]
    settings = json.load(open(SETTINGS, encoding="utf-8"))["settings"]
    log(f"moved OP {op['name']}; dial settings for anatomy: {settings}")

    out_rows: list[dict] = []
    meta = {
        "op_move": op,
        "settings": settings,
        "k": K_ANATOMY,
        "scales": SCALES,
        "radius": RADIUS,
        "center_jit": CENTER_JIT,
    }

    def flush() -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "rows": out_rows}, f, indent=1)

    # Real reference anatomy.
    corpus, _ = G.load_target(TARGET, cap=max(G.N_GRID) * 3)
    keep = np.fromiter((i for i in range(len(corpus)) if not sealed(i)), dtype=np.int64)
    corpus = np.asarray(corpus[keep])
    rmask = uniform_holdout_mask(len(corpus), min(G.N_QUERY * 2, len(corpus) // 10), 7)
    out_rows += anatomy_at_scales("real", corpus[~rmask], corpus[rmask], None)
    flush()
    del corpus

    # Moved instance, generated once; overlays reapplied per setting.
    log("generating the moved-OP pool instance (once)")
    x0 = hier_dupq_corpus(params, M_ROWS, DIM, SEED)
    base_blk = x0[: M_ROWS - int(round(M_ROWS * QUERY_FRAC))]
    hmask = uniform_holdout_mask(len(base_blk), HOLD, seed=70)

    out_rows += anatomy_at_scales(
        "moved_baseline", base_blk[~hmask], base_blk[hmask], None
    )
    flush()

    for m, p, ns in settings:
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
        planted_pool = np.flatnonzero(pmask_blk[~hmask])
        name = f"lc_m{m}_p{p}_s{ns}"
        out_rows += anatomy_at_scales(name, y[~hmask], y[hmask], planted_pool)
        flush()
        del y

    log(f"wrote {OUT} ({len(out_rows)} rows)")
    print("R11V2_STAGE3_DONE", flush=True)


if __name__ == "__main__":
    main()
