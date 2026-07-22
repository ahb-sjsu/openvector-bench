"""Round-2 refinement as a self-contained NRP swarm job (no corpus data needed).

Reads a precomputed real-target geometry profile (a few dozen numbers, staged via
ConfigMap), then runs a BOUNDED directed search over the decoupled manifold family
plus the structural-fuzzing adversary — entirely from synthetic corpora it
generates itself. No real embeddings, no GPU, no thermal budget: a swarm-class
CPU pod (<=1 CPU, <=2Gi) with unlimited replica headroom.

Env: TARGET (path to target json), N_BASE, N_QUERY, MAXFEV, MANIFOLD (JSON X0).
Prints the result between RESULT_JSON_BEGIN/END for `kubectl logs` collection.
"""

from __future__ import annotations

import json
import os

import numpy as np
from scipy.optimize import minimize

from openvector_bench.generator_search import (
    MANIFOLD_PARAMS,
    decode,
    make_evaluate_fn,
    manifold_corpus,
    measure_corpus,
)

TARGET = os.environ.get("TARGET", "/work/target_n8000.json")
N = int(os.environ.get("N_BASE", "8000"))
NQ = int(os.environ.get("N_QUERY", "1000"))
MAXFEV = int(os.environ.get("MAXFEV", "60"))
DIM = 1024
KS = (10,)
BATT = ("B",)
SPEC = MANIFOLD_PARAMS
NAMES = [n for n, _, _, _ in SPEC]
SHOW = ("g1_id_twonn", "g3_eff_rank", "g6_hubness_skew", "g8_pca_retention")
PROBE = ("amp", "freq_scale", "curvature", "latent_dim")
# Round-1 corner: good hubness/eff-rank, ID still high — the point to refine.
X0 = np.array(
    json.loads(os.environ.get("X0", "[52.0,0.6,4.09,7.77,1.54,0.61,2.99,0.29]"))
)


def main() -> None:
    raw = json.load(open(TARGET, encoding="utf-8"))
    target = {b: {int(k): v for k, v in raw[b].items()} for b in raw}
    real = target["B"][10]

    ev = make_evaluate_fn(
        target,
        dim=DIM,
        n=N,
        n_query=NQ,
        ks=KS,
        batteries=BATT,
        seed=0,
        generator=manifold_corpus,
        params_spec=SPEC,
    )
    n_eval = [0]

    def scal(x: np.ndarray) -> float:
        n_eval[0] += 1
        return ev(np.asarray(x, float))[0]

    # Bounded, directed local search from the corner (no runaway polish stage).
    res = minimize(
        scal,
        X0,
        method="Nelder-Mead",
        options={"maxfev": MAXFEV, "xatol": 1e-2, "fatol": 1e-3, "adaptive": True},
    )
    best = res.x

    def gates(px: np.ndarray) -> dict:
        p = decode(px, SPEC)
        return measure_corpus(
            manifold_corpus(p, N, DIM, 0),
            manifold_corpus(p, NQ, DIM, 1),
            ks=KS,
            batteries=BATT,
            n_query=NQ,
            seed=0,
        )["B"][10]

    bg = gates(best)

    adv: list[dict] = []
    try:
        from structural_fuzzing import find_adversarial_threshold

        for nm in PROBE:
            di = NAMES.index(nm)
            for r in find_adversarial_threshold(
                best, di, NAMES, ev, tolerance=0.4, n_steps=12
            ):
                adv.append(
                    {
                        "knob": nm,
                        "direction": r.direction,
                        "ratio": float(r.threshold_ratio),
                        "breaks_gate": r.target_flipped,
                    }
                )
    except Exception as exc:  # noqa: BLE001
        adv = [{"error": repr(exc)}]

    out = {
        "real": {g: real[g] for g in SHOW},
        "best_score": float(res.fun),
        "evals": int(n_eval[0]),
        "params": {nm: decode(best, SPEC)[nm] for nm in NAMES},
        "gates": {g: bg[g] for g in SHOW},
        "ratios": {g: bg[g] / real[g] for g in SHOW},
        "adversary": adv,
        "config": {"n": N, "n_query": NQ, "maxfev": MAXFEV},
    }
    print("RESULT_JSON_BEGIN")
    print(json.dumps(out, indent=2))
    print("RESULT_JSON_END")


if __name__ == "__main__":
    main()
