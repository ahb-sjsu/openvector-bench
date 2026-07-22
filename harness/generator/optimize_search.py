"""Round 2: directed optimizer + structural-fuzzing adversary on the DECOUPLED
manifold family.

Round 1 diagnosed two problems: (a) the single RFF ``freq_scale`` coupled
intrinsic dimension to effective rank, and (b) random search over the knobs was
too weak to find the good corner. This driver addresses both:

* the family now splits the immersion into a LINEAR part (pins intrinsic
  dimension = ``latent_dim``) and an ``amp``-weighted high-frequency part (raises
  effective rank / breaks low-rank), so the search can move G1 and G3 apart; and
* a DIRECTED global optimizer (differential evolution, warm-started from the
  round-1 corner) replaces random search, then the real **structural-fuzzing**
  adversary (``find_adversarial_threshold``) nudges the winner's knobs until a
  gate breaks -- an anti-Goodhart robustness check that a lucky spike would fail.

TRAIN/VALIDATION ONLY: the sealed 25% (PREREG_RC1 §7, hash of row index) is never
loaded. This is a fitting signal, not RC-1 admission, and never touches the seal.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np
from scipy.optimize import differential_evolution

from openvector_bench.generator_search import (
    MANIFOLD_PARAMS,
    decode,
    make_evaluate_fn,
    manifold_corpus,
    measure_corpus,
)

TARGET_DIR = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
DIM = 1024
N_BASE = int(os.environ.get("N_BASE", "12000"))
N_QUERY = int(os.environ.get("N_QUERY", "1500"))
MAXITER = int(os.environ.get("MAXITER", "5"))
POPSIZE = int(os.environ.get("POPSIZE", "5"))
POOL = int(os.environ.get("POOL", "250000"))
KS = (10,)
SEED = 0
BATT = ("B",)
SPEC = MANIFOLD_PARAMS
NAMES = [n for n, _, _, _ in SPEC]
SHOW = ("g1_id_twonn", "g3_eff_rank", "g6_hubness_skew", "g8_pca_retention")
# Round-1 corner (good hubness/eff-rank, bad ID), with latent_dim pulled toward the
# real intrinsic dimension and amp seeded -- a warm start for the directed search.
X0 = np.array([52.0, 0.6, 4.09, 7.77, 1.54, 0.61, 2.99, 0.29])
# Knobs whose robustness we probe adversarially (structural / mandatory-gate drivers).
PROBE = ("amp", "freq_scale", "curvature", "latent_dim")


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

    log(f"loading non-sealed real target from {TARGET_DIR}  (n={N_BASE})")
    pool = load_nonsealed(TARGET_DIR, N_BASE + N_QUERY)
    base, queries = pool[:N_BASE], pool[N_BASE : N_BASE + N_QUERY]
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
        generator=manifold_corpus,
        params_spec=SPEC,
    )
    n_eval = [0]

    def scal(x: np.ndarray) -> float:
        n_eval[0] += 1
        return ev(np.asarray(x, dtype=float))[0]

    def measure_point(params: np.ndarray) -> dict[str, float]:
        p = decode(params, SPEC)
        return measure_corpus(
            manifold_corpus(p, N_BASE, DIM, SEED),
            manifold_corpus(p, N_QUERY, DIM, SEED + 1),
            ks=KS,
            batteries=BATT,
            n_query=N_QUERY,
            seed=SEED,
        )["B"][10]

    def show(name: str, params: np.ndarray) -> dict[str, float]:
        s = ev(params)[0]
        gen = measure_point(params)
        cells = "  ".join(
            f"{g.split('_')[0].upper()}={gen[g]:.2f}(x{gen[g] / real[g]:.2f})"
            for g in SHOW
        )
        log(f"  {name:9s} score={s:6.3f}  {cells}")
        return gen

    log("warm start (round-1 corner, latent_dim->52, amp seeded):")
    show("X0", X0)

    bounds = [(lo, hi) for _, lo, hi, _ in SPEC]
    log(
        f"directed search: differential evolution (maxiter={MAXITER} popsize={POPSIZE})"
    )
    de_kw = dict(
        maxiter=MAXITER,
        popsize=POPSIZE,
        tol=0.02,
        seed=SEED,
        polish=True,
        mutation=(0.5, 1.0),
        recombination=0.7,
    )
    try:
        res = differential_evolution(scal, bounds, x0=X0, init="sobol", **de_kw)
    except TypeError:  # older scipy without x0
        res = differential_evolution(scal, bounds, **de_kw)
    best_p, best_s = res.x, float(res.fun)
    log(f"DE done in {n_eval[0]} evals; best score={best_s:.4f}")
    best_gen = show("BEST", best_p)

    # --- structural-fuzzing adversary: nudge each critical knob until a gate breaks
    log("structural-fuzzing adversary (find_adversarial_threshold, tol=0.4):")
    adv: list[dict] = []
    try:
        from structural_fuzzing import find_adversarial_threshold

        for nm in PROBE:
            di = NAMES.index(nm)
            for r in find_adversarial_threshold(
                best_p, di, NAMES, ev, tolerance=0.4, n_steps=14
            ):
                adv.append(
                    {
                        "knob": nm,
                        "direction": r.direction,
                        "ratio": float(r.threshold_ratio),
                        "breaks_gate": r.target_flipped,
                    }
                )
                log(
                    f"    {nm:12s} {r.direction:8s} x{r.threshold_ratio:5.2f} -> breaks {r.target_flipped}"
                )
        if not adv:
            log("    no gate broke within +/-1000x on any probed knob (robust)")
    except Exception as exc:  # noqa: BLE001 - report, don't crash the run
        log(f"    structural-fuzzing unavailable ({exc!r}); skipping adversary")
        adv = [{"error": repr(exc)}]

    out = {
        "family": "manifold_decoupled",
        "optimizer": "differential_evolution",
        "real": {g: real[g] for g in SHOW},
        "best": {
            "score": best_s,
            "params": {nm: decode(best_p, SPEC)[nm] for nm in NAMES},
            "gates": {g: best_gen[g] for g in SHOW},
            "ratios": {g: best_gen[g] / real[g] for g in SHOW},
        },
        "adversary": adv,
        "config": {
            "n_base": N_BASE,
            "n_query": N_QUERY,
            "de_evals": n_eval[0],
            "maxiter": MAXITER,
            "popsize": POPSIZE,
            "battery": "B",
        },
        "seconds": round(time.time() - t0, 1),
    }
    with open("ovb_gen_optimize.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    log("wrote ovb_gen_optimize.json")
    print("OPTIMIZE_DONE", flush=True)


if __name__ == "__main__":
    main()
