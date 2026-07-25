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


def test_r12_mechanisms_off_is_byte_identical_to_round10():
    from openvector_bench.generator_search import (
        HIER_R12_PARAMS,
        hier_dupq_corpus,
        hier_r12_corpus,
    )

    p = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    # Every round-12 mechanism defaults OFF.
    assert p["grad_decay"] == 0.0 and p["grad_span"] == 1.0
    assert p["occ_mix"] == 0.0 and p["dens_span"] == 0.0
    x_r12 = hier_r12_corpus(p, 900, DIM, 7)
    x_r10 = hier_dupq_corpus(p, 900, DIM, 7)
    assert np.array_equal(x_r12, x_r10)


def test_r12_gradient_moves_twonn_and_stays_count_quiet():
    """PREREG_ROUND12 P-A at unit-test scale: the gradient field lowers the
    TwoNN reading (anisotropy dials local effective dimension) while leaving
    the count tail within noise of the mechanism-off control."""
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import id_twonn, knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}  # architecture off
    pg = p0 | {"grad_decay": 0.8, "grad_span": 8.0}
    n, nq, k = 3000, 300, 10

    def _measure(p, seed=11):
        x = hier_r12_corpus(p, n + nq, DIM, seed)
        base, q = x[:n], x[n:]
        d, idx = knn(base, q, k)
        counts = np.bincount(idx[:, :k].ravel(), minlength=n).astype(np.float64)
        sk = ((counts - counts.mean()) ** 3).mean() / max(counts.std() ** 3, 1e-12)
        return id_twonn(d), sk

    id0, sk0 = _measure(p0)
    idg, skg = _measure(pg)
    assert idg < 0.8 * id0  # the gradient mechanism moves G1 down
    assert abs(skg - sk0) < 0.5 * max(abs(sk0), 1.0)  # and is count-quiet


def test_r12_renewal_moves_count_tail():
    """PREREG_ROUND12 P-B mechanism direction at unit-test scale: renewal
    occupancy + density contrast raise the count tail. NOTE: strict
    ID-quietness is the registered stage-2 DECOUPLING CHECK at ladder scale,
    not a toy-scale property — at n=3000/DIM=64 the occupancy re-weighting
    measurably lowers the pooled TwoNN reading (~0.77x control; more
    within-patch neighbour pairs), which is exactly what the r12_stage1
    sweeps exist to quantify. Here we assert the dial works and the ID
    reading stays sane, not silent."""
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import id_twonn, knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}
    po = p0 | {"occ_mix": 1.0, "occ_tail": 1.2, "dens_span": 0.9}
    n, nq, k = 3000, 300, 10

    def _measure(p, seed=13):
        x = hier_r12_corpus(p, n + nq, DIM, seed)
        base, q = x[:n], x[n:]
        d, idx = knn(base, q, k)
        counts = np.bincount(idx[:, :k].ravel(), minlength=n).astype(np.float64)
        sk = ((counts - counts.mean()) ** 3).mean() / max(counts.std() ** 3, 1e-12)
        return id_twonn(d), sk

    id0, sk0 = _measure(p0)
    ido, sko = _measure(po)
    assert sko > 1.5 * max(sk0, 0.1)  # the renewal law moves the count tail up
    assert ido > 0.5 * id0  # sanity: no collapse (quietness: stage-2, at scale)


def test_r12_cascade_builds_the_graded_ladder():
    """Round-12 v2 P-A' mechanism signature at unit-test scale: the cascade
    puts base->base NN distances at graded fractional scales (real's
    diagnostic: r1 1%-quantile 0.375 vs median 0.86, diag_target.json), so
    the 1%-quantile/median ratio must drop sharply vs cascade-off — while
    the count tail stays within noise (uniform parents, no owners).
    n-FLATNESS itself is the registered ladder-scale question, not a toy
    property."""
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}
    pc = p0 | {"cascade_frac": 0.5}
    n, k = 3000, 10

    def _measure(p, seed=19):
        x = hier_r12_corpus(p, n, DIM, seed)
        base = x[: n - int(round(n / 9))]
        d, idx = knn(base, base, 2)  # col 0 = self, col 1 = true NN
        r1 = d[:, 1]
        ladder = float(np.quantile(r1, 0.01) / max(np.median(r1), 1e-12))
        d10, i10 = knn(base, base, k + 1)
        counts = np.bincount(i10[:, 1:].ravel(), minlength=len(base)).astype(np.float64)
        sk = ((counts - counts.mean()) ** 3).mean() / max(counts.std() ** 3, 1e-12)
        return ladder, sk

    lad0, sk0 = _measure(p0)
    ladc, skc = _measure(pc)
    # Measured at these settings: ratio 0.637 (off) -> 0.443 (frac 0.5) —
    # the cascade grades the WHOLE r1 distribution (median 0.49 -> 0.13),
    # and the shape ratio lands at real's 0.375/0.86 = 0.44. The threshold
    # asserts the direction, not the coincidence of the toy-scale match.
    assert ladc < 0.75 * lad0  # graded short-range mass appears
    assert abs(skc - sk0) < 0.75 * max(abs(sk0), 1.0)  # and no count tail


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
