"""Screening probe: do sharded lookup tables + a designed (Mahalanobis) spectrum
crack the G1 wall that the continuous families (EC, stratified) hit?

PRE-REGISTERED (written before the run; see the PREDICTION block printed at start):
the load-bearing claim is that DISCRETE, combinatorial neighbourhoods let the
two-NN estimator read a low, controllable intrinsic dimension at n=8k, where an
undersampled continuous patch reads the ambient dimension (~325).

  PRIMARY (make-or-break): G1 tracks d_latent; at d_latent=61, G1 in [40, 110].
    FALSIFIED if G1 >= 200 (same wall), <= 8 (duplicate collapse), or flat vs d_latent.
  DECOUPLING: G3 is set by the designed-Sigma spectrum, ~independent of d_latent.
  HEALTH: frac_unique_cells > 0.5 (no mass collapse); G6 > 1.

Screening grid only (reduced n); never touches the sealed set. TRAIN/VALIDATION.
"""

from __future__ import annotations

import json
import time

import numpy as np

from openvector_bench.generator_search import GATES, measure_corpus
from openvector_bench.geometry import id_twonn, knn, normalize, spectrum

DIM = 1024
N = 8000
NQ = 1000

# real_ref: battery B, k=10, n=16000 (results/ec_experiment.json)
REAL = {
    "g1_id_twonn": 61.38,
    "g2_id_ballgrowth": 14.51,
    "g3_eff_rank": 189.96,
    "g4_dims90": 360.0,
    "g5_relative_contrast": 1.204,
    "g6_hubness_skew": 9.44,
    "g7_local_id_iqr": 25.57,
    "g8_pca_retention": 0.609,
}

DEFAULT = {
    "d_latent": 61,
    "shards": 64,
    "codebook": 16,
    "n_clusters": 256,
    "size_tail": 1.3,
    "within_noise": 0.20,  # > sqrt(w/dim) so cell-mates sit FARTHER than single-shard flips
    "curvature": 1.5,
    "spectrum_decay": 0.0,  # 0 = no Mahalanobis colouring (isolate the discrete mechanism)
}


def _clustered_latent(rng, n, d, n_clusters, size_tail, curvature):
    """A clustered, heavy-tailed latent (hubness); optional hyperbolic exp_0 layout."""
    w = np.arange(1, n_clusters + 1, dtype=np.float64) ** (-size_tail)
    w /= w.sum()
    counts = rng.multinomial(n, w)
    centres = rng.standard_normal((n_clusters, d)).astype(np.float32)
    row_c = np.repeat(np.arange(n_clusters), counts)
    z = centres[row_c] + 0.5 * rng.standard_normal((n, d)).astype(np.float32)
    if curvature > 0:
        c = np.float32(curvature)
        vn = np.linalg.norm(z, axis=1, keepdims=True).astype(np.float32)
        z = z * (np.tanh(np.sqrt(c) * vn) / (np.sqrt(c) * np.maximum(vn, 1e-9)))
    return z


def codebook_corpus(p: dict, n: int, dim: int, seed: int):
    """Sharded lookup-table corpus with an optional designed (Mahalanobis) spectrum.

    A d_latent-dim clustered latent drives, per shard, a quantised index into that
    shard's random codebook; the row is the concatenation of the looked-up sub-
    vectors plus a small continuous residual (so cell-mates are not exact
    duplicates). The backbone is thus a *piecewise-constant* function of a
    d_latent-dim latent: nearest neighbours differ by single-shard flips whose
    directions are confined to the latent's d_latent-dim image -- a discrete lattice
    the two-NN estimator can read regardless of sampling density. An optional
    power-law colouring in a random basis sets the ambient spectrum (G3/G4).
    """
    rng = np.random.default_rng(seed)
    d_latent = int(p["d_latent"])
    m_shards = int(p["shards"])
    k_code = int(p["codebook"])
    w = dim // m_shards
    z = _clustered_latent(
        rng, n, d_latent, int(p["n_clusters"]), p["size_tail"], p["curvature"]
    )
    a_proj = rng.standard_normal((m_shards, d_latent)).astype(np.float32)
    proj = z @ a_proj.T  # (n, shards)
    idx = np.empty((n, m_shards), dtype=np.int64)
    for m in range(m_shards):  # quantile bins -> uniform codebook occupancy
        edges = np.quantile(proj[:, m], np.linspace(0.0, 1.0, k_code + 1)[1:-1])
        idx[:, m] = np.searchsorted(edges, proj[:, m])
    codebooks = rng.standard_normal((m_shards, k_code, w)).astype(np.float32)
    x = np.zeros((n, dim), dtype=np.float32)
    for m in range(m_shards):
        x[:, m * w : (m + 1) * w] = codebooks[m][idx[:, m]]
    x += np.float32(p["within_noise"]) * rng.standard_normal((n, dim)).astype(
        np.float32
    )
    if p.get("spectrum_decay", 0.0) > 0:  # designed Mahalanobis spectrum
        q_basis, _ = np.linalg.qr(rng.standard_normal((dim, dim)).astype(np.float32))
        s = np.arange(1, dim + 1, dtype=np.float32) ** (
            -np.float32(p["spectrum_decay"])
        )
        s /= s.max()
        x = ((x @ q_basis) * s) @ q_basis.T
    rng.shuffle(x)
    frac_unique = len(np.unique(idx, axis=0)) / n
    return normalize(x), frac_unique


def g1_g3(p, seed=1):
    base, frac = codebook_corpus(p, N, DIM, seed)
    q, _ = codebook_corpus(p, NQ, DIM, seed + 1)
    d, _ = knn(base, q, 2)
    eff, _ = spectrum(base[:50000])
    return id_twonn(d), float(eff), frac


def full_gates(p, seed=1):
    base, frac = codebook_corpus(p, N, DIM, seed)
    q, _ = codebook_corpus(p, NQ, DIM, seed + 1)
    prof = measure_corpus(base, q, ks=(10,), batteries=("B",))["B"][10]
    return prof, frac


def main():
    t0 = time.time()

    def log(m):
        print(f"[{time.time() - t0:6.0f}s] {m}", flush=True)

    log("PREDICTION: G1 tracks d_latent; at d_latent=61, G1 in [40,110].")
    log("  FALSIFIED if G1>=200 (same wall), <=8 (collapse), or flat vs d_latent.")
    out = {
        "real_ref": REAL,
        "prediction": "G1 in [40,110] at d_latent=61; tracks d_latent",
    }

    log("=== PRIMARY: G1 vs d_latent (colouring OFF) ===")
    sweep = []
    for d in (20, 40, 61, 90):
        p = {**DEFAULT, "d_latent": d}
        g1, g3, frac = g1_g3(p)
        sweep.append({"d_latent": d, "g1": g1, "g3": g3, "frac_unique_cells": frac})
        log(f"  d_latent={d:3d}  G1={g1:7.1f}  G3={g3:6.1f}  unique_cells={frac:.2f}")
    out["g1_vs_dlatent"] = sweep

    log("=== FULL GATES at d_latent=61 (Mahalanobis colouring ON, decay=1.0) ===")
    prof, frac = full_gates({**DEFAULT, "spectrum_decay": 1.0})
    row = {g: prof[g] for g in GATES}
    row["frac_unique_cells"] = frac
    out["full_gates_dlatent61"] = row
    for g in GATES:
        log(f"  {g:22s} {prof[g]:8.2f}  ({prof[g] / REAL[g]:5.2f}x real)")

    log("=== DECOUPLING: vary spectrum_decay at d_latent=61 (G3 moves, G1 stays?) ===")
    dec = []
    for sd in (0.0, 0.5, 1.0):
        g1, g3, _ = g1_g3({**DEFAULT, "spectrum_decay": sd})
        dec.append({"spectrum_decay": sd, "g1": g1, "g3": g3})
        log(f"  decay={sd:.1f}  G1={g1:7.1f}  G3={g3:6.1f}")
    out["decoupling"] = dec

    out["seconds"] = round(time.time() - t0, 1)
    with open("results/codebook_probe.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    log("wrote results/codebook_probe.json")
    print("CODEBOOK_PROBE_DONE", flush=True)


if __name__ == "__main__":
    main()
