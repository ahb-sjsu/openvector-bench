"""Exploratory generator search on the REAL Cohere target.

Confirms the fitness loop moves the mandatory RC-1 gates before wiring the full
Theory-Radar x structural-fuzzing engines. Random search over a chosen generator
family's knobs; reports the mandatory gates (G1 intrinsic dimension, G6 hubness)
plus the spectral gates (G3 effective rank, G8 PCA retention) so a low-rank
"cheat" is visible.

Select the family with ``FAMILY=synth`` (round 0, cluster Gaussians) or
``FAMILY=manifold`` (round 1, nonlinear low-dim manifold + optional hyperbolic
latent). TRAIN/VALIDATION ONLY: the sealed 25% (PREREG_RC1 §7, hash of row index)
is never loaded; this is a fitting signal, not RC-1 admission, and never touches
the seal.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np

from openvector_bench.generator_search import (
    MANIFOLD_PARAMS,
    PARAMS,
    decode,
    make_evaluate_fn,
    manifold_corpus,
    measure_corpus,
    synth_corpus,
)

TARGET_DIR = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
FAMILY = os.environ.get("FAMILY", "manifold")
DIM = 1024
N_BASE = int(os.environ.get("N_BASE", "15000"))
N_QUERY = int(os.environ.get("N_QUERY", "1500"))
N_EVALS = int(os.environ.get("N_EVALS", "60"))
POOL = int(os.environ.get("POOL", "250000"))
KS = (10,)
SEED = 0
BATT = ("B",)
GEN, SPEC = (
    (manifold_corpus, MANIFOLD_PARAMS)
    if FAMILY == "manifold"
    else (synth_corpus, PARAMS)
)
SHOW = ("g1_id_twonn", "g3_eff_rank", "g6_hubness_skew", "g8_pca_retention")


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

    log(f"family={FAMILY}  loading non-sealed real target from {TARGET_DIR}")
    pool = load_nonsealed(TARGET_DIR, N_BASE + N_QUERY)
    base, queries = pool[:N_BASE], pool[N_BASE : N_BASE + N_QUERY]
    log(f"base={base.shape} queries={queries.shape}")

    target = measure_corpus(
        base, queries, ks=KS, batteries=BATT, n_query=N_QUERY, seed=SEED
    )
    real = target["B"][10]
    log(
        "REAL target (battery B, k=10): "
        + "  ".join(f"{g}={real[g]:.2f}" for g in SHOW)
    )

    ev = make_evaluate_fn(
        target,
        dim=DIM,
        n=N_BASE,
        n_query=N_QUERY,
        ks=KS,
        batteries=BATT,
        seed=SEED,
        generator=GEN,
        params_spec=SPEC,
    )

    def measure_point(params):
        p = decode(params, SPEC)
        return measure_corpus(
            GEN(p, N_BASE, DIM, SEED),
            GEN(p, N_QUERY, DIM, SEED + 1),
            ks=KS,
            batteries=BATT,
            n_query=N_QUERY,
            seed=SEED,
        )["B"][10]

    def report(name, params):
        s, _ = ev(params)
        gen = measure_point(params)
        cells = "  ".join(
            f"{g.split('_')[0].upper()}={gen[g]:.2f}(x{gen[g] / real[g]:.2f})"
            for g in SHOW
        )
        log(f"  {name:9s} score={s:5.3f}  {cells}")
        return s, gen

    log("baseline (family defaults):")
    report("default", np.array([d for _, _, _, d in SPEC]))

    log(f"random search ({N_EVALS} evals over {len(SPEC)} knobs)")
    rng = np.random.default_rng(SEED)
    best_s, best_p = float("inf"), None
    for e in range(N_EVALS):
        params = np.array([rng.uniform(lo, hi) for _, lo, hi, _ in SPEC])
        s, _ = ev(params)
        if s < best_s:
            best_s, best_p = s, params
            log(f"    eval {e + 1}/{N_EVALS}  NEW BEST score={s:.3f}")

    log("best found:")
    _, best_gen = report("BEST", best_p)

    out = {
        "family": FAMILY,
        "real": {g: real[g] for g in SHOW},
        "best": {
            "score": best_s,
            "params": {name: decode(best_p, SPEC)[name] for name, *_ in SPEC},
            "gates": {g: best_gen[g] for g in SHOW},
            "ratios": {g: best_gen[g] / real[g] for g in SHOW},
        },
        "config": {
            "n_base": N_BASE,
            "n_query": N_QUERY,
            "n_evals": N_EVALS,
            "battery": "B",
        },
        "seconds": round(time.time() - t0, 1),
    }
    with open(f"ovb_gen_{FAMILY}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    log(f"wrote ovb_gen_{FAMILY}.json")
    print("EXPLORE_DONE", flush=True)


if __name__ == "__main__":
    main()
