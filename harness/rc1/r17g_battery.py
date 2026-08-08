"""P-17cG — the RC-1 geometry battery on the capacity-limited family.

Registered use: round 17c admitted nothing, but measured the capacity family's
hub scaling at +0.514 +/- 0.065 against real corpora's +0.51. Hub scaling is
the ONLY gate this candidate has ever been measured on. This runs the rest.

**Configuration is declared here, before the run.** The candidate is the
capacity-limited family at growth exponent **0.38**, the midpoint of round
17c's declared range and the value 17c registered as its predicted winner.
Round 17c found its arms statistically indistinguishable on hub scaling, so
picking the arm that scored best would be a cherry-pick with no justification.
The midpoint is chosen by rule instead.

**Why the real reference is re-measured rather than loaded.** The stored cells
in ``rc1_cells.json`` were measured 2026-07-20. The 2026-08-07 amendment
evaluates G6 as the Poisson-deconvolved attractiveness skew, and those cells
carry only the raw k-occurrence skew, so the candidate cannot be scored on the
mandatory G6 against them. PREREG_RC1 already anticipated a re-measurement for
the holdout-protocol fix. Real and candidate are therefore measured here under
identical code in the same run, which is the only way the ratio is meaningful.

Battery A only, the corpus-holdout battery. Battery B needs real held-out
queries and is a separate run; admission requires both, so **nothing is
admitted from this alone**. What it can do is fail the candidate, which is the
cheaper and more likely outcome and the reason to run it first.

Low signal is disclosed, not exempted. rho = n_query*k/n_base falls to 0.5 at
the top rung with k=10, where the deconvolution has little to work with. Every
cell reports rho and is flagged when its excess over the Poisson null falls
below 2.0, per spec/QUERY_BUDGET.md.

Env: R17G_OUT, R17G_TARGET, R17G_FROZEN, R17G_CALIB, R17G_ALPHA, R17G_DIM,
R17G_SUBS, R17G_CAP.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    hier_query_corpus,
)
from openvector_bench.geometry import (  # noqa: E402
    K_GRID,
    N_GRID,
    N_QUERY,
    load_target,
    measure,
    normalize,
    spectrum,
)

OUT = os.environ.get("R17G_OUT", "results/r17g_battery_cells.json")
TARGET = os.environ.get("R17G_TARGET", "/archive/tqp_real/wiki1024")
FROZEN = os.environ.get("R17G_FROZEN", "results/r14_frozen_corpus.json")
CALIB = os.environ.get("R17G_CALIB", "results/r17b_calibration.json")
ALPHA = float(os.environ.get("R17G_ALPHA", "0.38"))
DIM = int(os.environ.get("R17G_DIM", "1024"))
SUBS = int(os.environ.get("R17G_SUBS", "5"))
CAP = int(os.environ.get("R17G_CAP", str(max(N_GRID) * 3)))


def log(m: str) -> None:
    print(m, flush=True)


def main() -> None:
    params0 = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    cal = {
        a["growth"]: a["capacity"]
        for a in json.load(open(CALIB, encoding="utf-8"))["arms"]
    }
    if ALPHA not in cal:
        raise SystemExit(f"no calibrated capacity for alpha={ALPHA}: {list(cal)}")
    cap_c = cal[ALPHA]
    log("P-17cG BATTERY - capacity family vs real, identical code, battery A")
    log(f"alpha={ALPHA} (declared: midpoint of 17c's range), capacity={cap_c:.4g}")
    log(f"n_grid={N_GRID} k_grid={K_GRID} subs={SUBS} nq={N_QUERY} dim={DIM}")

    corpus, _ = load_target(TARGET, CAP)
    log(f"real corpus {corpus.shape}")
    eff, _ = spectrum(normalize(corpus[:50000]))
    log(f"real effective rank {eff:.1f}")

    # Uniform holdout, per the registered protocol fix. Taking the first rows
    # inherits Wikipedia's topical ordering and smuggles a concentrated query
    # marginal into a corpus-to-corpus battery.
    hold = min(N_QUERY * 2, len(corpus) // 10)
    hrng = np.random.default_rng(7)
    hidx = np.sort(hrng.choice(len(corpus), size=hold, replace=False))
    hmask = np.zeros(len(corpus), dtype=bool)
    hmask[hidx] = True
    real_q, real_base = corpus[hmask], corpus[~hmask]

    cells: list[dict] = []
    for sub in range(SUBS):
        for n in N_GRID:
            if n > len(real_base):
                log(f"  skip n={n}, real base has {len(real_base)}")
                continue
            for name, (b_raw, q_raw) in {
                "real": (real_base, real_q),
                "capacity": (None, None),
            }.items():
                if name == "capacity":
                    nq = min(N_QUERY * 2, max(1000, n // 10))
                    gen_n = int(round((n + nq) / (1.0 - QUERY_FRAC)))
                    pr = {**params0, "cluster_growth": ALPHA, "cluster_capacity": cap_c}
                    x = hier_query_corpus(pr, gen_n, DIM, 1000 + sub)
                    b_raw, q_raw = x[:n], x[n : n + nq]
                for c in measure(name, "A_corpus", b_raw, q_raw, n, sub):
                    d = c.__dict__ if hasattr(c, "__dict__") else dict(c)
                    cells.append(json.loads(json.dumps(d, default=float)))
            log(f"  sub {sub} n={n} done ({len(cells)} cells)")

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "meta": {
                    "what": "P-17cG battery A, capacity family vs re-measured real",
                    "alpha": ALPHA,
                    "capacity": cap_c,
                    "dim": DIM,
                    "subs": SUBS,
                    "n_grid": N_GRID,
                    "k_grid": K_GRID,
                    "n_query": N_QUERY,
                    "note": "battery A only; admission needs both batteries, so this "
                    "can fail the candidate but cannot admit it",
                },
                "cells": cells,
            },
            f,
            indent=1,
        )
    log(f"wrote {len(cells)} cells to {OUT}")
    log("R17G_BATTERY_DONE")


if __name__ == "__main__":
    main()
