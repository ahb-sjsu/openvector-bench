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


# Round-4 family: STRATIFIED. The concentration family (round 3) fixed *one* local
# dimension per cluster, so the local-ID DISTRIBUTION is a spike: it can chase the
# G1 median but not the real G7 spread (real local-ID IQR = 25.6; every prior family
# misses G1 and G7 *together* by ~4-5x because both are dragged by an ambient-
# dominated local dimension). A Whitney (b)-regular stratified space is the principled
# generalisation: within each cone the points live on a *flag* of nested subspaces
# V_0 ⊃ V_1 ⊃ ... (strata of DECREASING dimension s_0 > s_1 > ... meeting along their
# closures), so the per-point local dimension is a genuine SPECTRUM. Set that spectrum
# to the target ID distribution and G1 (its centre) and G7 (its spread) are matched by
# construction. Nesting gives Whitney (a) for free (a deeper stratum's tangent ⊆ the
# shallower one's); ``frontier_conc`` shrinks the "shell" coordinates that separate a
# stratum from the next-deeper one, so points accumulate onto the frontier (the (b)
# secant condition) AND pile onto the low-dimensional strata -> hubness. K cones in K
# independent flags span the effective rank (G3) exactly as the concentration family's
# subspaces do. Byte-reproducible from ``seed`` like every family.
#
# HONEST PRE-REGISTERED RISK (see results/STRATIFIED_PREDICTION.md): a top stratum of
# dimension ~80 is still undersampled at n=8-16k, so its two-NN reading may overshoot
# s_0 exactly as the flat torus did. The bet is that the well-sampled, heavily
# populated DEEP strata pull the ID *distribution* toward target even when the tail is
# undersampled. That is what the experiment tests; it is not assumed.
STRATIFIED_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    (
        "top_dim",
        8.0,
        120.0,
        88.0,
    ),  # s_0: top stratum dim -> upper end of the ID spectrum
    (
        "bottom_dim",
        2.0,
        80.0,
        38.0,
    ),  # s_L: deepest stratum dim -> lower end (gap -> G7)
    ("n_strata", 2.0, 8.0, 4.0),  # strata per flag -> granularity of the spectrum
    ("log2_cones", 2.0, 12.0, 8.0),  # 2**this nested flags -> effective rank (G3)
    ("frontier_conc", 0.2, 4.0, 1.5),  # frontier accumulation + deep-stratum tilt -> G6
    ("cone_tail", 0.0, 2.5, 1.3),  # Zipf on cone sizes -> hubness (G6)
    (
        "within_scale",
        0.02,
        0.6,
        0.12,
    ),  # cone radius; MUST stay < spacing (concentration)
    ("curvature", 0.0, 3.0, 1.5),  # hyperbolic (Ch.3 exp_0) centre layout -> hubness
    ("noise", 0.0, 0.2, 0.02),  # off-stratum floor
)


def _stratum_dims(p: dict[str, float], dim: int) -> np.ndarray:
    """The flag's stratum dimensions s_0 > s_1 > ... > s_L (strictly decreasing)."""
    d_top = min(max(2, int(round(p["top_dim"]))), dim)
    d_bot = min(max(1, int(round(p["bottom_dim"]))), d_top)
    n_s = min(max(1, int(round(p["n_strata"]))), d_top - d_bot + 1)
    s = np.unique(np.round(np.linspace(d_bot, d_top, n_s)).astype(int))[::-1]
    return s  # descending; s[0] = d_top, s[-1] = d_bot


def _stratum_latent(
    rng: np.random.Generator, ck: int, s_dims: np.ndarray, fc: float, d_top: int
) -> tuple[np.ndarray, np.ndarray]:
    """Latent coordinates (in the flag basis) + stratum index for ``ck`` points.

    Each point gets an active block of ``s_dims[stratum]`` Gaussian coordinates and
    zeros beyond it (so it lies in V_stratum); the "shell" coordinates between its own
    stratum dimension and the next-deeper one are shrunk toward 0 by ``fc`` (frontier
    accumulation). Population is tilted toward the DEEP strata by ``fc`` too, so the
    low-dimensional strata are the densely-sampled hubs.
    """
    n_s = len(s_dims)
    depth = np.arange(n_s, dtype=np.float64)  # 0 = top ... n_s-1 = deepest
    w = (depth + 1.0) ** fc
    w /= w.sum()
    strat = rng.choice(n_s, size=ck, p=w)
    cols = np.arange(d_top)[None, :]
    own = s_dims[strat][:, None]  # each point's own stratum dimension
    nxt = s_dims[np.minimum(strat + 1, n_s - 1)][:, None]  # next-deeper dimension
    u = rng.standard_normal((ck, d_top)).astype(np.float32) * (cols < own)
    shell = (cols >= nxt) & (cols < own)  # coords separating this stratum from the next
    shrink = rng.random((ck, d_top)).astype(np.float32) ** np.float32(fc)
    u = np.where(shell, u * shrink, u).astype(np.float32)
    return u, strat


def stratified_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """A byte-reproducible Whitney-stratified corpus from decoded knobs ``p``.

    K cones, each an independent flag of nested subspaces (orthonormal basis from QR
    of a Gaussian): a point in stratum ``i`` has ``s_dims[i]`` active latent dimensions,
    so the two-NN estimator reads a *distribution* of local dimensions across strata
    (G1 = its centre, G7 = its spread) rather than a single value. Heavy-tailed cone
    sizes and the deep-stratum frontier pile-up give hubness (G6); K independent flags
    span the effective rank (G3). Unit-normed.
    """
    rng = np.random.default_rng(seed)
    s_dims = _stratum_dims(p, dim)
    d_top = int(s_dims[0])
    fc = float(p["frontier_conc"])
    k_cones = min(max(1, int(round(2 ** p["log2_cones"]))), n)
    w = np.arange(1, k_cones + 1, dtype=np.float64) ** (-p["cone_tail"])
    w /= w.sum()
    counts = rng.multinomial(n, w)
    centres = rng.standard_normal((k_cones, dim)).astype(np.float32)
    if p["curvature"] > 0:  # hyperbolic (Poincare exp_0) centre layout -> hub structure
        c = np.float32(p["curvature"])
        vn = np.linalg.norm(centres, axis=1, keepdims=True).astype(np.float32)
        centres = centres * (
            np.tanh(np.sqrt(c) * vn) / (np.sqrt(c) * np.maximum(vn, 1e-9))
        )
    ws = np.float32(p["within_scale"])
    x = np.empty((n, dim), dtype=np.float32)
    row = 0
    for kc in range(k_cones):
        ck = int(counts[kc])
        if ck == 0:
            continue
        u, _ = _stratum_latent(rng, ck, s_dims, fc, d_top)
        basis, _ = np.linalg.qr(rng.standard_normal((dim, d_top)).astype(np.float32))
        x[row : row + ck] = centres[kc] + ws * (u @ basis.astype(np.float32).T)
        row += ck
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x)
    return normalize(x)


def whitney_b_defect(p: dict[str, float], n: int, dim: int, seed: int) -> float:
    """Numerical Whitney (b)-condition defect of the stratified family (0 = regular).

    For each shallow-stratum point, take its nearest deeper-stratum cone-mate; the
    secant between them, expressed in the orthonormal flag basis, has coordinates
    exactly ``u_shallow - u_deep`` (the QR basis is orthonormal, so no ambient vector
    is needed). Whitney (b) asks the secant to lie in the shallow tangent as the pair
    contracts; the defect is the mean fraction of the secant *outside* the shallow
    stratum's subspace, ``||diff[s_shallow:]|| / ||diff||``. This is a CONSTRUCTION-side
    diagnostic, not an RC-1 gate: the registered prediction is that the gates track the
    dimension spectrum + cone count, and are *insensitive* to this defect at matched
    spectrum (i.e. (b)-regularity is second-order). This function is what falsifies that.
    """
    rng = np.random.default_rng(seed)
    s_dims = _stratum_dims(p, dim)
    d_top = int(s_dims[0])
    if len(s_dims) < 2:
        return float("nan")  # a single stratum has no frontier
    fc = float(p["frontier_conc"])
    k_cones = min(max(1, int(round(2 ** p["log2_cones"]))), n)
    per = max(2, n // k_cones)
    defects: list[float] = []
    for _ in range(k_cones):
        u, strat = _stratum_latent(rng, per, s_dims, fc, d_top)
        deep_dim = int(s_dims[-1])
        deep = strat == (len(s_dims) - 1)
        shallow = ~deep
        if deep.sum() < 1 or shallow.sum() < 1:
            continue
        ud, us = u[deep], u[shallow]
        # nearest deeper cone-mate for each shallow point (latent-space distance)
        d2 = ((us[:, None, :] - ud[None, :, :]) ** 2).sum(-1)
        j = np.argmin(d2, axis=1)
        diff = us - ud[j]
        num = np.linalg.norm(diff[:, deep_dim:], axis=1)
        den = np.maximum(np.linalg.norm(diff, axis=1), 1e-9)
        defects.append(float(np.mean(num / den)))
    return float(np.mean(defects)) if defects else float("nan")


# Round-5 family: HIERARCHICAL concentration. Rounds 3-4 matched G1/G3/G7/G8 but hubness
# (G6) stayed ~0.18x. Root cause (diagnosed round 4): the `curvature`/exp_0 map is RADIAL
# (preserves direction), so after unit-normalisation it is discarded and does nothing to the
# angular geometry the gates see -- which is why curving the centres never moved hubness.
# On the sphere hubness = ANGULAR density variation: a few points that are the nearest
# neighbour of many. Round 1 got it because exp_0 fed a NONLINEAR lift (radial -> angular);
# the linear concentration embedding cannot. The fix is to build the angular density gradient
# directly into CENTRE PLACEMENT: a self-similar codebook hierarchy (geometric-methods Ch.5
# tree/hyperbolic theme) where a heavy-tailed choice at each level makes some angular regions
# dense (hubs) and most sparse, while each cluster stays a flat local_dim patch (G1/G8) and a
# range of cluster sizes/depths keeps the local-ID spread (G7). Byte-reproducible.
HIER_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("local_dim", 8.0, 120.0, 55.0),  # within-cluster flat patch dim -> G1
    ("log2_clusters", 4.0, 13.0, 9.0),  # 2**this leaf clusters
    ("n_levels", 1.0, 5.0, 3.0),  # codebook hierarchy depth (angular multi-scale)
    ("level_decay", 0.2, 0.95, 0.6),  # radius shrink per level (self-similar contrast)
    ("branch_tail", 0.0, 3.0, 1.6),  # Zipf on codebook choice -> ANGULAR hubs (G6)
    ("within_scale", 0.02, 0.6, 0.15),  # patch radius; < spacing (concentration)
    ("size_tail", 0.0, 2.5, 1.3),  # heavy-tailed cluster sizes -> hubness assist
    ("noise", 0.0, 0.2, 0.02),  # off-cluster floor
)


def hier_concentration_corpus(
    p: dict[str, float], n: int, dim: int, seed: int
) -> np.ndarray:
    """Concentration with a self-similar hierarchical CENTRE layout for angular hubness.

    Each centre is a sum over ``n_levels`` scales of a codebook vector chosen by a
    heavy-tailed (Zipf ``branch_tail``) draw: at each level the codebook grows, so
    high-level codes carve coarse angular clusters and the Zipf choice makes a few of
    them dense -> those angular regions become hubs (G6). Each leaf cluster is still a
    flat ``local_dim`` patch in its own random subspace (G1/G8); heavy-tailed sizes give
    a local-ID spread (G7). Unit-normed.
    """
    rng = np.random.default_rng(seed)
    d_local = min(max(2, int(round(p["local_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n)
    n_levels = min(max(1, int(round(p["n_levels"]))), 6)
    decay = float(p["level_decay"])
    tail = float(p["branch_tail"])
    # Self-similar centres: sum of codebook vectors over levels, heavy-tailed choice.
    centres = np.zeros((k_clusters, dim), dtype=np.float32)
    scale = 1.0
    for lvl in range(n_levels):
        n_codes = max(
            1, min(k_clusters, int(round(k_clusters ** ((lvl + 1) / n_levels))))
        )
        codes = rng.standard_normal((n_codes, dim)).astype(np.float32)
        w = np.arange(1, n_codes + 1, dtype=np.float64) ** (-tail)
        w /= w.sum()
        assign = rng.choice(n_codes, size=k_clusters, p=w)
        centres += np.float32(scale) * codes[assign]
        scale *= decay
    w = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-p["size_tail"])
    w /= w.sum()
    counts = rng.multinomial(n, w)
    ws = np.float32(p["within_scale"])
    x = np.empty((n, dim), dtype=np.float32)
    row = 0
    for k in range(k_clusters):
        ck = int(counts[k])
        if ck == 0:
            continue
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
        # Battery B queries must be held out from the SAME instance, not a fresh
        # draw: for an instance-random generator (clusters/subspaces/projections
        # depend on the seed) a different seed is a DIFFERENT manifold, so the
        # queries land off the base's clusters and two-NN reads cross-instance
        # (high) dimension instead of the local one -- silently penalising every
        # concentrated family. Real queries.npy lie on the real manifold, so the
        # faithful analog is one instance split into base + held-out queries.
        full = generator(p, n + n_query, dim, seed)
        base, q_b = full[:n], full[n:]
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
