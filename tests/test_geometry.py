"""The battery must discriminate: a structured corpus and an iid Gaussian of
matched dimension cannot look alike under the registered diagnostics."""

import numpy as np

from openvector_bench.geometry import id_twonn, knn, normalize, spectrum


def _lowrank(n=3000, dim=64, rank=8, seed=0):
    rng = np.random.default_rng(seed)
    basis = rng.standard_normal((rank, dim))
    return (rng.standard_normal((n, rank)) @ basis).astype(np.float32)


def test_knn_is_exact_against_brute_force():
    rng = np.random.default_rng(1)
    base = normalize(rng.standard_normal((500, 16)).astype(np.float32))
    q = normalize(rng.standard_normal((20, 16)).astype(np.float32))
    _, idx = knn(base, q, 5)
    d2 = ((q[:, None, :] - base[None, :, :]) ** 2).sum(-1)
    assert np.array_equal(idx[:, 0], d2.argmin(1))


def test_effective_rank_tracks_construction():
    eff, _ = spectrum(_lowrank(rank=8))
    assert 2.0 < eff < 20.0


def test_intrinsic_dimension_separates_structure_from_noise():
    rng = np.random.default_rng(2)
    lr = normalize(_lowrank(rank=8))
    iid = normalize(rng.standard_normal((3000, 64)).astype(np.float32))
    d_lr, _ = knn(lr[500:], lr[:500], 10)
    d_iid, _ = knn(iid[500:], iid[:500], 10)
    assert id_twonn(d_lr) < id_twonn(d_iid)
