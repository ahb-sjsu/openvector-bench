# SPDX-License-Identifier: MIT
"""Geometry-match fitness for procedural-corpus discovery.

Turns *"find a generator whose geometry matches real embeddings (RC-1)"* into a
single ``evaluate_fn(params) -> (score, per-gate errors)`` — the shared contract
that a **searcher** (e.g. Theory Radar) and an **adversary**
(`structural-fuzzing`) both plug into. See ``spec/GENERATOR_SEARCH.md`` for the
method (an anti-Goodhart, adversarial generator-discovery loop) and its limits.

The score reuses OpenVector Bench's *own* geometry battery (`geometry.py`), so it
is the real RC-1 objective, not a re-implementation. It is a **fitting** signal
on train/validation only; the discrete RC-1 admission (`score_rc1.py`) and the
sealed RC-2 test remain the registered judges — this module never touches them.

Honest scope: this scaffolds the search substrate + fitness. It does **not** ship
a generator that passes RC-1 (none exists yet), and matching the battery does not
prove a generator is right — that is exactly what the sealed test is for.
"""

from __future__ import annotations

import numpy as np

from .geometry import (
    hubness,
    id_ball_growth,
    id_local,
    id_twonn,
    knn,
    normalize,
    pca_retention,
    relative_contrast,
    spectrum,
)

# The eight registered geometric gates (PREREG_RC1 §5). G1/G5/G6 are mandatory —
# they govern ANN difficulty and must pass in every cell — so the fitness
# up-weights them.
GATES: tuple[str, ...] = (
    "g1_id_twonn",
    "g2_id_ballgrowth",
    "g3_eff_rank",
    "g4_dims90",
    "g5_relative_contrast",
    "g6_hubness_skew",
    "g7_local_id_iqr",
    "g8_pca_retention",
)
MANDATORY: frozenset[str] = frozenset(
    {"g1_id_twonn", "g5_relative_contrast", "g6_hubness_skew"}
)

# Parametric generator (name, lo, hi, default) — the search substrate. Each knob
# moves the geometry a searcher/fuzzer cares about; the mechanism for HUBNESS is
# the heavy-tailed cluster sizes (density gradients), for COMPRESSIBILITY the
# within-cluster power-law spectrum, and the noise floor keeps it off any exact
# low-rank subspace (the flaw that sinks `null_lowrank`).
PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("log2_clusters", 0.0, 12.0, 6.0),  # 2**this cluster centres
    ("size_tail", 0.0, 2.5, 1.1),  # Zipf exponent on cluster sizes -> hubness
    ("spectrum_decay", 0.1, 3.0, 1.0),  # within-cluster eigenvalue power law
    ("cluster_spread", 0.02, 1.0, 0.30),  # within-cluster scale
    ("noise", 0.0, 0.5, 0.05),  # isotropic floor -> not exactly low-rank
)
_INACTIVE = 1e6  # structural-fuzzing convention: params >= 1e6 are "off"


def decode(params: np.ndarray, spec=PARAMS) -> dict[str, float]:
    """A parameter vector (structural-fuzzing convention) -> named knobs.

    A value ``>= 1e6`` (or a missing entry) turns that knob off, restoring its
    default, so a fuzzer can ablate dimensions exactly as it does for any model.
    ``spec`` selects the generator family's (name, lo, hi, default) layout.
    """
    p = np.asarray(params, dtype=float).ravel()
    out: dict[str, float] = {}
    for i, (name, lo, hi, dflt) in enumerate(spec):
        v = float(p[i]) if i < len(p) else _INACTIVE
        out[name] = dflt if v >= _INACTIVE else float(np.clip(v, lo, hi))
    return out


def synth_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """A byte-reproducible synthetic corpus from decoded knobs ``p``.

    Heavy-tailed cluster sizes create the density gradients that produce hubness;
    a power-law within-cluster spectrum sets effective rank / compressibility; an
    isotropic noise floor keeps it off any exact subspace. Returned unit-normed.
    """
    rng = np.random.default_rng(seed)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n)
    w = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-p["size_tail"])
    w /= w.sum()
    counts = rng.multinomial(n, w)
    centres = normalize(rng.standard_normal((k_clusters, dim)).astype(np.float32))
    eig = np.arange(1, dim + 1, dtype=np.float32) ** (-p["spectrum_decay"])
    eig /= eig.max()
    row_cluster = np.repeat(np.arange(k_clusters), counts)
    z = rng.standard_normal((n, dim)).astype(np.float32) * eig
    x = centres[row_cluster] + np.float32(p["cluster_spread"]) * z
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x)  # de-correlate row order from cluster order
    return normalize(x)


# Round-1 family: a nonlinear low-dimensional manifold. `synth_corpus` (clusters
# of anisotropic Gaussians) fills too many dimensions to reach real embeddings'
# ~52-dim intrinsic dimension (see results/GEN_EXPLORE_ROUND0.md). Here the
# intrinsic dimension is set *directly* by a `latent_dim`-dimensional latent,
# lifted to the ambient space through random Fourier features -- a smooth CURVED
# immersion, so the ambient effective rank stays high and the corpus is NOT
# trivially PCA-compressible (the flaw that sinks a linear low-rank map), while
# the local intrinsic dimension tracks the latent. Clustered, heavy-tailed latent
# density supplies hubness. Byte-reproducible from `(seed, row)` like every family.
MANIFOLD_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    (
        "latent_dim",
        8.0,
        200.0,
        52.0,
    ),  # sets intrinsic dimension via the LINEAR part (G1)
    (
        "amp",
        0.0,
        3.0,
        0.6,
    ),  # weight of the high-freq part -> eff-rank / PCA-break, DECOUPLED from ID
    (
        "freq_scale",
        0.2,
        6.0,
        2.0,
    ),  # character of the high-freq part (how curved the immersion is)
    (
        "log2_clusters",
        0.0,
        12.0,
        7.0,
    ),  # density gradients on the latent -> hubness (G6)
    ("size_tail", 0.0, 2.5, 1.3),  # heavy-tailed cluster sizes -> hubness
    ("latent_spread", 0.05, 1.5, 0.5),  # within-cluster latent scale
    (
        "curvature",
        0.0,
        3.0,
        1.5,
    ),  # 0 = Euclidean latent; >0 = hyperbolic (Poincare exp_0) -> hubness
    ("noise", 0.0, 0.3, 0.03),  # off-manifold floor
)
_N_FREQ = 2048  # random-Fourier feature count (fixed; freq_scale tunes curvature)


def manifold_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """A byte-reproducible nonlinear-manifold corpus from decoded knobs ``p``.

    Latent (clustered, heavy-tailed for hubness; optional Poincare exp_0 map) is
    lifted to ambient by a DECOUPLED immersion:

        x = z @ A_lin  +  amp * (cos(z @ W_hf + b) @ A_hf)

    The linear term pins the *local* intrinsic dimension to ``latent_dim`` (a
    linear map preserves local dimension -> G1), while the ``amp``-scaled
    high-frequency term spreads the ambient spectrum (effective rank, G3) and
    breaks the low-rank structure (PCA retention, G8) SEPARATELY. Round 1's single
    RFF ``freq_scale`` pulled ID and eff-rank together; splitting the immersion and
    weighting the nonlinear part by ``amp`` is what lets the search hit low ID and
    high eff-rank at once. Unit-normed.
    """
    rng = np.random.default_rng(seed)
    d_latent = min(max(2, int(round(p["latent_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n)
    w = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-p["size_tail"])
    w /= w.sum()
    counts = rng.multinomial(n, w)
    centres = rng.standard_normal((k_clusters, d_latent)).astype(np.float32)
    row_cluster = np.repeat(np.arange(k_clusters), counts)
    z = centres[row_cluster] + np.float32(p["latent_spread"]) * rng.standard_normal(
        (n, d_latent)
    ).astype(np.float32)
    if p["curvature"] > 0:
        # Map the latent into the Poincare ball via exp_0 (geometric-methods Ch 3):
        # the conformal factor packs most points near the boundary while a few sit
        # central -- the boundary/hub structure of hierarchical data, hence hubness.
        c = np.float32(p["curvature"])
        vn = np.linalg.norm(z, axis=1, keepdims=True).astype(np.float32)
        z = z * (np.tanh(np.sqrt(c) * vn) / (np.sqrt(c) * np.maximum(vn, 1e-9)))
    # Linear immersion: preserves local intrinsic dimension = d_latent (G1).
    a_lin = rng.standard_normal((d_latent, dim)).astype(np.float32) / np.sqrt(d_latent)
    x = z @ a_lin
    # High-frequency immersion, weighted by amp: raises eff-rank / breaks low-rank.
    freq = rng.standard_normal((d_latent, _N_FREQ)).astype(np.float32) * np.float32(
        p["freq_scale"]
    )
    bias = rng.uniform(0.0, 2.0 * np.pi, _N_FREQ).astype(np.float32)
    feats = np.cos(z @ freq + bias, dtype=np.float32)  # nonlinear lift
    a_hf = rng.standard_normal((_N_FREQ, dim)).astype(np.float32) / np.sqrt(_N_FREQ)
    x += np.float32(p["amp"]) * (feats @ a_hf)
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x)
    return normalize(x)


# Round-3 family: CONCENTRATION. The EC falsification (results/EC_FALSIFICATION.md)
# showed a flat 52-torus reads intrinsic dimension ~345, not 52 -- real embeddings
# hit ~57 because they are *concentrated* (clustered/hierarchical -> locally
# low-dimensional neighbourhoods), not merely low-dimensional. Round 2 confirmed no
# smooth-manifold knob lowers the measured local dimension. So each cluster here is a
# genuine `local_dim`-dimensional LINEAR patch in its OWN random subspace (a
# Grassmannian sample, orthonormal basis by QR of a Gaussian): within a cluster the
# neighbourhood is exactly `local_dim`-dimensional (two-NN reads it -> G1), while K
# clusters in K different subspaces collectively span the effective rank (G3) and
# break any single low-rank subspace (G8, the gate every smooth family failed).
# Heavy-tailed cluster sizes + an optional hyperbolic (Ch.3 exp_0) layout of the
# centres supply hubness (G6). Concentration requires ``within_scale`` < the centre
# spacing, so nearest neighbours stay in-cluster -- that is the whole mechanism.
CONCENTRATION_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("local_dim", 8.0, 120.0, 57.0),  # within-cluster (LOCAL) intrinsic dimension -> G1
    ("log2_clusters", 2.0, 12.0, 8.0),  # 2**this local subspaces
    (
        "center_spread",
        0.1,
        3.0,
        1.0,
    ),  # separation of cluster centres -> effective rank (G3)
    (
        "within_scale",
        0.02,
        0.6,
        0.12,
    ),  # cluster radius; MUST stay < spacing (concentration)
    ("size_tail", 0.0, 2.5, 1.3),  # heavy-tailed cluster sizes -> hubness (G6)
    ("curvature", 0.0, 3.0, 1.5),  # hyperbolic centre layout (Ch.3 exp_0) -> hubness
    ("noise", 0.0, 0.2, 0.02),  # off-cluster floor
)


def concentration_corpus(
    p: dict[str, float], n: int, dim: int, seed: int
) -> np.ndarray:
    """A byte-reproducible mixture-of-local-subspaces corpus from decoded knobs ``p``.

    Each cluster is a ``local_dim``-dimensional linear patch in its own random
    subspace of R^dim (orthonormal basis from QR of a Gaussian -- a Grassmannian
    sample). If ``within_scale`` is below the centre spacing, a point's nearest
    neighbours are its cluster-mates, so the two-NN estimator reads ``local_dim``
    (G1) even though the K subspaces collectively span a much higher effective rank
    (G3) and no single PCA subspace captures them (G8). Heavy-tailed sizes and an
    optional hyperbolic centre layout give hubness (G6). Unit-normed.
    """
    rng = np.random.default_rng(seed)
    d_local = min(max(2, int(round(p["local_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n)
    w = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-p["size_tail"])
    w /= w.sum()
    counts = rng.multinomial(n, w)
    centres = rng.standard_normal((k_clusters, dim)).astype(np.float32) * np.float32(
        p["center_spread"]
    )
    if p["curvature"] > 0:
        # Hyperbolic (Poincare exp_0) layout of the centres -- geometric-methods Ch.3;
        # packs most centres near the boundary with a few central -> hub structure.
        c = np.float32(p["curvature"])
        vn = np.linalg.norm(centres, axis=1, keepdims=True).astype(np.float32)
        centres = centres * (
            np.tanh(np.sqrt(c) * vn) / (np.sqrt(c) * np.maximum(vn, 1e-9))
        )
    x = np.empty((n, dim), dtype=np.float32)
    ws = np.float32(p["within_scale"])
    row = 0
    for k in range(k_clusters):
        ck = int(counts[k])
        if ck == 0:
            continue
        # A random local_dim-dim subspace of R^dim (Grassmannian sample).
        basis, _ = np.linalg.qr(rng.standard_normal((dim, d_local)).astype(np.float32))
        local = rng.standard_normal((ck, d_local)).astype(np.float32) * ws
        x[row : row + ck] = centres[k] + local @ basis.T
        row += ck
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x)
    return normalize(x)


def geometry_vector(base, q, k: int, kmax: int | None = None) -> dict[str, float]:
    """The eight gates for one ``k`` — the same functions the RC-1 battery uses."""
    base = normalize(np.asarray(base, dtype=np.float32))
    q = normalize(np.asarray(q, dtype=np.float32))
    kmax = max(kmax or k, 2)
    d, idx = knn(base, q, kmax)
    eff, d90 = spectrum(base[: min(50_000, len(base))])
    lid = id_local(d, k)
    return {
        "g1_id_twonn": id_twonn(d),
        "g2_id_ballgrowth": id_ball_growth(d, k),
        "g3_eff_rank": float(eff),
        "g4_dims90": float(d90),
        "g5_relative_contrast": relative_contrast(d, base, q, k),
        "g6_hubness_skew": hubness(idx, len(base), k),
        "g7_local_id_iqr": float(np.subtract(*np.percentile(lid, [75, 25]))),
        "g8_pca_retention": pca_retention(base, q, idx, k),
    }


def measure_corpus(
    base,
    queries=None,
    *,
    ks=(10,),
    kmax: int | None = None,
    batteries=("A", "B"),
    n_query: int = 1000,
    seed: int = 0,
) -> dict[str, dict[int, dict[str, float]]]:
    """Per-battery geometry profile of a corpus: ``{battery: {k: {gate: value}}}``.

    Battery **A** samples its queries from the corpus itself (corpus->corpus);
    battery **B** uses the supplied held-out ``queries`` (query->corpus), falling
    back to A's sampling when none are given. RC-1 requires a generator to match
    **both**. Use this to build the real target (pass real ``base`` + real
    ``queries``) and, inside the fitness, on a generated corpus — same protocol
    each side, so the numbers are comparable.
    """
    base = normalize(np.asarray(base, dtype=np.float32))
    kmax = max(kmax or max(ks), 2)
    out: dict[str, dict[int, dict[str, float]]] = {}
    for battery in batteries:
        if battery == "B" and queries is not None and len(queries):
            q = normalize(np.asarray(queries, dtype=np.float32))
        else:
            rng = np.random.default_rng(seed + 99)
            take = min(n_query, len(base))
            q = base[rng.choice(len(base), size=take, replace=False)]
        out[battery] = {int(k): geometry_vector(base, q, k, kmax) for k in ks}
    return out


def _log_ratio(gen: float, real: float, eps: float = 1e-9) -> float:
    """Signed scale-free deviation of a gate; sign encodes over/under-shoot."""
    return float(np.log((abs(gen) + eps) / (abs(real) + eps)))


def make_evaluate_fn(
    target: dict[str, dict[int, dict[str, float]]],
    *,
    dim: int,
    n: int = 4000,
    n_query: int = 1000,
    ks=(10,),
    batteries=("A", "B"),
    seed: int = 0,
    weight_mandatory: float = 3.0,
    nan_penalty: float = 4.0,
    generator=synth_corpus,
    params_spec=PARAMS,
):
    """Build the shared ``evaluate_fn(params) -> (score, errors)``.

    ``target`` is :func:`measure_corpus` on the **real** embeddings. Each call
    generates a fresh synthetic corpus at ``(n, dim)``, measures the same gates
    on the same batteries, and returns:

    * ``score`` — mean ``|log-ratio|`` mismatch across (battery, k, gate), with the
      mandatory gates up-weighted; **lower is better** (a searcher minimises it);
    * ``errors`` — ``{"g6_hubness_skew@Bk10": +0.7, ...}`` signed per-cell
      deviations, the fuzzer's per-target failure signal.

    Gates that are non-finite in the target are skipped (uninformative); a gate
    that goes non-finite only for the candidate is charged ``nan_penalty`` — a
    generator that *breaks* a measurement should not look like a good fit.
    """
    ks = tuple(int(k) for k in ks)
    kmax = max(ks)

    def evaluate_fn(params: np.ndarray) -> tuple[float, dict[str, float]]:
        p = decode(params, params_spec)
        base = generator(p, n, dim, seed)
        q_b = generator(p, n_query, dim, seed + 1)  # held-out queries
        prof = measure_corpus(
            base,
            q_b,
            ks=ks,
            kmax=kmax,
            batteries=batteries,
            n_query=n_query,
            seed=seed,
        )
        errors: dict[str, float] = {}
        num = 0.0
        den = 0.0
        for battery in batteries:
            for k in ks:
                for g in GATES:
                    real = target[battery][k][g]
                    if not np.isfinite(real):
                        continue
                    gen = prof[battery][k][g]
                    e = nan_penalty if not np.isfinite(gen) else _log_ratio(gen, real)
                    errors[f"{g}@{battery}k{k}"] = e
                    weight = weight_mandatory if g in MANDATORY else 1.0
                    num += weight * abs(e)
                    den += weight
        return (num / den if den else nan_penalty), errors

    return evaluate_fn
