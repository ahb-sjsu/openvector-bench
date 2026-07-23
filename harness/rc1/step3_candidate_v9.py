"""Round-9 protocol step 3 (ROUND9_PREDICTION.md): candidate cells for the
formal §5 gating run, scored against the published v3 targets.

Candidate: ``hier_dupq_corpus`` at the step-2 operating point
(``results/fit_v9_result.json``, committed before this run). Conventions mirror
``step1_targets_v3.py`` exactly: full v2 grid, 5 subsamples (one fresh candidate
instance per subsample, seed = sub), UNIFORM battery-A holdout with the null
convention (seed = 70 + sub), battery-B queries from the candidate's own query
block (§4 analogous-query clause — the query generator is part of the candidate).
Output cells are appended to a copy of the v3 target cells and scored with
``score_rc1`` so the §8 no-null-admitted check re-runs under the v3 protocol.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict

import numpy as np

from openvector_bench import geometry as G
from openvector_bench.generator_search import hier_dupq_corpus

TARGETS = os.environ.get("RC_TARGETS", "/home/claude/r9/rc1_targets_v3.json")
PARAMS_PATH = os.environ.get("RC_PARAMS", "/home/claude/r9/fit_v9_result.json")
OUT = os.environ.get("RC_OUT", "/home/claude/r9/rc1_v9_cells.json")
QUERY_FRAC = 1.0 / 9.0

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - _T0:7.0f}s] {msg}", flush=True)


def uniform_holdout(x: np.ndarray, hold: int, seed: int):
    rng = np.random.default_rng(seed)
    hidx = np.sort(rng.choice(len(x), size=hold, replace=False))
    mask = np.zeros(len(x), dtype=bool)
    mask[hidx] = True
    return x[mask], x[~mask]


def main() -> None:
    params = json.load(open(PARAMS_PATH, encoding="utf-8"))["params"]
    targets = json.load(open(TARGETS, encoding="utf-8"))
    log(f"targets: {len(targets)} cells; grid n={G.N_GRID} subs={G.SUBSAMPLES}")

    # Pool sized so n=200k remains a genuine subsample after holdout.
    pool = max(G.N_GRID) + 220_000
    m = int(round(pool / (1.0 - QUERY_FRAC)))
    hold = min(G.N_QUERY * 2, pool // 10)

    cells = list(targets)
    for sub in range(G.SUBSAMPLES):
        x = hier_dupq_corpus(params, m, 1024, seed=sub)
        n_base = m - int(round(m * QUERY_FRAC))
        base_blk, qb = x[:n_base], x[n_base:]
        qa, base_x = uniform_holdout(base_blk, hold, seed=70 + sub)
        log(
            f"sub {sub}: instance {x.shape}, base {base_x.shape}, "
            f"qa {qa.shape}, qb {qb.shape}"
        )
        for n in G.N_GRID:
            if n > len(base_x):
                continue
            for battery, qset in (("A_corpus", qa), ("B_query", qb)):
                for c in G.measure("hier_dupq_r9", battery, base_x, qset, n, sub):
                    cells.append(asdict(c))
                log(
                    f"sub {sub} hier_dupq_r9 n={n:6d} {battery}  "
                    f"({len(cells)} cells)"
                )
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(cells, f, indent=1)
    log(f"wrote {OUT}")
    print("STEP3_CANDIDATE_DONE", flush=True)


if __name__ == "__main__":
    main()
