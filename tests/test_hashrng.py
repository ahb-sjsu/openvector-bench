"""Integer-exact, random-access randomness — the `DISTRIBUTION.md` §3 contract.

`R48` measured what a float-heavy emitter costs: a float32 matmul is not
bit-reproducible across platforms. `R22` measured why `philox_u8` is — pure
integer arithmetic. These tests pin the properties a structured emitter needs to
inherit that guarantee.
"""

from __future__ import annotations

import numpy as np

from openvector_bench.hashrng import (
    hash_gaussian,
    hash_index,
    hash_uniform,
    mix_keys,
    splitmix64,
)


def test_gaussian_is_unit_variance_and_zero_mean():
    g = hash_gaussian(np.arange(20_000), count=8)
    assert g.shape == (20_000, 8) and g.dtype == np.float32
    assert abs(float(g.mean())) < 0.01
    assert abs(float(g.std()) - 1.0) < 0.01
    # Irwin-Hall truncates at +-6 sigma; state it rather than hide it.
    assert float(np.abs(g).max()) <= 6.0


def test_random_access_at_a_large_index():
    """Row i must be computable without generating row i-1, at any index."""
    batch = hash_gaussian(np.array([10**14, 10**14 + 1, 10**14 + 2]), count=4)
    alone = hash_gaussian(np.array([10**14 + 1]), count=4)
    assert np.array_equal(batch[1], alone[0])


def test_chunking_does_not_change_any_value():
    full = hash_gaussian(np.arange(5000), count=4)
    parts = np.concatenate([hash_gaussian(np.arange(i, min(i + 137, 5000)), count=4)
                            for i in range(0, 5000, 137)])
    assert np.array_equal(full, parts)


def test_key_order_matters_so_levels_cannot_collide_with_rows():
    """A level index and a row index must not alias each other."""
    assert mix_keys(3, 7)[()] != mix_keys(7, 3)[()]
    a = hash_gaussian(np.full(4, 1), np.arange(4), count=2)
    b = hash_gaussian(np.arange(4), np.full(4, 1), count=2)
    assert not np.array_equal(a, b)


def test_ranges_and_determinism():
    rows = np.arange(2000)
    u = hash_uniform(rows, count=4)
    assert float(u.min()) >= 0.0 and float(u.max()) < 1.0
    i = hash_index(rows, count=4, modulus=8192)
    assert int(i.min()) >= 0 and int(i.max()) < 8192
    assert np.array_equal(hash_uniform(rows, count=4), u)
    # splitmix64 is a bijection on uint64; distinct inputs stay distinct.
    h = splitmix64(np.arange(10_000, dtype=np.uint64))
    assert len(np.unique(h)) == 10_000
