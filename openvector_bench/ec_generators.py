# SPDX-License-Identifier: MIT
"""Elliptic-curve corpus generators — a registered falsification probe.

Tests, against the RC-1 battery, whether "points on an elliptic curve" make a
plausible embedding-geometry generator. The name denotes two very different
objects, and the experiment separates them:

* :func:`ec_ff_corpus` — the **cryptographic** object: coordinates of scalar
  multiples ``k·G`` on a curve over a finite field ``F_p``. Its defining property
  is that ``k·G`` is pseudo-uniform over the group (that uniformity *is* ECDLP
  hardness), so the prediction is that it lands on the iid-uniform null RC-1
  rejects: intrinsic dimension too high, no hubness. Uniformity is the enemy.

* :func:`ec_torus_corpus` — the **geometric** object: a real elliptic curve is a
  1-manifold and over ℂ a flat torus ``ℂ/Λ``; a product of ``g`` of them (an
  abelian variety) is a flat ``g``-torus. Uniformly sampled and embedded, it has
  a *controllable* intrinsic dimension (the right category!) but, being flat and
  homogeneous, still has **no hubness** — the inhomogeneity that makes real
  embeddings hard is exactly what the group/torus does not supply.

Both are byte-reproducible from ``(seed, row)`` like every family, so they plug
into the same :func:`~openvector_bench.generator_search.measure_corpus`. This
module makes a prediction the experiment then confirms or refutes; a refutation
would be reported as a refutation (PREREG_RC1 §1).
"""

from __future__ import annotations

import numpy as np

from .geometry import normalize


def _is_prime(m: int) -> bool:
    """Deterministic Miller-Rabin for the small (< 2^32) primes used here."""
    if m < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if m % q == 0:
            return m == q
    d, r = m - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, m)
        if x in (1, m - 1):
            continue
        for _ in range(r - 1):
            x = x * x % m
            if x == m - 1:
                break
        else:
            return False
    return True


def _prime_3mod4_below(hi: int) -> int:
    """Largest prime p ≡ 3 (mod 4) below ``hi`` — gives sqrt via x^((p+1)/4)."""
    m = hi - 1 - (hi - 1) % 4 + 3  # largest <= hi with m ≡ 3 (mod 4)
    if m >= hi:
        m -= 4
    while m > 3:
        if _is_prime(m):
            return m
        m -= 4
    raise ValueError("no prime found")


def _ec_add(pt, q, a: int, p: int):
    """Group law on y^2 = x^3 + a x + b over F_p; ``None`` is the point at infinity."""
    if pt is None:
        return q
    if q is None:
        return pt
    x1, y1 = pt
    x2, y2 = q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if pt == q:
        lam = (3 * x1 * x1 + a) * pow(2 * y1 % p, p - 2, p) % p
    else:
        lam = (y2 - y1) * pow((x2 - x1) % p, p - 2, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


_XTAB_CACHE: dict[int, tuple[int, np.ndarray]] = {}


def _x_table(field_bits: int) -> tuple[int, np.ndarray]:
    """Walk the cyclic subgroup <G> once; return ``(ord, X)`` with ``X[m]=x(m·G)/p``.

    Cached per field size. ``X[0]`` (the identity) is set to 0. This turns EC
    scalar multiplication into an O(1) table lookup: ``x(m·G) = X[m mod ord]``.
    """
    if field_bits in _XTAB_CACHE:
        return _XTAB_CACHE[field_bits]
    p = _prime_3mod4_below(1 << field_bits)
    a, b = 2, 3  # a fixed, unremarkable curve; the finding is family-level

    def walk(gx: int, gy: int) -> list[float]:
        xs = [0.0]  # index 0 = identity
        pt = (gx, gy)
        while pt is not None and len(xs) <= 2 * p:
            xs.append(float(pt[0]))
            pt = _ec_add(pt, (gx, gy), a, p)
        return xs

    # Scan base points and take one whose subgroup <G> is large (>= p/2 points),
    # so the corpus coordinates sample the field densely rather than a tiny cycle.
    best: list[float] = [0.0]
    for x in range(1, p):
        t = (x * x * x + a * x + b) % p
        if pow(t, (p - 1) // 2, p) != 1:  # not a quadratic residue
            continue
        y = pow(t, (p + 1) // 4, p)
        if y * y % p != t:
            continue
        xs = walk(x, y)
        if len(xs) > len(best):
            best = xs
        if len(best) >= p // 2:
            break
    if len(best) <= 1:
        raise ValueError("no base point")
    order = len(best)
    x_arr = (np.asarray(best, dtype=np.float64) / p - 0.5).astype(np.float32)
    x_arr[0] = 0.0
    _XTAB_CACHE[field_bits] = (order, x_arr)
    return order, x_arr


def ec_ff_corpus(p: dict, n: int, dim: int, seed: int) -> np.ndarray:
    """Finite-field EC corpus: coordinate ``j`` of row ``i`` is ``x((k_i·j)·G)/p``.

    Each row draws a scalar ``k_i``; the ``dim`` coordinates read the x-coordinates
    of ``(k_i·j)·G`` for ``j = 1..dim`` (all in ``<G>``, since the group is
    cyclic). Because EC scalar multiplication is pseudo-uniform, both rows and
    columns are near-uniform and independent — the vector is ≈ uniform on a
    shell. Byte-reproducible from ``(seed, curve)``.
    """
    field_bits = int(p.get("field_bits", 16))
    order, x_arr = _x_table(field_bits)
    rng = np.random.default_rng(seed)
    k = rng.integers(1, order, size=n, dtype=np.int64)
    j = (np.arange(1, dim + 1, dtype=np.int64)) % order
    idx = (k[:, None] * j[None, :]) % order
    x = x_arr[idx]
    return normalize(x)


def ec_torus_corpus(p: dict, n: int, dim: int, seed: int) -> np.ndarray:
    """Flat ``g``-torus corpus: a product of ``g`` real elliptic curves / abelian variety.

    Uniform angles on ``g`` circle factors, embedded as ``(cos θ, sin θ)`` and
    randomly projected to ``dim``. Intrinsic dimension ≈ ``g`` (the geometric EC
    object is the *right category* of low-dim manifold), but the sampling is flat
    and homogeneous, so hubness is null — the property the group law does not
    supply. ``latent_dim`` sets ``g``.
    """
    rng = np.random.default_rng(seed)
    g = int(round(p.get("latent_dim", 52.0)))
    g = max(1, min(g, dim // 2))
    theta = rng.uniform(0.0, 2.0 * np.pi, (n, g)).astype(np.float32)
    feats = np.concatenate([np.cos(theta), np.sin(theta)], axis=1)
    proj = rng.standard_normal((2 * g, dim)).astype(np.float32) / np.sqrt(2 * g)
    x = feats @ proj
    noise = float(p.get("noise", 0.0))
    if noise:
        x += np.float32(noise) * rng.standard_normal(x.shape).astype(np.float32)
    return normalize(x)


def gaussian_null_corpus(p: dict, n: int, dim: int, seed: int) -> np.ndarray:
    """iid Gaussian on the unit sphere — the reference null (PREREG_RC1 §8.1)."""
    rng = np.random.default_rng(seed)
    return normalize(rng.standard_normal((n, dim)).astype(np.float32))
