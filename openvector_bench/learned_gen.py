# SPDX-License-Identifier: MIT
"""A learned emitter: hash noise -> small fixed map -> corpus row.

**Status: EXPLORATORY.** Not registered, no admission claim, seal untouched.

## Why a learned map, when six hand-designed families are closed

`R25_ANISOTROPY_CONTROLS.md` showed the dimension ramp is carried by structure
**beyond the first two moments**: a Gaussian with real's exact mean and
covariance produces a flat profile (+0.021 against real's +0.511). So any
family whose geometry is fixed by its covariance is excluded a priori, and the
hand-designed families that remain all produce a *falling* profile at every rung
(`results/family_profile_scan.json`). The gap looks mechanistic rather than
parametric.

A learned map is the cheapest way to obtain beyond-second-moment structure
without having to guess its form — which matters, because guessing is what has
failed six times.

## Why this can be cheap enough to be legal

`DISTRIBUTION.md` §3 orders sources *regenerate -> cache -> mirror* because
regeneration is faster than fetching. That is a **ratio**, not a total, so no
amount of extra compute rescues a slow emitter: at LaBSE's 17.7 kB/s/core
regeneration is ~2300x slower than the network and the ordering inverts.

The bound is roughly 10 MB/s/core, i.e. ~4 MFLOPs/row at 4 KB/row. A 2-layer
map with hidden width ``H`` costs ``2*D*H`` MACs/row — at D=1024, H=64 that is
0.13 MFLOPs/row, **thirty times inside the bound**. A transformer cannot fit
here; this can.

## Determinism

The input noise comes from `bitmap_gen`'s splitmix64, so it is integer-exact
and random-access: row *i* emits without touching any other row. The Gaussian
is built by **Irwin-Hall** (sum of 12 uniforms minus 6) rather than Box-Muller
or an inverse-CDF, because that needs only additions — no transcendentals, no
libm, hence bit-identical across platforms. The remaining float work is a small
fixed-size matmul, which is the one thing a fixed-point port would have to pin
down (fixed accumulation order); the structural path is already exact.

## Shape

    z = irwin_hall(hash(seed, row))                     (n, D) pseudo-Gaussian
    h = tanh(z @ W1 + b1)                               (n, H)
    x = alpha * z + h @ W2                              (n, D)  skip + map
    row = x / ||x||

The skip term keeps the map a *perturbation* of a Gaussian at initialisation,
so training starts from a known-flat profile and any ramp it acquires is
attributable to the learned part. `tanh` is the only transcendental and is
replaceable by a fixed polynomial in a bit-exact port.

Weights are the generator spec: ~131k float32 = 525 KB, hashed and shipped in
the manifest like any other parameter blob.
"""

from __future__ import annotations

import numpy as np

from openvector_bench.bitmap_gen import _sm64, _U64

_SALT_Z = _U64(0x27D4EB2F165667C5)
UNIFORMS_PER_NORMAL = 12  # Irwin-Hall order; 12 gives unit variance exactly


def hash_noise(rows: np.ndarray, dim: int, seed: int) -> np.ndarray:
    """Integer-exact pseudo-Gaussian noise, one independent draw per (row, j).

    Irwin-Hall: the sum of 12 uniforms on [0,1) has mean 6 and variance 1, so
    subtracting 6 gives a unit-variance, approximately normal variate using
    only additions. Deterministic, random-access, and free of transcendentals.
    """
    rows = np.asarray(rows, dtype=np.int64)
    out = np.zeros((len(rows), dim), dtype=np.float32)
    base = _sm64(rows.astype(np.uint64) ^ (_sm64(_U64(seed)) + _SALT_Z))
    cols = np.arange(dim, dtype=np.uint64)
    with np.errstate(over="ignore"):
        for t in range(UNIFORMS_PER_NORMAL):
            h = _sm64(base[:, None] ^ (cols + _U64(t) * _sm64(_U64(t) + _SALT_Z)))
            out += ((h >> _U64(11)).astype(np.float64) * (1.0 / float(1 << 53))).astype(
                np.float32
            )
    return out - np.float32(UNIFORMS_PER_NORMAL / 2)


def init_params(dim: int, hidden: int, seed: int = 0) -> dict:
    """Small init: the map starts as a near-identity perturbation of Gaussian."""
    rng = np.random.default_rng(seed)
    return {
        "W1": (rng.standard_normal((dim, hidden)) / np.sqrt(dim)).astype(np.float32),
        "b1": np.zeros(hidden, dtype=np.float32),
        "W2": (rng.standard_normal((hidden, dim)) / np.sqrt(hidden) * 0.1).astype(
            np.float32
        ),
        "alpha": np.float32(1.0),
    }


def forward_np(z: np.ndarray, p: dict) -> np.ndarray:
    """Deployment path (numpy). Mirrors :func:`forward_torch` exactly."""
    h = np.tanh(z @ p["W1"] + p["b1"])
    x = np.float32(p["alpha"]) * z + h @ p["W2"]
    n = np.sqrt(np.maximum((x * x).sum(1, keepdims=True), 1e-24))
    return (x / n).astype(np.float32)


def emit_rows(
    p: dict, rows: np.ndarray, dim: int, seed: int, chunk: int = 8192
) -> np.ndarray:
    """Random-access emission of an arbitrary set of rows, in any order."""
    rows = np.asarray(rows, dtype=np.int64)
    out = np.empty((len(rows), dim), dtype=np.float32)
    for s in range(0, len(rows), chunk):
        sl = rows[s : s + chunk]
        out[s : s + chunk] = forward_np(hash_noise(sl, dim, seed), p)
    return out


def learned_corpus(p: dict, n: int, dim: int, seed: int) -> np.ndarray:
    """Family entry point, matching ``synth_corpus``'s contract."""
    return emit_rows(p, np.arange(n, dtype=np.int64), dim, seed)


def flops_per_row(dim: int, hidden: int) -> float:
    """MACs per emitted row — the number that decides whether this is legal."""
    return 2.0 * dim * hidden


def save_params(p: dict, path: str) -> None:
    np.savez(path, **{k: np.asarray(v) for k, v in p.items()})


def load_params(path: str) -> dict:
    d = np.load(path)
    out = {k: d[k] for k in d.files}
    out["alpha"] = np.float32(out["alpha"])
    return out
