"""Exploratory generator search on the REAL Cohere target.

Confirms the fitness loop MOVES the mandatory RC-1 gates (G1 intrinsic dimension,
G6 hubness) before wiring the full Theory-Radar x structural-fuzzing engines. A
plain random search over the synth_corpus knobs is enough to answer "can the
substrate reach hubness closer to real than the low-rank recipe?".

TRAIN/VALIDATION ONLY: the sealed 25% (PREREG_RC1 §7, hash of row index) is never
loaded. This is a fitting signal, not RC-1 admission, and never touches the seal.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np

from openvector_bench.generator_search import (
    PARAMS,
    decode,
    make_evaluate_fn,
    measure_corpus,
    synth_corpus,
)

TARGET_DIR = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
DIM = 1024
N_BASE = int(os.environ.get("N_BASE", "15000"))
N_QUERY = int(os.environ.get("N_QUERY", "1500"))
N_EVALS = int(os.environ.get("N_EVALS", "50"))
POOL = int(os.environ.get("POOL", "250000"))
KS = (10,)
SEED = 0
BATT = ("B",)  # query->corpus; the harder battery, halves exploratory cost


def sealed(i: int) -> bool:
    """PREREG §7: hash of row index -> train/val/sealed. True = the untouchable 25%."""
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def load_nonsealed(path: str, need: int) -> np.ndarray:
    parts = sorted(
        p for p in os.listdir(path) if p.startswith("part_") and p.endswith(".npy")
    )
    a = np.load(os.path.join(path, parts[0]), mmap_mode="r")
    m = min(POOL, len(a))
    keep = np.fromiter((i for i in range(m) if not sealed(i)), dtype=np.int64)
    rng = np.random.default_rng(SEED)
    pick = np.sort(rng.choice(keep, size=min(need, len(keep)), replace=False))
    return np.asarray(a[pick], dtype=np.float32)


def main() -> None:
    t0 = time.time()

    def log(msg: str) -> None:
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    log(f"loading non-sealed real target from {TARGET_DIR}")
    pool = load_nonsealed(TARGET_DIR, N_BASE + N_QUERY)
    base, queries = pool[:N_BASE], pool[N_BASE : N_BASE + N_QUERY]
    log(f"base={base.shape} queries={queries.shape}")

    target = measure_corpus(
        base, queries, ks=KS, batteries=BATT, n_query=N_QUERY, seed=SEED
    )
    real_g1 = target["B"][10]["g1_id_twonn"]
    real_g6 = target["B"][10]["g6_hubness_skew"]
    log(
        f"REAL target (battery B, k=10): G1 id_twonn={real_g1:.2f}  G6 hubness={real_g6:.2f}"
    )

    ev = make_evaluate_fn(
        target, dim=DIM, n=N_BASE, n_query=N_QUERY, ks=KS, batteries=BATT, seed=SEED
    )

    def measure_point(params):
        p = decode(params)
        gen = measure_corpus(
            synth_corpus(p, N_BASE, DIM, SEED),
            synth_corpus(p, N_QUERY, DIM, SEED + 1),
            ks=KS,
            batteries=BATT,
            n_query=N_QUERY,
            seed=SEED,
        )["B"][10]
        return gen["g1_id_twonn"], gen["g6_hubness_skew"]

    def report(name, params):
        s, _ = ev(params)
        g1, g6 = measure_point(params)
        log(
            f"  {name:10s} score={s:5.3f}  "
            f"G1={g1:6.2f} (x{g1 / real_g1:4.2f})  G6={g6:7.2f} (x{g6 / real_g6:5.2f})"
        )
        return s, g1, g6

    log("baselines:")
    low = np.array(
        [0.0, 0.0, 2.5, 1.0, 0.05]
    )  # 1 cluster, steep spectrum ~ null_lowrank
    report("low-rank", low)
    report("default", np.array([d for _, _, _, d in PARAMS]))

    log(f"random search ({N_EVALS} evals over {len(PARAMS)} knobs)")
    rng = np.random.default_rng(SEED)
    best_s, best_p = float("inf"), None
    for e in range(N_EVALS):
        params = np.array([rng.uniform(lo, hi) for _, lo, hi, _ in PARAMS])
        s, _ = ev(params)
        if s < best_s:
            best_s, best_p = s, params
            log(f"    eval {e + 1}/{N_EVALS}  NEW BEST score={s:.3f}")

    log("best found:")
    bs, bg1, bg6 = report("BEST", best_p)

    out = {
        "real": {"g1_id_twonn": real_g1, "g6_hubness_skew": real_g6},
        "best": {
            "score": best_s,
            "params": {name: decode(best_p)[name] for name, *_ in PARAMS},
            "g1_id_twonn": bg1,
            "g6_hubness_skew": bg6,
            "g1_ratio": bg1 / real_g1,
            "g6_ratio": bg6 / real_g6,
        },
        "config": {
            "n_base": N_BASE,
            "n_query": N_QUERY,
            "n_evals": N_EVALS,
            "battery": "B",
        },
        "seconds": round(time.time() - t0, 1),
    }
    with open("ovb_gen_explore.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    log("wrote ovb_gen_explore.json")
    print("EXPLORE_DONE", flush=True)


if __name__ == "__main__":
    main()
