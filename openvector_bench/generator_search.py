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


# Round-6 family: hier placement INSIDE a designed spectral colouring. Round 5 proved the
# G6/G3 trade-off is real *within* codebook geometry: the Zipf hierarchy that makes angular
# hubs concentrates the corpus onto a few dominant modes (rank collapse), and flattening the
# hierarchy to recover rank erases the density gradient. Registered round-6 bet (P3 of
# HIER_PREDICTION.md): set the two properties by SEPARATE mechanisms — hubs by *where* the
# centres sit (round 5's mechanism, kept verbatim), the spectrum by an explicit Mahalanobis
# reshape of the centred covariance toward a designed power law (the codebook probe's one
# confirmed G3 knob). The reshape is a linear sphere-to-ellipsoid map: it rescales the
# centred directions but never reorders which angular region is dense, so the open question
# is only how much hub *contrast* survives the flattening of the dominant modes. The mean is
# left untouched (real embedding anisotropy is itself hub structure).
HIER_COLOURED_PARAMS: tuple[tuple[str, float, float, float], ...] = HIER_PARAMS + (
    ("spectrum_decay", 0.1, 1.5, 0.6),  # target power-law slope of the centred spectrum
    ("reshape_mix", 0.0, 1.0, 1.0),  # 0 = raw hier spectrum, 1 = fully designed
)


def hier_coloured_corpus(
    p: dict[str, float], n: int, dim: int, seed: int
) -> np.ndarray:
    """Round-5 hier corpus recoloured to a designed centred-covariance spectrum.

    Eigendecompose the centred covariance of the (unit-normed) hier corpus, remap its
    eigenvalues toward the power law ``i^-spectrum_decay`` (geometric blend by
    ``reshape_mix``), apply the corresponding Mahalanobis map to the centred part only,
    re-add the mean, re-normalize. Hub placement and spectrum are thus set by different
    parts of the construction.
    """
    x = hier_concentration_corpus(p, n, dim, seed)
    return _recolour(x, float(p["spectrum_decay"]), float(p["reshape_mix"]))


# Round-10: optional NONPARAMETRIC spectral target (PREREG v2 §7 — a fitted
# distributional parameter, fitted on TRAIN rows only). When set, the recolouring
# targets the measured real eigenvalue profile itself; the parametric knee capped
# G4 at 1.52x because no one- or two-piece power law has the real spectrum's
# shape. Drivers call ``set_spectrum_target(path_or_array)``; None (default)
# preserves the parametric path byte-identically for all committed families.
SPECTRUM_TARGET: np.ndarray | None = None


def set_spectrum_target(source) -> None:
    """Install the fitted spectral target (JSON path with 'eigenvalues', or array)."""
    global SPECTRUM_TARGET
    if source is None:
        SPECTRUM_TARGET = None
        return
    if isinstance(source, (str, bytes)):
        import json

        source = json.load(open(source, encoding="utf-8"))["eigenvalues"]
    SPECTRUM_TARGET = np.asarray(source, dtype=np.float64)


def _recolour(
    x: np.ndarray,
    decay: float,
    mix: float,
    knee: float | None = None,
    decay2: float | None = None,
) -> np.ndarray:
    """Mahalanobis reshape of the centred covariance toward a designed spectrum.

    Default: the single power law ``i^-decay`` (byte-identical to all committed
    families). With ``knee``/``decay2`` (round 9): ``i^-decay`` up to index
    ``knee``, then continuously ``(knee^-decay)(i/knee)^-decay2`` — a second
    spectral degree of freedom, because one power law rigidly couples effective
    rank (G3) to dims90 (G4).
    """
    dim = x.shape[1]
    mu = x.mean(0, keepdims=True)
    xc = x - mu
    cov = (xc.T @ xc) / max(len(xc) - 1, 1)
    lam, vecs = np.linalg.eigh(cov)
    lam, vecs = lam[::-1], vecs[:, ::-1]  # descending
    lam = np.maximum(lam, 1e-12)
    i = np.arange(1, dim + 1, dtype=np.float64)
    if SPECTRUM_TARGET is not None and len(SPECTRUM_TARGET) == dim:
        target = np.maximum(SPECTRUM_TARGET, 1e-15)
    elif knee is None or decay2 is None:
        target = i ** (-decay)
    else:
        kn = float(np.clip(knee, 1.0, dim))
        target = np.where(i <= kn, i ** (-decay), (kn**-decay) * (i / kn) ** (-decay2))
    target *= lam.sum() / target.sum()  # match total energy
    new_lam = lam ** (1.0 - mix) * target**mix
    gain = np.sqrt(new_lam / lam).astype(np.float32)
    x = mu + (xc @ vecs) * gain @ vecs.T
    return normalize(x.astype(np.float32))


# Round-7 exploratory family (radius spectrum): screened NEGATIVE — a per-point radius law
# does not move G2 (the window is across-query, not within-neighbourhood) and is kept only
# as a probe record; see results/GEN_ROUND7_QUERY.md for the diagnosis that replaced it.
HIER_MS_PARAMS: tuple[tuple[str, float, float, float], ...] = HIER_COLOURED_PARAMS + (
    ("radius_growth", 2.0, 40.0, 12.0),  # ball-count growth exponent (G2)
    ("radius_floor", 0.0, 0.8, 0.1),  # smallest radius fraction (protects G1/G7)
)


def hier_multiscale_corpus(
    p: dict[str, float], n: int, dim: int, seed: int
) -> np.ndarray:
    """Round-6 coloured hierarchy with a designed within-cluster radius spectrum.

    Identical centre hierarchy and recolouring; each point's local offset is scaled by
    ``floor + (1-floor) * u**(1/radius_growth)`` so within-cluster ball counts grow as
    ``~r**radius_growth`` across scales (G2) instead of saturating at one radius.
    """
    rng = np.random.default_rng(seed)
    d_local = min(max(2, int(round(p["local_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n)
    n_levels = min(max(1, int(round(p["n_levels"]))), 6)
    decay = float(p["level_decay"])
    tail = float(p["branch_tail"])
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
    g = float(p["radius_growth"])
    floor = np.float32(p["radius_floor"])
    x = np.empty((n, dim), dtype=np.float32)
    row = 0
    for k in range(k_clusters):
        ck = int(counts[k])
        if ck == 0:
            continue
        basis, _ = np.linalg.qr(rng.standard_normal((dim, d_local)).astype(np.float32))
        radii = floor + (1.0 - floor) * rng.random((ck, 1)).astype(np.float32) ** (
            1.0 / g
        )
        local = rng.standard_normal((ck, d_local)).astype(np.float32) * (ws * radii)
        x[row : row + ck] = centres[k] + local @ basis.T
        row += ck
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x)
    return _recolour(normalize(x), float(p["spectrum_decay"]), float(p["reshape_mix"]))


# Round-7 family: a QUERY MODEL. Hub-anatomy diagnosis (diag_hubs.json): real's
# base->base reverse-NN skew is only ~1.5 — the battery-B G6 target of 6.8 lives in the
# QUERY MARGINAL (real queries concentrate on popular regions, piling their top-k lists
# onto a subset of base points), not in corpus-side density. Every corpus-side hub
# mechanism therefore either fails (six probes: equalize, mean offset, dup families,
# per-point tilt, sub-clusters, cluster count) or fakes the number with wrong-anatomy
# super-hubs (round 6: max reverse-count 369 vs real 78) whose density contrast is what
# widens the d10 window and pins G2 at 0.14x. This family keeps the corpus HOMOGENEOUS
# (mild size_tail via its knob, per-cluster scale equalized to uniform local density ->
# narrow window -> G2) and draws the held-out battery-B queries from the SAME instance
# but a Zipf-`query_tail`-weighted cluster preference — the query/corpus asymmetry real
# workloads actually have. Rows [0, n-QUERY_FRAC*n) are the corpus; the tail rows are
# the query block (callers split at n_base, matching the harness convention).
QUERY_FRAC = 1.0 / 9.0  # harness convention: n = 8000 base + 1000 held-out queries

HIER_QUERY_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    HIER_COLOURED_PARAMS
    + (
        ("query_tail", 0.0, 3.0, 1.2),  # Zipf over clusters for the QUERY draw (G6)
        (
            "equalize",
            0.0,
            2.0,
            1.0,
        ),  # per-cluster scale ~ count^(eq/d) -> uniform density
    )
)


def _py_theta_for_level(alpha: float, k_target: float, n_ref: float) -> float:
    """Pitman-Yor concentration giving ``k_target`` clusters at ``n_ref`` rows.

    The expected number of occupied clusters after ``n`` draws is
    ``Gamma(theta+1) / (alpha * Gamma(theta+alpha)) * n**alpha``. The discount
    ``alpha`` fixes the exponent, so this solves the prefactor for ``theta``
    and thereby sets the level independently of the growth rate. Geometric
    bisection, because ``theta`` ranges over several orders of magnitude.
    """
    import math

    a = min(max(alpha, 1e-3), 0.999)

    def expected(theta: float) -> float:
        return (
            math.exp(math.lgamma(theta + 1.0) - math.lgamma(theta + a) - math.log(a))
            * n_ref**a
        )

    lo, hi = 1e-4, 1e7
    for _ in range(120):
        mid = math.sqrt(lo * hi)
        if expected(mid) < k_target:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def emergent_cluster_sizes(
    p: dict, growth: float, n_base: int, rng: np.random.Generator
) -> np.ndarray:
    """Cluster sizes from a capacity-limited growth process.

    Round 17's first attempt drew occupancy from a power law and its second
    from a Pitman-Yor process. Both failed the same way. Any exchangeable
    process whose cluster count grows as ``n**alpha`` has a heavy-tailed
    occupancy, so most of its clusters hold a handful of points. Three things
    the round needs are then jointly unsatisfiable: a cluster count near the
    frozen 78, every cluster larger than the local subspace dimension of 94,
    and a count that grows without the generator reading n. At the ladder's
    bottom rung 78 clusters over 11,111 points averages 141 against a floor of
    94, which demands near-balanced clusters, and heavy tails cannot supply
    them. Solving the Pitman-Yor concentration for that level peaked at 20
    clusters and was not even monotone.

    This process is balanced by construction instead. Each row joins a
    uniformly chosen cluster unless that cluster has reached capacity
    ``c * K**beta``, where K is the number of clusters so far, in which case
    the row starts a new cluster. Cluster sizes are then bounded by a common
    capacity rather than spread over a power law.

    The count follows ``n ~ c * K**(1+beta)``, so ``alpha = 1/(1+beta)`` and
    the capacity ``c`` sets the level without touching the exponent. That is
    the separation round 17 needed and neither earlier family had.

    Nothing here reads n. The row loop terminates when the corpus is exhausted,
    but every decision it makes depends only on the state built so far, so a
    prefix of the draw is the same process as the whole. That is what keeps
    subsampling and direct generation equivalent, which is the constraint that
    closed the earlier attempt in the round-17 intervention.
    """
    a = min(max(float(growth), 1e-3), 0.999)
    beta = 1.0 / a - 1.0
    cap_c = float(p.get("cluster_capacity", 1.0))

    sizes = [0]
    n_clust = 1
    for u in rng.random(int(n_base)):
        j = int(u * n_clust)
        if sizes[j] >= cap_c * n_clust**beta:
            sizes.append(1)
            n_clust += 1
        else:
            sizes[j] += 1
    counts = np.asarray(sizes, dtype=np.int64)
    counts = counts[counts > 0]

    # A hard floor was tried here and removed. Folding sub-floor clusters into
    # survivors makes the cluster count a discontinuous and non-monotone
    # function of the capacity, which destroys the calibration that pins the
    # level, and it is the wrong criterion anyway. What made round 17's first
    # gate unreadable was arms whose clusters held 13 points on average against
    # a local subspace dimension of 94, not the handful of clusters that have
    # merely been spawned recently and not yet filled. Degeneracy matters in
    # proportion to how many points experience it, so the gate checks the share
    # of points sitting in sub-floor clusters instead, and the generator returns
    # the process untouched.
    return counts


def hier_query_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """Homogeneous coloured hierarchy + a Zipf-concentrated same-instance query block.

    Corpus rows are the round-6 construction with per-cluster scale equalized
    (``equalize``) so local density — hence the across-query d10 window — is uniform
    (G2). The final ``QUERY_FRAC`` of rows are queries: same clusters, same patches,
    but cluster choice is Zipf(``query_tail``) — the query-marginal concentration that
    carries battery-B hubness (G6). Unit-normed, recoloured as round 6.
    """
    rng = np.random.default_rng(seed)
    n_query = int(round(n * QUERY_FRAC))
    n_base = n - n_query
    d_local = min(max(2, int(round(p["local_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n_base)
    # Emergent cluster count (round 17). Off by default, and when off this
    # function is byte-identical to the frozen round-8 point.
    #
    # The round-17 intervention measured that this family's hub-scaling rise
    # is densification at a FIXED cluster count: every added row joins one of
    # k_clusters clusters, so within-cluster competition intensifies. Scaling
    # the count as n**0.5 moved the slope from +0.905 onto real's +0.51.
    #
    # But a generator may not read n. The grid subsamples a pool rather than
    # regenerating, so a scale-aware generator would give different geometry
    # under subsampling than under generation, which is the sampling-operator
    # problem of rounds 9 and 11. So the count is made to GROW rather than to
    # be set: cluster sizes are drawn from a power law over a pool large
    # enough not to bind, and the number of clusters a corpus occupies then
    # grows as n**cluster_growth as a consequence of drawing rows.
    #
    # The weight exponent is 1/cluster_growth, which is the standard relation
    # between a power-law size law and the occupancy growth it induces.
    growth = float(p.get("cluster_growth", 0.0))
    occupied_from_pool = None
    if growth > 0.0:
        # Round 17's first attempt used a plain power law and failed because
        # level and exponent are coupled through its normalizer: every arm
        # changed how MANY clusters there were as well as how fast the count
        # grew, so the sweep was never a one-parameter sweep and produced 13
        # clusters at one end and 816 at the other against a frozen 78.
        #
        # Pitman-Yor has two parameters and separates them. The discount sets
        # the growth exponent, E[K_n] ~ C(alpha, theta) * n**alpha, and the
        # concentration sets C without touching alpha. Solving for theta
        # against a REFERENCE size pins the level.
        #
        # The reference is a constant of the family, not the corpus size, so
        # the generator still never reads n. That distinction is what keeps
        # subsampling and generation equivalent.
        occupied_from_pool = emergent_cluster_sizes(p, growth, n_base, rng)
        k_clusters = int(len(occupied_from_pool))
    n_levels = min(max(1, int(round(p["n_levels"]))), 6)
    decay = float(p["level_decay"])
    tail = float(p["branch_tail"])
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
    if occupied_from_pool is not None:
        # Sizes already drawn; the pool law replaces size_tail in this mode.
        counts = occupied_from_pool
    else:
        w = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-p["size_tail"])
        w /= w.sum()
        counts = rng.multinomial(n_base, w)
    mean_ck = max(1.0, float(counts[counts > 0].mean()))
    wq = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-p["query_tail"])
    wq /= wq.sum()
    qcounts = rng.multinomial(n_query, wq)
    ws = np.float32(p["within_scale"])
    eq = float(p["equalize"])
    x = np.empty((n, dim), dtype=np.float32)
    rowb, rowq = 0, n_base
    for k in range(k_clusters):
        ck, qk = int(counts[k]), int(qcounts[k])
        if ck + qk == 0:
            continue
        basis, _ = np.linalg.qr(rng.standard_normal((dim, d_local)).astype(np.float32))
        ws_k = ws * np.float32((max(ck, 1) / mean_ck) ** (eq / d_local))
        local = rng.standard_normal((ck + qk, d_local)).astype(np.float32) * ws_k
        pts = centres[k] + local @ basis.T
        x[rowb : rowb + ck] = pts[:ck]
        x[rowq : rowq + qk] = pts[ck:]
        rowb += ck
        rowq += qk
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x[:n_base])  # base rows only — the query block stays the tail
    return _recolour(normalize(x), float(p["spectrum_decay"]), float(p["reshape_mix"]))


# Round-9 family: transfer to the RC-1 grid. The formal §5 admission of the round-8
# point (results/RC1_ROUND2_CANDIDATE.md, 0/24) localized three scale defects the
# n=8k fit could not see: (a) real's two-NN reading is n-FLAT (53-63 across 8x n) —
# pinned by fine-scale near-duplicate pairs (diag_target.json: r1 1%-quantile 0.375
# vs median 0.86) — while flat patches drift upward as sampling densifies; (b) real's
# battery-B hubness grows at +0.22/decade while a FIXED query concentration gives
# +0.13 (capture basins shrink ~1/n; real's per-basin query mass does not); (c) the
# colouring was tuned to +-2x bands, not +-15%. This family adds the two missing
# mechanisms as knobs and keeps everything else from round 8: `dup_mass` of base rows
# are near-copies of other rows (Zipf family multiplicity, capped, jitter
# `dup_scale` x within_scale) -> a short-range pair-distance spike that pins G1/G7;
# `query_tail_n` raises the query Zipf exponent per decade of n above the fitting
# anchor (n_base=8000) -> G6 growth becomes a knob instead of an accident.
HIER_DUPQ_PARAMS: tuple[tuple[str, float, float, float], ...] = HIER_QUERY_PARAMS + (
    ("dup_mass", 0.0, 0.25, 0.0),  # near-dup base rows — FALSIFIED for G1 (probes
    ("dup_scale", 0.01, 1.0, 0.12),  # v9/v9b: invisible to the trimmed estimator or
    ("dup_tail", 1.2, 3.0, 2.0),  # inert); kept at inert defaults, recorded
    ("query_tail_n", 0.0, 1.0, 0.0),  # cluster-Zipf n-coupling — saturated, inert
    ("q_anchor", 0.0, 0.9, 0.5),  # fraction of queries anchored to popular rows (G6)
    ("anchor_tail", 0.5, 2.5, 1.0),  # Zipf popularity field: anchors AND cloud centres
    ("q_jit", 0.1, 2.0, 0.8),  # IN-PATCH anchor offset radius, x within_scale
    ("log2_knee", 4.0, 9.0, 7.3),  # two-piece spectrum knee index (2**this)
    ("spectrum_decay2", 0.5, 2.5, 1.6),  # tail slope beyond the knee (G4)
    ("cloud_mass", 0.0, 0.5, 0.25),  # fraction of base rows in paraphrase clouds
    ("cloud_grade", 0.2, 2.0, 0.7),  # radius law P(r<=t) ~ t^grade (graded ladder)
    ("cloud_span", 0.2, 1.5, 0.9),  # max cloud radius, x within_scale
    ("cloud_tail", 0.5, 2.5, 1.0),  # Zipf on cloud OWNERSHIP (round 10: decoupled
)  # from anchor_tail so k=100 capture depth and query concentration tune apart
_QT_ANCHOR_N = 8000.0  # n_base at which query_tail applies unmodified


def hier_dupq_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """Round-8 construction + near-duplicate families + n-coupled query concentration.

    Base rows [0, n_base): the hier_query construction on ``n_base - n_dup`` seed
    rows, then ``n_dup`` near-copies of Zipf-multiplicity originals (jitter
    ``dup_scale * within_scale``, applied pre-recolour). Query block rows
    [n_base, n): cluster choice Zipf with exponent
    ``query_tail + query_tail_n * log10(n_base / 8000)``.
    """
    rng = np.random.default_rng(seed)
    n_query = int(round(n * QUERY_FRAC))
    n_base = n - n_query
    n_dup = min(int(round(float(p["dup_mass"]) * n_base)), n_base // 2)
    n_seed_rows = n_base - n_dup
    d_local = min(max(2, int(round(p["local_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n_seed_rows)
    n_levels = min(max(1, int(round(p["n_levels"]))), 6)
    decay = float(p["level_decay"])
    tail = float(p["branch_tail"])
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
    counts = rng.multinomial(n_seed_rows, w)
    mean_ck = max(1.0, float(counts[counts > 0].mean()))
    qt = float(p["query_tail"]) + float(p["query_tail_n"]) * np.log10(
        max(n_base, 2) / _QT_ANCHOR_N
    )
    wq = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-max(qt, 0.0))
    wq /= wq.sum()
    qcounts = rng.multinomial(n_query, wq)
    ws = np.float32(p["within_scale"])
    eq = float(p["equalize"])
    x = np.empty((n, dim), dtype=np.float32)
    rowb, rowq = 0, n_base
    q_anchor = float(p["q_anchor"])
    a_tail = float(p["anchor_tail"])
    q_jit = np.float32(float(p["q_jit"]))
    cloud_mass = float(p["cloud_mass"])
    cloud_grade = float(p["cloud_grade"])
    cloud_span = np.float32(float(p["cloud_span"]))

    def _unit_dirs(m: int) -> np.ndarray:
        d = rng.standard_normal((m, d_local)).astype(np.float32)
        return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)

    for k in range(k_clusters):
        ck, qk = int(counts[k]), int(qcounts[k])
        if ck + qk == 0:
            continue
        basis, _ = np.linalg.qr(rng.standard_normal((dim, d_local)).astype(np.float32))
        ws_k = ws * np.float32((max(ck, 1) / mean_ck) ** (eq / d_local))
        # One Zipf POPULARITY FIELD over this cluster's seed rows drives both
        # mechanisms below: popular rows grow paraphrase clouds (the corpus
        # measure) and attract anchored queries (the query measure) — the
        # coupling real corpora have, by construction rather than coincidence.
        n_cloud_k = int(round(cloud_mass * ck))
        n_seed_k = ck - n_cloud_k
        if n_seed_k <= 0:
            n_seed_k, n_cloud_k = ck, 0
        wpop = np.arange(1, n_seed_k + 1, dtype=np.float64) ** (-a_tail)
        wpop /= wpop.sum()
        # Radius unit for clouds and anchor offsets: the PATCH RADIUS
        # ws_k * sqrt(d_local) (a Gaussian patch point's typical norm), so the
        # knobs are fractions of the scale neighbours actually live at.
        pr_k = ws_k * np.float32(np.sqrt(d_local))
        local = np.empty((ck + qk, d_local), dtype=np.float32)
        local[:n_seed_k] = (
            rng.standard_normal((n_seed_k, d_local)).astype(np.float32) * ws_k
        )
        wcloud = np.arange(1, n_seed_k + 1, dtype=np.float64) ** (
            -float(p.get("cloud_tail", a_tail))
        )
        wcloud /= wcloud.sum()
        owners = None
        if n_cloud_k > 0:
            # Paraphrase clouds: members at GRADED radii around popular rows —
            # the short-range mu ladder (r spanning ~0..cloud_span x patch
            # scale, denser near the centre for grade < 1) that pins the
            # trimmed two-NN reading, smooths ball growth, and gives anchored
            # queries neighbours at every fractional distance (probe D's gap).
            owners = rng.choice(n_seed_k, size=n_cloud_k, p=wcloud)
            radii = (
                cloud_span
                * pr_k
                * rng.random((n_cloud_k, 1)).astype(np.float32)
                ** np.float32(1.0 / cloud_grade)
            )
            local[n_seed_k:ck] = local[owners] + radii * _unit_dirs(n_cloud_k)
        # Queries: unanchored ones sample the patch; anchored ones sit at
        # q_jit x within_scale from a popularity-weighted seed row, IN-PATCH
        # (ambient jitter reads ambient dimension; probe v9c).
        local[ck:] = rng.standard_normal((qk, d_local)).astype(np.float32) * ws_k
        qa_k = int(round(q_anchor * qk)) if n_seed_k > 0 else 0
        if qa_k > 0:
            # Anchors are drawn from the realized cloud-OWNER multiset (weight
            # = ladder size): queried rows are exactly the paraphrased rows, so
            # every anchored query has graded near neighbours (its anchored mu
            # -> 1), and the pooled two-NN reading becomes a smooth function of
            # q_anchor between the anchored and patch populations — G1 as a
            # knob. Ladder-less Zipf-tail anchors were the probe-E failure.
            pool = owners if owners is not None and len(owners) else None
            anchors = (
                rng.choice(pool, size=qa_k)
                if pool is not None
                else rng.choice(n_seed_k, size=qa_k, p=wpop)
            )
            local[ck : ck + qa_k] = local[anchors] + (q_jit * pr_k) * _unit_dirs(qa_k)
        pts = centres[k] + local @ basis.T
        x[rowb : rowb + ck] = pts[:ck]
        x[rowq : rowq + qk] = pts[ck:]
        rowb += ck
        rowq += qk
    if n_dup > 0:  # near-duplicate families: a short-range pair-distance spike
        fam = np.minimum(rng.zipf(float(p["dup_tail"]), size=n_dup), 8)
        originals = rng.choice(n_seed_rows, size=n_dup)
        reps = np.repeat(originals, fam)[:n_dup]
        jit = np.float32(float(p["dup_scale"])) * ws
        x[n_seed_rows:n_base] = x[reps] + jit * rng.standard_normal(
            (n_dup, dim)
        ).astype(np.float32)
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x[:n_base])  # base rows only — the query block stays the tail
    return _recolour(
        normalize(x),
        float(p["spectrum_decay"]),
        float(p["reshape_mix"]),
        knee=2.0 ** float(p["log2_knee"]),
        decay2=float(p["spectrum_decay2"]),
    )


# Round-11 primitive: PLANTED LOCAL CENTERS (results/PREREG_ROUND11.md, draft).
# Round 10 closed with a generator-CAPABILITY diagnosis: no optimizer pass over
# the existing family reaches real's battery-A count tail — donor mechanisms cap
# a row's k-occurrence count at Theta(k) and the soft-gradient path at ~2.2k
# (turboquant-pro STRATA fixture measurements). This primitive CONSTRUCTS the
# tail instead of searching for it: m off-center unit shells (chordal radius r
# on the unit sphere), each with p rows planted AT its local center. Every
# shell member sits at ~r from the planted rows but ~r*sqrt(2) from its fellow
# members, so the planted rows top each member's neighbour list and a planted
# row's count response is near-deterministic — a dial (m, p, n_shell), not a
# search target. Placement is population-typical (each shell center IS an
# existing base row), so planted hubs occupy the same central band the
# population does — the origin-shell trick that keeps the centrality signature
# G1's mechanism constraint demands. The overlay composes AFTER the round-10
# machinery (nonparametric spectral target + cloud_tail untouched, recolouring
# already applied, so the constructed distances are exact); defaults keep the
# primitive OFF and the family byte-identical to ``hier_dupq_corpus``.
HIER_LC_PARAMS: tuple[tuple[str, float, float, float], ...] = HIER_DUPQ_PARAMS + (
    ("lc_shells", 0.0, 256.0, 0.0),  # m: off-center unit shells (0 = primitive off)
    ("lc_planted", 1.0, 64.0, 4.0),  # p: rows planted AT each local center
    ("lc_shell_rows", 8.0, 8192.0, 512.0),  # n_shell: shell population per center
    ("lc_radius", 0.02, 0.6, 0.15),  # r: shell radius (chordal, on the unit sphere)
    ("lc_center_jit", 0.005, 0.3, 0.05),  # planted-row spread, x r (no exact dups)
)


def local_centers(
    x: np.ndarray,
    n_base: int,
    m: int,
    n_planted: int,
    n_shell: int,
    radius: float,
    center_jit: float,
    rng: np.random.Generator,
    return_rows: bool = False,
):
    """Overwrite base rows with ``m`` planted-local-center shells (round 11).

    Each shell takes ``n_planted + n_shell`` distinct base-row slots; the first
    slot's ORIGINAL position becomes the shell's local center (ambient
    placement per the existing geometry — population-typical centrality by
    construction). ``n_planted`` rows land at the center (spread
    ``center_jit * radius``) and ``n_shell`` rows on the chordal-radius-
    ``radius`` shell around it. Rows at and beyond ``n_base`` (the query
    block) are never touched, and the overlay refuses to claim more than half
    the base (returned unchanged). With ``return_rows`` the planted row
    indices are also returned, so calibration can read the constructed count
    response directly.
    """
    per = n_planted + n_shell
    if m <= 0 or per <= 0 or m * per > n_base // 2:
        return (x, np.empty(0, dtype=np.int64)) if return_rows else x
    x = np.array(x, copy=True)
    dim = x.shape[1]
    slots = rng.choice(n_base, size=m * per, replace=False)
    centres = x[slots[::per]].copy()  # snapshot before any slot is overwritten
    dirs = rng.standard_normal((m * per, dim)).astype(np.float32)
    dirs /= np.maximum(np.linalg.norm(dirs, axis=1, keepdims=True), 1e-9)
    rad = np.full((per, 1), radius, dtype=np.float32)
    rad[:n_planted] = radius * center_jit
    x[slots] = normalize(np.repeat(centres, per, axis=0) + np.tile(rad, (m, 1)) * dirs)
    if return_rows:
        return x, slots.reshape(m, per)[:, :n_planted].ravel()
    return x


def hier_lc_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """Round-10 corpus + the round-11 planted-local-center overlay."""
    x = hier_dupq_corpus(p, n, dim, seed)
    n_base = n - int(round(n * QUERY_FRAC))
    return local_centers(
        x,
        n_base,
        m=int(round(p.get("lc_shells", 0.0))),
        n_planted=max(1, int(round(p.get("lc_planted", 4.0)))),
        n_shell=max(0, int(round(p.get("lc_shell_rows", 512.0)))),
        radius=float(p.get("lc_radius", 0.15)),
        center_jit=float(p.get("lc_center_jit", 0.05)),
        rng=np.random.default_rng(777_000 + seed),
    )


# Round-12 family: CONCENTRATION ARCHITECTURE, NOT KNOBS (results/PREREG_ROUND12.md,
# draft). Round 11 v2 measured joint-constraint infeasibility at the fit_v10 family
# level: the two levers that move battery-A counts each break a mandatory companion
# (clouds <-> G1, hierarchy <-> G5 + Δslope), and the 5-draw real reference shows
# why — real holds its count-skew LEVEL n-stably while its count MAXIMA thin
# (42 -> 9.4 at k10 across 25k -> 200k). Fixed owners can only overshoot or vanish;
# a population law re-expresses itself at every sampling scale. This family
# decouples the two jobs the cloud ladder was doing:
#   G1 by GRADIENTS — a within-patch anisotropic axis profile (``grad_decay``)
#     sets the local effective dimension, and a scale-free per-point radial
#     density field (``grad_span``, ``grad_shape``) supplies neighbour distances
#     at every fractional scale (the μ ladder as a FIELD, not owner rows) —
#     count-quiet by construction (the soft-gradient count cap measured in the
#     turboquant-pro STRATA fixtures).
#   G6 by RENEWAL — patch occupancy from iid scale-free density weights
#     (``occ_mix``, ``occ_tail``), decoupled from hierarchy/branch rank, with
#     local density CONTRAST ``dens_span`` (popular patches denser, not merely
#     bigger): every subsample redraws the same law, so the skew level is
#     n-stable while absolute maxima thin with the sample — real's measured
#     covariance by construction rather than by calibration.
# Defaults keep every mechanism OFF and the family byte-identical to
# ``hier_dupq_corpus`` (regression-tested); the round-12 operating point removes
# the old architecture by configuration (cloud_mass = dup_mass = 0) — a
# replacement at the fitted-family level, not another overlay.
HIER_R12_PARAMS: tuple[tuple[str, float, float, float], ...] = HIER_DUPQ_PARAMS + (
    ("grad_decay", 0.0, 2.5, 0.0),  # axis-scale power law within the patch (G1)
    ("grad_span", 1.0, 30.0, 1.0),  # densest->sparsest radial scale ratio (μ ladder)
    ("grad_shape", 0.2, 5.0, 1.0),  # mass along the gradient: u**(1/shape)
    ("occ_mix", 0.0, 1.0, 0.0),  # renewal blend: 0 = inherited Zipf-by-rank sizes
    ("occ_tail", 1.05, 3.5, 2.0),  # Pareto tail of the iid patch density weights
    ("dens_span", 0.0, 1.5, 0.0),  # density contrast: patch scale ~ share^(-this/d)
    # Round-12 v2 (P-A'): the self-similar within-patch CASCADE — correlated
    # pairs at graded sub-patch scales (a per-row radial law cannot make
    # pairs; R12_STAGE1_RESULT.md isolated G1 n-flatness as the missing
    # mechanism). Generational attachment to uniform parents: no fixed
    # owners, scale-free pair spectrum, subsample-covariant by construction.
    ("cascade_frac", 0.0, 0.9, 0.0),  # fraction of seed rows drawn by attachment
    ("cascade_smin", 0.001, 0.3, 0.02),  # finest attachment scale, x patch radius
    ("cascade_alpha", 0.3, 3.0, 1.0),  # scale law s = smin**(u**alpha); 1 = log-uniform
)


def hier_r12_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """Round-10 construction with the round-12 decoupled concentration mechanisms.

    Byte-identical to ``hier_dupq_corpus`` at default knobs (same RNG call
    sequence when every mechanism is off). ``occ_mix`` blends the Zipf-by-rank
    occupancy toward iid Pareto(``occ_tail``) density weights; ``dens_span``
    makes heavily weighted patches denser (scale ~ share^(-dens_span/d_local));
    ``grad_decay``/``grad_span``/``grad_shape`` impose the within-patch gradient
    field on every patch-sampled row — base and unanchored queries alike, so the
    query block shares the structural realization (the query-coupling rule).
    """
    rng = np.random.default_rng(seed)
    n_query = int(round(n * QUERY_FRAC))
    n_base = n - n_query
    n_dup = min(int(round(float(p["dup_mass"]) * n_base)), n_base // 2)
    n_seed_rows = n_base - n_dup
    d_local = min(max(2, int(round(p["local_dim"]))), dim)
    k_clusters = min(max(1, int(round(2 ** p["log2_clusters"]))), n_seed_rows)
    n_levels = min(max(1, int(round(p["n_levels"]))), 6)
    decay = float(p["level_decay"])
    tail = float(p["branch_tail"])
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
    occ_mix = float(p.get("occ_mix", 0.0))
    if occ_mix > 0.0:
        # RENEWAL occupancy: iid scale-free density weights, decoupled from
        # hierarchy rank — the branch heads no longer own the concentration.
        v = 1.0 + rng.pareto(float(p.get("occ_tail", 2.0)), size=k_clusters)
        v /= v.sum()
        w = (1.0 - occ_mix) * w + occ_mix * v
        w /= w.sum()
    counts = rng.multinomial(n_seed_rows, w)
    mean_ck = max(1.0, float(counts[counts > 0].mean()))
    qt = float(p["query_tail"]) + float(p["query_tail_n"]) * np.log10(
        max(n_base, 2) / _QT_ANCHOR_N
    )
    wq = np.arange(1, k_clusters + 1, dtype=np.float64) ** (-max(qt, 0.0))
    wq /= wq.sum()
    qcounts = rng.multinomial(n_query, wq)
    ws = np.float32(p["within_scale"])
    eq = float(p["equalize"])
    x = np.empty((n, dim), dtype=np.float32)
    rowb, rowq = 0, n_base
    q_anchor = float(p["q_anchor"])
    a_tail = float(p["anchor_tail"])
    q_jit = np.float32(float(p["q_jit"]))
    cloud_mass = float(p["cloud_mass"])
    cloud_grade = float(p["cloud_grade"])
    cloud_span = np.float32(float(p["cloud_span"]))
    grad_span = float(p.get("grad_span", 1.0))
    grad_shape = float(p.get("grad_shape", 1.0))
    dens_span = float(p.get("dens_span", 0.0))
    cascade_frac = float(p.get("cascade_frac", 0.0))
    cascade_smin = float(p.get("cascade_smin", 0.02))
    cascade_alpha = float(p.get("cascade_alpha", 1.0))
    sigma: np.ndarray | None = None
    if float(p.get("grad_decay", 0.0)) > 0.0:
        # Anisotropic axis profile at unit mean-square energy: dials the local
        # participation ratio (hence the TwoNN level) without moving the patch
        # radius the count machinery sees.
        j = np.arange(1, d_local + 1, dtype=np.float64)
        s2 = j ** (-2.0 * float(p["grad_decay"]))
        sigma = np.sqrt(s2 * (d_local / s2.sum())).astype(np.float32)[None, :]

    def _graded(m: int) -> np.ndarray:
        """Patch sample under the gradient field (identity when both knobs are
        off — same RNG call sequence as the round-10 draw)."""
        z = rng.standard_normal((m, d_local)).astype(np.float32)
        if sigma is not None:
            z *= sigma
        if grad_span > 1.0:
            # Scale-free radial density: per-point scale log-spaced in
            # [1/grad_span, 1], mass along the gradient set by grad_shape —
            # neighbour distances at every fractional scale, no owner rows.
            t = rng.random((m, 1)).astype(np.float32) ** np.float32(1.0 / grad_shape)
            z *= np.float32(grad_span) ** (t - np.float32(1.0))
        return z

    def _unit_dirs(m: int) -> np.ndarray:
        d = rng.standard_normal((m, d_local)).astype(np.float32)
        return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)

    for k in range(k_clusters):
        ck, qk = int(counts[k]), int(qcounts[k])
        if ck + qk == 0:
            continue
        basis, _ = np.linalg.qr(rng.standard_normal((dim, d_local)).astype(np.float32))
        ws_k = ws * np.float32((max(ck, 1) / mean_ck) ** (eq / d_local))
        if dens_span > 0.0:
            # Density CONTRAST: heavily weighted patches are denser, not just
            # bigger — hub mass carried by relative density, a per-row law
            # every subsample redraws. Direct exponent, clipped to [1/3, 3]:
            # a /d_local normalization (the equalize convention) caps the
            # factor at ~1.04 over two decades of share — measured inert.
            ws_k = ws_k * np.float32(
                np.clip(max(w[k] * k_clusters, 1e-9) ** (-dens_span), 1.0 / 3.0, 3.0)
            )
        n_cloud_k = int(round(cloud_mass * ck))
        n_seed_k = ck - n_cloud_k
        if n_seed_k <= 0:
            n_seed_k, n_cloud_k = ck, 0
        wpop = np.arange(1, n_seed_k + 1, dtype=np.float64) ** (-a_tail)
        wpop /= wpop.sum()
        pr_k = ws_k * np.float32(np.sqrt(d_local))
        local = np.empty((ck + qk, d_local), dtype=np.float32)
        local[:n_seed_k] = _graded(n_seed_k) * ws_k
        n_casc = (
            min(int(round(cascade_frac * n_seed_k)), n_seed_k - 1)
            if cascade_frac > 0.0 and n_seed_k >= 2
            else 0
        )
        if n_casc > 0:
            # Self-similar CASCADE (round-12 v2, P-A'): the last n_casc seed
            # rows are re-drawn by generational attachment — each attaches to
            # a uniformly chosen EARLIER row (fresh or cascaded: ladders grow
            # on ladders) at a scale-free offset in [cascade_smin, 1] x patch
            # radius. Correlated pairs at every fractional octave with no
            # fixed owners; if the pair spectrum is scale-free the TwoNN
            # mu-statistics are subsample-invariant — n-flatness as a
            # symmetry (the renewal principle at sub-patch scale).
            done = n_seed_k - n_casc
            per_gen = max(1, (n_casc + 3) // 4)
            while done < n_seed_k:
                m = min(per_gen, n_seed_k - done)
                parents = rng.integers(0, done, size=m)
                u = rng.random((m, 1)).astype(np.float32)
                s = np.float32(cascade_smin) ** (u ** np.float32(cascade_alpha))
                local[done : done + m] = local[parents] + (s * pr_k) * _unit_dirs(m)
                done += m
        wcloud = np.arange(1, n_seed_k + 1, dtype=np.float64) ** (
            -float(p.get("cloud_tail", a_tail))
        )
        wcloud /= wcloud.sum()
        owners = None
        if n_cloud_k > 0:
            owners = rng.choice(n_seed_k, size=n_cloud_k, p=wcloud)
            radii = (
                cloud_span
                * pr_k
                * rng.random((n_cloud_k, 1)).astype(np.float32)
                ** np.float32(1.0 / cloud_grade)
            )
            local[n_seed_k:ck] = local[owners] + radii * _unit_dirs(n_cloud_k)
        local[ck:] = _graded(qk) * ws_k
        qa_k = int(round(q_anchor * qk)) if n_seed_k > 0 else 0
        if qa_k > 0:
            pool = owners if owners is not None and len(owners) else None
            anchors = (
                rng.choice(pool, size=qa_k)
                if pool is not None
                else rng.choice(n_seed_k, size=qa_k, p=wpop)
            )
            local[ck : ck + qa_k] = local[anchors] + (q_jit * pr_k) * _unit_dirs(qa_k)
        pts = centres[k] + local @ basis.T
        x[rowb : rowb + ck] = pts[:ck]
        x[rowq : rowq + qk] = pts[ck:]
        rowb += ck
        rowq += qk
    if n_dup > 0:
        fam = np.minimum(rng.zipf(float(p["dup_tail"]), size=n_dup), 8)
        originals = rng.choice(n_seed_rows, size=n_dup)
        reps = np.repeat(originals, fam)[:n_dup]
        jit = np.float32(float(p["dup_scale"])) * ws
        x[n_seed_rows:n_base] = x[reps] + jit * rng.standard_normal(
            (n_dup, dim)
        ).astype(np.float32)
    x += np.float32(p["noise"]) * rng.standard_normal(x.shape).astype(np.float32)
    rng.shuffle(x[:n_base])  # base rows only — the query block stays the tail
    return _recolour(
        normalize(x),
        float(p["spectrum_decay"]),
        float(p["reshape_mix"]),
        knee=2.0 ** float(p["log2_knee"]),
        decay2=float(p["spectrum_decay2"]),
    )


def dirichlet_codebook_corpus(
    p: dict[str, float], n: int, dim: int, seed: int
) -> np.ndarray:
    """Codebook family: every row is a Dirichlet admixture of ``r`` atoms.

    The continuous analogue of the topic model in Blum, Hopcroft and Kannan
    ch. 9 (``A = BC + N``): B is a codebook of ``r`` atom directions, each row
    draws mixing weights from a Dirichlet, and the row is ``B c`` normalized.
    Written for one property the campaign's corpus-side mechanisms have never
    had, and three the search has never been able to separate.

    **Subsample covariance, by construction.** Hub mass lives in *atom
    popularity* — a law over the codebook — not in owner rows. Thinning the
    corpus leaves the codebook and the popularity law untouched, so the hub
    structure re-expresses at every sampling scale. Rounds 9, 11 and 12 each
    failed on the converse: planted owners keep their absolute counts while
    the reference thins.

    **Three near-independent knobs**, which is the point:

    ``log2_atoms``     r, the codebook size. Sets global effective rank (G3):
                       rows span r directions however concentrated each is.
    ``concentration``  mu of a symmetric Dirichlet. The effective number of
                       active atoms per row is ~ r*mu, which sets LOCAL
                       intrinsic dimension (G1) without touching r. This is
                       the decoupling rounds 1-2 concluded the manifold family
                       did not have ("no knob breaks G1").
    ``atom_tail``      Zipf exponent on atom popularity, via an asymmetric
                       Dirichlet (the book flags the asymmetric case at the
                       end of its §9.6). Popular atoms make dense regions and
                       hence hubs, as a population law rather than planted
                       rows. Touches neither r nor r*mu.

    ``noise`` adds isotropic off-codebook mass so rows are not confined to the
    exact simplex; the simplex is flat and real embedding geometry is not, so
    this is a knob the family will probably need rather than a formality.

    Not yet measured against any gate. The registered first question is
    whether the subsample-covariance claim above survives contact with the
    grid's own sampling operator; nothing else about this family matters if
    it does not.
    """
    rng = np.random.default_rng(seed)
    r = max(2, int(round(2.0 ** float(p.get("log2_atoms", 7.5)))))
    mu = max(1e-3, float(p.get("concentration", 0.3)))
    tail = float(p.get("atom_tail", 0.0))
    noise = float(p.get("noise", 0.05))

    # Codebook: random directions. Random atoms in high dimension are nearly
    # orthogonal, so effective rank tracks r rather than collapsing.
    basis = rng.standard_normal((r, dim))
    basis /= np.maximum(np.linalg.norm(basis, axis=1, keepdims=True), 1e-12)

    # Asymmetric concentration: atom l gets mu * l^-tail, so popularity is a
    # Zipf law over the codebook. tail = 0 recovers the symmetric case.
    alpha = mu * (np.arange(1, r + 1, dtype=np.float64) ** (-tail))
    alpha = np.maximum(alpha, 1e-6)

    out = np.empty((n, dim), dtype=np.float32)
    block = max(1, min(n, 4096))
    for a in range(0, n, block):
        k = min(a + block, n) - a
        # Dirichlet via normalized independent Gammas — the standard
        # construction, and it costs one draw per (row, atom).
        g = rng.gamma(shape=np.broadcast_to(alpha, (k, r)), scale=1.0)
        c = g / np.maximum(g.sum(axis=1, keepdims=True), 1e-300)
        x = c @ basis
        if noise > 0:
            x += noise * rng.standard_normal((k, dim))
        out[a : a + k] = x.astype(np.float32)
    return normalize(out)


def py_codebook_support(p: dict[str, float], n: int, seed: int):
    """Which atoms a corpus of ``n`` rows touches, and each row's support.

    Factored out so the family's central claim is directly observable. The
    claim is that the used-atom count grows as ``n**py_alpha`` without the
    generator being told ``n``, and a spectral proxy cannot check that
    because effective rank saturates against the ambient dimension. Counting
    the atoms can.

    Returns ``(used_atom_ids, per_row_support)`` with the support already
    compacted to index into ``used_atom_ids``.
    """
    rng = np.random.default_rng(seed)
    alpha = float(np.clip(p.get("py_alpha", 0.5), 1e-3, 0.999))
    theta = float(max(p.get("py_theta", 10.0), -alpha + 1e-6))
    s = max(1, int(round(p.get("atoms_per_row", 8))))

    # Stick-breaking for PY(alpha, theta). Truncated where the remaining mass
    # can no longer be reached by n*s draws, so the truncation follows the
    # budget rather than being an arbitrary cap.
    k_max = int(min(200_000, max(1_000, 40 * (n * s) ** alpha)))
    idx = np.arange(k_max)
    v = rng.beta(1.0 - alpha, theta + (idx + 1) * alpha)
    log1mv = np.log1p(-np.clip(v, 0.0, 1 - 1e-12))
    w = v * np.exp(np.concatenate([[0.0], np.cumsum(log1mv[:-1])]))
    w = np.maximum(w, 0.0)
    w /= w.sum()

    pick = rng.choice(k_max, size=(n, s), p=w)
    used, compact = np.unique(pick, return_inverse=True)
    return used, compact.reshape(n, s)


def py_codebook_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """Codebook whose size grows with the corpus, without being told to.

    The round-15 fixed codebook failed because a fixed set of atoms is a
    fixed set of owners. Every row added crowds the same attractors, so hub
    concentration grew about six times faster than the real corpus does
    (`results/R15_CODEBOOK_GATE.md`).

    The repair is not to make the codebook a function of ``n``, which would
    be a generator that knows its own scale and would break byte-reproducible
    subsampling. It is to give atom popularity a **power-law tail**, drawn
    once, and let the corpus discover as many atoms as it has rows to spend.
    Under Pitman-Yor stick-breaking with discount ``py_alpha``, the sorted
    weights decay as ``k**(-1/alpha)``, and the number of atoms a corpus of
    ``n`` rows actually touches grows as ``n**alpha`` as a consequence rather
    than as an instruction. A subsample of the rows uses correspondingly
    fewer atoms, which is exactly how a smaller real corpus behaves.

    Knobs, with the round-15 three retained:

    ``py_alpha``       discount in (0, 1). Sets how fast the used-atom count
                       grows, hence how fast hub concentration is diluted as
                       the corpus grows. This is the one the campaign has
                       never had a controller for.
    ``py_theta``       concentration. Shifts the number of atoms at a given
                       ``n`` without changing the growth exponent, so it
                       moves effective rank at fixed scaling behaviour.
    ``atoms_per_row``  admixture size s.
    ``concentration``  Dirichlet spread within a row, so ``s*mu`` sets local
                       intrinsic dimension.
    ``noise``          isotropic off-codebook mass.

    ``py_alpha`` and the popularity tail are not independent, since one
    discount sets both. Whether a single exponent can match real's growth and
    real's hubness at once is the open question the registered gate asks, and
    it is a property of the process rather than of this implementation.
    """
    rng = np.random.default_rng(seed)
    mu = max(1e-3, float(p.get("concentration", 0.3)))
    noise = float(p.get("noise", 0.05))

    # py_alpha and py_theta are consumed by the support draw, which is where
    # the growth property lives and where it can be checked.
    used, compact = py_codebook_support(p, n, seed)
    s = compact.shape[1]

    # Directions only for atoms this corpus actually touched.
    a_rng = np.random.default_rng(seed + 991)
    basis = a_rng.standard_normal((len(used), dim)).astype(np.float32)
    basis /= np.maximum(np.linalg.norm(basis, axis=1, keepdims=True), 1e-12)

    out = np.empty((n, dim), dtype=np.float32)
    block = max(1, min(n, 4096))
    for a in range(0, n, block):
        k = min(a + block, n) - a
        g = rng.gamma(shape=mu, scale=1.0, size=(k, s))
        c = (g / np.maximum(g.sum(axis=1, keepdims=True), 1e-300)).astype(np.float32)
        # Accumulate one atom slot at a time. The natural expression gathers
        # (block, s, dim) at once, which at s = 8 and dim = 1024 is eight
        # times this working set and OOMed a 2Gi worker. Per-slot accumulation
        # holds (block, dim) and costs nothing but a short Python loop.
        x = np.zeros((k, dim), dtype=np.float32)
        sup = compact[a : a + k]
        for j in range(s):
            x += c[:, j : j + 1] * basis[sup[:, j]]
        if noise > 0:
            x += (noise * rng.standard_normal((k, dim))).astype(np.float32)
        out[a : a + k] = x
    return normalize(out)


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
            searched = base
        else:
            # WP0.1 (spec/NORMAL_FORMS.md): battery-A queries are held OUT of the
            # searched base. Sampling them from the searched rows self-matches at
            # distance 0, collapsing every neighbour diagnostic (id_twonn ~ 0.1) —
            # the artifact documented in results/QUERY_COUPLING_ARTIFACT.md.
            rng = np.random.default_rng(seed + 99)
            take = min(n_query, len(base) // 2)
            qi = rng.choice(len(base), size=take, replace=False)
            hold = np.zeros(len(base), dtype=bool)
            hold[qi] = True
            q = base[qi]
            searched = base[~hold]
        out[battery] = {int(k): geometry_vector(searched, q, k, kmax) for k in ks}
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
    anatomy_target: float | None = None,
    anatomy_queries: int = 2000,
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

    ``anatomy_target`` (round-8 protocol, the lesson of round 7's fired P2):
    when set, the base->base reverse-NN skew — measured with ``anatomy_queries``
    corpus rows as queries, self excluded, at the first ``k`` — is scored
    against it at mandatory weight. An unpriced anatomy is an invitation the
    optimizer accepts: round 7's score-best point hit every gate band while
    rebuilding corpus super-hubs (skew ~7 vs real ~1.5). Pricing the anatomy
    makes the query-marginal mechanism the cheap path, not the expensive one.
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
        if anatomy_target is not None:
            nq_a = min(anatomy_queries, n)
            _, idx_a = knn(base, base[:nq_a], kmax + 1)
            bb = hubness(idx_a[:, 1:], n, ks[0])
            e = (
                nan_penalty
                if not np.isfinite(bb)
                else _log_ratio(max(bb, 0.05), anatomy_target)
            )
            errors["bb_skew@anatomy"] = e
            num += weight_mandatory * abs(e)
            den += weight_mandatory
        return (num / den if den else nan_penalty), errors

    return evaluate_fn
