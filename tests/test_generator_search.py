"""Generator-search fitness — the shared ``evaluate_fn`` for procedural-corpus
discovery, reusing the RC-1 geometry battery. Tests are self-consistent (no real
embeddings needed): a synthetic corpus at known knobs is the "target", and the
fitness must reward a candidate that reproduces those knobs.
"""

from __future__ import annotations

import numpy as np

from openvector_bench.generator_search import (
    GATES,
    decode,
    make_evaluate_fn,
    measure_corpus,
    synth_corpus,
)

DIM = 64
N, NQ, KS = 1500, 400, (10,)
P_STAR = np.array([4.0, 1.2, 1.0, 0.30, 0.05])  # PARAMS order


def _target(p, seed=0):
    # Same-instance split, matching make_evaluate_fn: queries are held out from
    # the SAME generated instance (results/QUERY_COUPLING_ARTIFACT.md) — an
    # independent seed is a different manifold realization.
    full = synth_corpus(decode(p), N + NQ, DIM, seed)
    base, q = full[:N], full[N:]
    return measure_corpus(base, q, ks=KS, batteries=("A", "B"), n_query=NQ, seed=seed)


def test_decode_inactive_restores_defaults():
    on = decode(P_STAR)
    off = decode(np.full(len(P_STAR), 1e6))
    assert off["log2_clusters"] == 6.0 and off["size_tail"] == 1.1  # defaults
    assert on["size_tail"] == 1.2  # active value passes through


def test_synth_corpus_shape_and_unit_norm():
    x = synth_corpus(decode(P_STAR), 800, DIM, 3)
    assert x.shape == (800, DIM)
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)


def test_evaluate_fn_contract_and_rewards_match():
    target = _target(P_STAR, seed=0)
    ev = make_evaluate_fn(target, dim=DIM, n=N, n_query=NQ, ks=KS, seed=0)

    near, err = ev(P_STAR)  # the candidate IS the target (same knobs + seed)
    far, _ = ev(np.array([0.0, 0.0, 3.0, 1.0, 0.4]))  # very different knobs

    # structural-fuzzing contract: (scalar score, dict of signed per-target errors)
    assert isinstance(near, float) and isinstance(err, dict) and err
    assert all("@" in key for key in err)
    assert {key.split("@")[0] for key in err} <= set(GATES)

    assert np.isfinite([near, far]).all()
    assert near < 1e-6  # exact reproduction -> ~zero mismatch
    assert far > near  # matching the target's geometry fits it better


def test_manifold_corpus_shape_norm_and_hyperbolic_branch():
    from openvector_bench.generator_search import MANIFOLD_PARAMS, manifold_corpus

    p = {name: dflt for name, _, _, dflt in MANIFOLD_PARAMS}
    x = manifold_corpus(p, 600, DIM, 5)
    assert x.shape == (600, DIM)
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)
    # the hyperbolic (Poincare exp_0) latent branch runs and stays finite
    xh = manifold_corpus({**p, "curvature": 2.0}, 600, DIM, 5)
    assert xh.shape == (600, DIM) and np.isfinite(xh).all()


def test_local_centers_off_is_byte_identical_to_round10():
    from openvector_bench.generator_search import (
        HIER_LC_PARAMS,
        hier_dupq_corpus,
        hier_lc_corpus,
    )

    p = {name: dflt for name, _, _, dflt in HIER_LC_PARAMS}
    assert p["lc_shells"] == 0.0  # the primitive's default is OFF
    x_lc = hier_lc_corpus(p, 900, DIM, 7)
    x_r10 = hier_dupq_corpus(p, 900, DIM, 7)
    assert np.array_equal(x_lc, x_r10)


def test_local_centers_count_response_is_a_dial():
    """PREREG_ROUND11 mechanism claim at unit-test scale: every shell member's
    nearest neighbours are its planted rows, so a planted row's k-occurrence
    count ~ its shell's membership — constructed, not emergent."""
    from openvector_bench.generator_search import local_centers
    from openvector_bench.geometry import knn, normalize

    n, m, p, n_shell = 2400, 4, 3, 80
    base = normalize(np.random.default_rng(0).standard_normal((n, DIM)))
    x, planted = local_centers(
        base,
        n_base=n,
        m=m,
        n_planted=p,
        n_shell=n_shell,
        radius=0.1,
        center_jit=0.05,
        rng=np.random.default_rng(1),
        return_rows=True,
    )
    assert x.shape == base.shape and len(planted) == m * p
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)
    _, idx = knn(x, x, p + 1)  # self lands in column 0; count columns 1..p
    counts = np.bincount(idx[:, 1:].ravel(), minlength=n).astype(np.float64)
    pmask = np.zeros(n, dtype=bool)
    pmask[planted] = True
    # Near-deterministic response: planted rows capture ~all member slots ...
    assert counts[pmask].sum() >= 0.9 * m * n_shell * p
    assert counts[pmask].min() >= 0.7 * n_shell
    # ... and no unplanted row comes close (the tail is constructed).
    assert counts[~pmask].max() <= 0.25 * n_shell


def test_make_evaluate_fn_accepts_the_manifold_family():
    from openvector_bench.generator_search import (
        MANIFOLD_PARAMS,
        manifold_corpus,
        measure_corpus,
    )

    p_star = np.array([d for _, _, _, d in MANIFOLD_PARAMS])
    # Same-instance split, matching make_evaluate_fn (see _target above).
    full = manifold_corpus({n: d for n, _, _, d in MANIFOLD_PARAMS}, N + NQ, DIM, 0)
    base, q = full[:N], full[N:]
    target = measure_corpus(base, q, ks=KS, batteries=("B",), n_query=NQ, seed=0)
    ev = make_evaluate_fn(
        target,
        dim=DIM,
        n=N,
        n_query=NQ,
        ks=KS,
        batteries=("B",),
        seed=0,
        generator=manifold_corpus,
        params_spec=MANIFOLD_PARAMS,
    )
    near, err = ev(p_star)
    assert isinstance(near, float) and err and near < 1e-6  # candidate == target
