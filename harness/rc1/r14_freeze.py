"""Round-14 step 1: record the frozen corpus point's reference values.

PREREG_ROUND14 §6 step 1. Measures the round-8 winning point's five
corpus-side geometry gates plus the anatomy guard on three seeds. These
become the **P-14C reference values**: the query-model search that follows
must leave each of them within 0.05x, and without a baseline measured
before the search begins there is nothing to hold it to.

Nothing is scored against a band here and no admission is claimed. This is
a baseline, not a result.

Two scope points, both deliberate:

* Only the CORPUS parameters are frozen. ``query_tail`` and ``equalize``
  belong to the query model and are round 14's search space, so they are
  swept here rather than fixed — the point of the baseline is that the
  geometry gates do not move when they change.
* G6 is not part of this baseline. It is the query model's responsibility
  under the round-14 split, and it is measured in its budget-invariant form
  (``attractiveness_skew``) per the 2026-08-07 amendment to PREREG_RC1 §5.
  Reporting a raw-``s_k`` G6 here would invite exactly the comparison that
  amendment exists to prevent.

Env: R14F_OUT, R14F_N, R14F_DIM, R14F_SEEDS, R14F_K, R14F_QT (query_tail
sweep), R14F_EQ (equalize sweep).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    geometry_vector,
    hier_query_corpus,
)
from openvector_bench.geometry import hubness, knn, normalize  # noqa: E402
from openvector_bench.hubness import attractiveness_skew, rho  # noqa: E402

OUT = os.environ.get("R14F_OUT", "results/r14_freeze_baseline.json")
FROZEN = os.environ.get("R14F_FROZEN", "results/r14_frozen_corpus.json")
N = int(os.environ.get("R14F_N", "25000"))
DIM = int(os.environ.get("R14F_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R14F_SEEDS", "[0, 1, 2]"))
K = int(os.environ.get("R14F_K", "10"))
KMAX = int(os.environ.get("R14F_KMAX", "100"))
# The query-model axes. Held at the round-8 values plus two probes each, so
# the baseline records how much the geometry gates move under exactly the
# search this round will run.
QT = json.loads(os.environ.get("R14F_QT", "[]"))
EQ = json.loads(os.environ.get("R14F_EQ", "[]"))
GEOMETRY_GATES = (
    "g1_id_twonn",
    "g3_eff_rank",
    "g4_dims90",
    "g7_local_id_iqr",
    "g8_pca_retention",
)
ANATOMY_QUERIES = 2000


def log(m: str) -> None:
    print(m, flush=True)


def measure(params: dict, seed: int) -> dict:
    x = hier_query_corpus(params, N, DIM, seed)
    n_query = int(round(N * QUERY_FRAC))
    base, q = normalize(x[: N - n_query]), normalize(x[N - n_query :])
    gv = geometry_vector(base, q, K, KMAX)
    # Anatomy guard, computed exactly as make_evaluate_fn does.
    nq_a = min(ANATOMY_QUERIES, len(base))
    _, idx_a = knn(base, base[:nq_a], KMAX + 1)
    bb = hubness(idx_a[:, 1:], len(base), K)
    # Query-side, recorded for context only — it is the search's target, not
    # part of the baseline the search must preserve.
    _, idx_q = knn(base, q, K)
    counts = np.bincount(idx_q[:, :K].ravel(), minlength=len(base)).astype(float)
    return {
        "geometry": {g: float(gv[g]) for g in GEOMETRY_GATES},
        "g2_id_ballgrowth": float(gv["g2_id_ballgrowth"]),
        "g5_relative_contrast": float(gv["g5_relative_contrast"]),
        "bb_skew": float(bb),
        "context_only": {
            "g6_raw_s_k": float(gv["g6_hubness_skew"]),
            "attractiveness_skew": attractiveness_skew(counts),
            "rho": rho(len(q), K, len(base)),
        },
    }


def main() -> None:
    frozen = json.load(open(FROZEN, encoding="utf-8"))
    params = dict(frozen["params"])
    log(f"R14 FREEZE — baseline for P-14C, n={N} dim={DIM} seeds={SEEDS}")
    log(f"frozen corpus params from {FROZEN}")

    arms = [("frozen", params)]
    for qt in QT:
        arms.append((f"query_tail={qt}", dict(params, query_tail=qt)))
    for eq in EQ:
        arms.append((f"equalize={eq}", dict(params, equalize=eq)))

    runs = []
    for name, p in arms:
        per_seed = []
        for sd in SEEDS:
            per_seed.append(measure(p, sd))
            log(f"  {name:22s} seed {sd} done")
        agg = {}
        for g in GEOMETRY_GATES:
            vals = [r["geometry"][g] for r in per_seed]
            agg[g] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals))}
        bb = [r["bb_skew"] for r in per_seed]
        runs.append(
            {
                "arm": name,
                "params_delta": {k: v for k, v in p.items() if params.get(k) != v},
                "geometry": agg,
                "bb_skew": {"mean": float(np.mean(bb)), "sd": float(np.std(bb))},
                "context_only": per_seed[0]["context_only"],
            }
        )
        log(
            f"  {name:22s} "
            + " ".join(
                f"{g.split('_')[0]}={agg[g]['mean']:.3g}" for g in GEOMETRY_GATES
            )
            + f" bb_skew={np.mean(bb):.3g}"
        )

    base_row = runs[0]
    drift = {}
    for r in runs[1:]:
        drift[r["arm"]] = {
            g: abs(
                r["geometry"][g]["mean"] / max(base_row["geometry"][g]["mean"], 1e-12)
                - 1.0
            )
            for g in GEOMETRY_GATES
        }
    worst = max((max(v.values()) for v in drift.values()), default=0.0)
    log(
        f"\nworst geometry drift under query-model moves: {worst:.4f} (P-14C allows 0.05)"
    )

    out = {
        "meta": {
            "prereg": "results/PREREG_ROUND14.md step 1 — P-14C reference values",
            "frozen_source": FROZEN,
            "n": N,
            "dim": DIM,
            "k": K,
            "seeds": SEEDS,
            "query_frac": QUERY_FRAC,
            "note": "baseline only; nothing scored against a band, no "
            "admission claimed. G6 excluded by design — it is the query "
            "model's responsibility this round.",
        },
        "runs": runs,
        "geometry_drift_under_query_moves": drift,
        "worst_drift": worst,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R14_FREEZE_DONE")


if __name__ == "__main__":
    main()
