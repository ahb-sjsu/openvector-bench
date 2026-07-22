# SPDX-License-Identifier: MIT
"""EC generators: byte-reproducible, unit-normed, right shape. The *geometry*
claims (ec_ff ~ null, ec_torus has controllable ID but no hubness) are settled by
harness/generator/ec_experiment.py, not asserted here."""

from __future__ import annotations

import numpy as np

from openvector_bench.ec_generators import (
    ec_ff_corpus,
    ec_torus_corpus,
    gaussian_null_corpus,
)

DIM = 128


def _check(fn, p):
    x = fn(p, 400, DIM, 7)
    assert x.shape == (400, DIM)
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)
    assert np.isfinite(x).all()
    np.testing.assert_array_equal(x, fn(p, 400, DIM, 7))  # byte-reproducible


def test_ec_ff():
    _check(ec_ff_corpus, {"field_bits": 14})


def test_ec_torus():
    _check(ec_torus_corpus, {"latent_dim": 20.0})


def test_gaussian_null():
    _check(gaussian_null_corpus, {})
