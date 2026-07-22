"""Fan-out random search over a generator family — one seed-shard per NRP swarm pod.

An Indexed Job runs M swarm-class pods (<=1 CPU, <=2Gi -> unlimited replicas, no
thermal budget); each reads ``JOB_COMPLETION_INDEX`` for a distinct RNG seed and
searches a different slice of the knob space, printing its best between
RESULT_JSON_BEGIN/END. Collect all M pods' logs and take the global min. Fully
self-contained: the small real-target geometry profile is staged via ConfigMap;
the pod generates its own synthetic corpora (no corpus data, no GPU).

Env: FAMILY (concentration|manifold|synth), TARGET, N_BASE, N_QUERY, N_EVALS.
"""

from __future__ import annotations

import json
import os

import numpy as np

from openvector_bench.generator_search import (
    CONCENTRATION_PARAMS,
    MANIFOLD_PARAMS,
    PARAMS,
    concentration_corpus,
    decode,
    make_evaluate_fn,
    manifold_corpus,
    measure_corpus,
    synth_corpus,
)

FAMILIES = {
    "concentration": (concentration_corpus, CONCENTRATION_PARAMS),
    "manifold": (manifold_corpus, MANIFOLD_PARAMS),
    "synth": (synth_corpus, PARAMS),
}
FAMILY = os.environ.get("FAMILY", "concentration")
GEN, SPEC = FAMILIES[FAMILY]
TARGET = os.environ.get("TARGET", "/work/target_n8000.json")
N = int(os.environ.get("N_BASE", "8000"))
NQ = int(os.environ.get("N_QUERY", "1000"))
N_EVALS = int(os.environ.get("N_EVALS", "40"))
SHARD = int(os.environ.get("JOB_COMPLETION_INDEX", os.environ.get("SHARD", "0")))
DIM = 1024
KS = (10,)
BATT = ("B",)
NAMES = [n for n, _, _, _ in SPEC]
SHOW = ("g1_id_twonn", "g3_eff_rank", "g6_hubness_skew", "g8_pca_retention")


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
        generator=GEN,
        params_spec=SPEC,
    )
    rng = np.random.default_rng(1000 + SHARD)

    trials = []
    if SHARD == 0:  # anchor the sweep with the family defaults
        trials.append(np.array([d for _, _, _, d in SPEC]))
    for _ in range(N_EVALS):
        trials.append(np.array([rng.uniform(lo, hi) for _, lo, hi, _ in SPEC]))

    best_s, best_p = float("inf"), trials[0]
    for params in trials:
        s = ev(params)[0]
        if s < best_s:
            best_s, best_p = s, params

    p = decode(best_p, SPEC)
    full = GEN(p, N + NQ, DIM, 0)  # same-instance base + held-out queries
    prof = measure_corpus(
        full[:N],
        full[N:],
        ks=KS,
        batteries=BATT,
        n_query=NQ,
        seed=0,
    )["B"][10]
    out = {
        "shard": SHARD,
        "family": FAMILY,
        "best_score": best_s,
        "params": {nm: p[nm] for nm in NAMES},
        "ratios": {g: prof[g] / real[g] for g in SHOW},
        "gates": {g: prof[g] for g in SHOW},
    }
    print("RESULT_JSON_BEGIN")
    print(json.dumps(out, indent=2))
    print("RESULT_JSON_END")


if __name__ == "__main__":
    main()
