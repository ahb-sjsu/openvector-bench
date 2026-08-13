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


def test_segment_corpus_is_random_access_and_chunk_invariant():
    """The property the harness version lacked (`R56`-`R61` port).

    Article boundaries there came from a cumsum over lognormal lengths, so row i
    could not be produced without its predecessors. Here every structural
    decision is a function of the index.
    """
    import numpy as np

    from openvector_bench.segment_gen import SEGMENT_PARAMS, segment_corpus

    p = {k: d for k, _, _, d in SEGMENT_PARAMS}
    full = segment_corpus(p, 4000, 64, 3)
    assert full.shape == (4000, 64)
    assert np.allclose(np.linalg.norm(full, axis=1), 1.0, atol=1e-4)

    # chunking must not change any row
    assert np.array_equal(full, segment_corpus(p, 4000, 64, 3, chunk=333))

    # arbitrary rows alone equal their value in a full generation
    pick = np.array([0, 1, 17, 999, 3999])
    assert np.array_equal(segment_corpus(p, 0, 64, 3, rows=pick), full[pick])

    # and a row far beyond any generated range is reproducible on its own
    a = segment_corpus(p, 0, 64, 3, rows=np.array([10**12, 10**12 + 1]))
    b = segment_corpus(p, 0, 64, 3, rows=np.array([10**12 + 1]))
    assert np.array_equal(a[1], b[0])


def test_segment_corpus_autocorrelation_decays_with_index_gap():
    """`R30`'s decay emerges from the segment structure rather than being fitted.

    `R32` had to fit level weights by NNLS to reproduce it; here it falls out.
    Real: 0.598, 0.530, 0.449, 0.367, 0.304 at gaps 1, 2, 4, 8, 16.
    """
    import numpy as np

    from openvector_bench.segment_gen import SEGMENT_PARAMS, segment_corpus

    p = {k: d for k, _, _, d in SEGMENT_PARAMS}
    x = segment_corpus(p, 6000, 128, 3)
    prev = 1.0
    for gap in (1, 2, 4, 8, 16, 64):
        cos = float(np.mean(np.sum(x[:3000] * x[gap:3000 + gap], axis=1)))
        assert cos < prev, "cosine must fall with index gap"
        prev = cos
    # the gap-1 value should be in the neighbourhood of real's 0.598
    g1 = float(np.mean(np.sum(x[:3000] * x[1:3001], axis=1)))
    assert 0.45 < g1 < 0.80, g1
