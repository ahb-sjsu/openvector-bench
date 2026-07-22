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
    base = synth_corpus(decode(p), N, DIM, seed)
    q = synth_corpus(decode(p), NQ, DIM, seed + 1)
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
