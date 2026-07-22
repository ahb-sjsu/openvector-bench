"""Definitive falsification: can an elliptic curve generate embedding geometry?

Runs the real Cohere target and four generators through the IDENTICAL RC-1
battery and applies the registered §5 admission rule:

  real  ..........  the target (Cohere Embed-V3 Wikipedia, non-sealed rows)
  ec_ff ..........  finite-field EC scalar multiples (the cryptographic object)
  ec_torus .......  flat g-torus = product of real elliptic curves (geometric)
  gaussian_null ..  iid Gaussian shell (the reference null, §8.1)
  manifold_best ..  the best generator found so far (round-2 winner if present)

Grid: n ∈ {8k, 16k} (two points -> a scaling read), k ∈ {10, 30, 100}, both
batteries, N_SUB subsamples. For each (generator, battery, k, gate, n) it forms
R = T_gen / T_real with a subsampling interval and checks the mandatory gates
(G1, G5, G6) against the [0.85, 1.15] equivalence band. Reports which — if any —
generator is admitted, and for the rest, the mandatory gate it misses and by how
much. A miss is reported as a miss (PREREG_RC1 §1).

TRAIN/VALIDATION ONLY: the sealed 25% (hash of row index) is never loaded; this
is a screening grid (reduced n vs §3), decisive for the mandatory gates but not
the sealed RC-1 admission run. It never touches the seal.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np

from openvector_bench.ec_generators import (
    ec_ff_corpus,
    ec_torus_corpus,
    gaussian_null_corpus,
)
from openvector_bench.generator_search import (
    GATES,
    MANDATORY,
    manifold_corpus,
    measure_corpus,
)

TARGET_DIR = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
DIM = 1024
N_LIST = [int(x) for x in os.environ.get("N_LIST", "8000,16000").split(",")]
N_QUERY = int(os.environ.get("N_QUERY", "1000"))
N_SUB = int(os.environ.get("N_SUB", "3"))
KS = (10, 30, 100)
BATT = ("A", "B")
POOL = int(os.environ.get("POOL", "250000"))
SEED = 0
BAND = {"tight": (0.85, 1.15), "wide": (0.80, 1.20)}
WIDE_GATES = {"g2_id_ballgrowth", "g4_dims90", "g7_local_id_iqr"}

# Best manifold params: round-2 winner if the optimiser wrote one, else the corner.
_CORNER = {
    "latent_dim": 52.0,
    "amp": 0.6,
    "freq_scale": 4.09,
    "log2_clusters": 7.77,
    "size_tail": 1.54,
    "latent_spread": 0.61,
    "curvature": 2.99,
    "noise": 0.29,
}
if os.path.exists("ovb_gen_optimize.json"):
    with open("ovb_gen_optimize.json", encoding="utf-8") as f:
        _CORNER = json.load(f)["best"]["params"]

GENERATORS = {
    "ec_ff": (ec_ff_corpus, {"field_bits": 16}),
    "ec_torus": (ec_torus_corpus, {"latent_dim": 52.0}),
    "gaussian_null": (gaussian_null_corpus, {}),
    "manifold_best": (manifold_corpus, _CORNER),
}


def sealed(i: int) -> bool:
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def _nonsealed_indices(m: int) -> np.ndarray:
    return np.fromiter((i for i in range(m) if not sealed(i)), dtype=np.int64)


def band_for(gate: str) -> tuple[float, float]:
    return BAND["wide"] if gate in WIDE_GATES else BAND["tight"]


def measure(base, queries) -> dict:
    return measure_corpus(
        base, queries, ks=KS, kmax=max(KS), batteries=BATT, n_query=N_QUERY, seed=SEED
    )


def main() -> None:
    t0 = time.time()

    def log(msg: str) -> None:
        print(f"[{time.time() - t0:6.0f}s] {msg}", flush=True)

    log(f"loading non-sealed real pool from {TARGET_DIR}")
    parts = sorted(
        p
        for p in os.listdir(TARGET_DIR)
        if p.startswith("part_") and p.endswith(".npy")
    )
    arr = np.load(os.path.join(TARGET_DIR, parts[0]), mmap_mode="r")
    keep = _nonsealed_indices(min(POOL, len(arr)))
    qpath = os.path.join(TARGET_DIR, "queries.npy")
    real_q = (
        np.asarray(np.load(qpath)[:N_QUERY], np.float32)
        if os.path.exists(qpath)
        else None
    )
    log(
        f"battery-B real queries: {'queries.npy' if real_q is not None else 'held-out corpus points'}"
    )

    # profiles[gen][n][batt][k][gate] = list over subsamples
    profiles: dict = {name: {} for name in ["real", *GENERATORS]}
    for n in N_LIST:
        rng = np.random.default_rng(SEED + n)
        for name in profiles:
            profiles[name][n] = {
                b: {k: {g: [] for g in GATES} for k in KS} for b in BATT
            }
        for s in range(N_SUB):
            pick = np.sort(
                rng.choice(keep, size=min(n + N_QUERY, len(keep)), replace=False)
            )
            rb = np.asarray(arr[pick[:n]], np.float32)
            rq = (
                real_q
                if real_q is not None
                else np.asarray(arr[pick[n : n + N_QUERY]], np.float32)
            )
            runs = {"real": measure(rb, rq)}
            for name, (fn, pp) in GENERATORS.items():
                gb = fn(pp, n, DIM, 1000 * s + 1)
                gq = fn(pp, N_QUERY, DIM, 1000 * s + 2)
                runs[name] = measure(gb, gq)
            for name, prof in runs.items():
                for b in BATT:
                    for k in KS:
                        for g in GATES:
                            profiles[name][n][b][k][g].append(prof[b][k][g])
            log(f"  n={n} subsample {s + 1}/{N_SUB} measured ({len(runs)} corpora)")

    def real_mean(n, b, k, g):
        return float(np.mean(profiles["real"][n][b][k][g]))

    # Admission check + per-generator verdict
    verdicts: dict = {}
    for name in GENERATORS:
        cells = []  # every mandatory-gate cell
        worst = None
        for n in N_LIST:
            for b in BATT:
                for k in KS:
                    for g in MANDATORY:
                        rm = real_mean(n, b, k, g)
                        vals = np.array(profiles[name][n][b][k][g], float)
                        if rm == 0 or not np.isfinite(rm):
                            continue
                        r = vals / rm
                        lo_b, hi_b = band_for(g)
                        rlo, rhi = float(np.min(r)), float(np.max(r))
                        passed = rlo >= lo_b and rhi <= hi_b
                        cells.append(passed)
                        dev = max(abs(np.mean(r) - 1.0), 0)
                        if worst is None or dev > worst["dev"]:
                            worst = {
                                "gate": g,
                                "n": n,
                                "batt": b,
                                "k": k,
                                "ratio": float(np.mean(r)),
                                "dev": dev,
                            }
        admitted = all(cells) and len(cells) > 0
        # scaling: slope of log T vs log n for G1, G6 (need >=2 n)
        slopes = {}
        for g in ("g1_id_twonn", "g6_hubness_skew"):
            xs = np.log(N_LIST)
            gen_y = [
                np.log(max(np.mean(profiles[name][n]["B"][10][g]), 1e-9))
                for n in N_LIST
            ]
            real_y = [np.log(max(real_mean(n, "B", 10, g), 1e-9)) for n in N_LIST]
            if len(N_LIST) >= 2:
                slopes[g] = {
                    "gen": float(np.polyfit(xs, gen_y, 1)[0]),
                    "real": float(np.polyfit(xs, real_y, 1)[0]),
                }
        verdicts[name] = {
            "admitted": admitted,
            "worst_mandatory": worst,
            "slopes": slopes,
        }

    # Headline table at the reference cell (battery B, k=10, largest n)
    nref = N_LIST[-1]
    log("")
    log(
        f"=== mandatory-gate ratios at battery B, k=10, n={nref} (want R in [0.85,1.15]) ==="
    )
    hdr = "  ".join(g.split("_")[0].upper() for g in MANDATORY)
    log(f"  {'generator':14s}  {hdr}   admitted?")
    for name in ["real", *GENERATORS]:
        rs = []
        for g in MANDATORY:
            v = np.mean(profiles[name][nref]["B"][10][g])
            rm = real_mean(nref, "B", 10, g)
            rs.append("  1.00 " if name == "real" else f"{v / rm:5.2f}x")
        tag = (
            ""
            if name == "real"
            else ("  ADMITTED" if verdicts[name]["admitted"] else "  rejected")
        )
        log(f"  {name:14s}  {'  '.join(rs)}{tag}")

    out = {
        "target": TARGET_DIR,
        "grid": {
            "n": N_LIST,
            "k": list(KS),
            "subsamples": N_SUB,
            "batteries": list(BATT),
        },
        "real_ref": {g: real_mean(nref, "B", 10, g) for g in GATES},
        "verdicts": verdicts,
        "ref_ratios": {
            name: {
                g: float(
                    np.mean(profiles[name][nref]["B"][10][g])
                    / real_mean(nref, "B", 10, g)
                )
                for g in GATES
            }
            for name in GENERATORS
        },
        "battery_b_source": "queries.npy" if real_q is not None else "held-out-corpus",
        "seconds": round(time.time() - t0, 1),
    }
    with open("ec_experiment.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    log("wrote ec_experiment.json")
    print("EC_EXPERIMENT_DONE", flush=True)


if __name__ == "__main__":
    main()
