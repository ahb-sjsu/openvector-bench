# SPDX-License-Identifier: MIT
"""Hierarchical bit-address generators: the corpus as a sparse high-order tensor.

**Status: EXPLORATORY.** This family is not registered against any round and
nothing measured with it can be cited as admission evidence. It exists to test
one mechanism question that closed the round-8 lineage
(``results/R20_CONVERGENCE.md``): *can a generator make intrinsic dimension
FALL with n by construction rather than by tuning?*

## Why a new construction rather than another parameter level

R19 and R20 established that ``local_dim`` and cluster count are **level**
parameters: they move the whole G1 curve without bending it. Real embeddings'
intrinsic dimension falls by a third across the ladder (26.64 -> 18.42 over
25k -> 200k); every member of the round-8 family produces a G1 that is flat or
rising. No setting of a level parameter converts a rising curve into a falling
one, so the fix has to live in the *construction*.

The mechanism here is **scale-dependent resolution**. Each row is addressed by
a bit-string; its vector is the sum of one displacement per address prefix, at
geometrically shrinking scale::

    x_i = sum_{l=0..L-1}  amp_l * d( node_l(i) )

where ``node_l(i)`` is the hash of row i's length-l address prefix. Two rows
that share a long prefix differ only in their deepest terms. As n grows, the
tree fills, nearest neighbours share longer prefixes, and the local geometry
around a point is dominated by *deeper* levels. So if the displacement at level
l is supported on ``m_l`` coordinates and ``m_l`` SHRINKS with depth, then
local intrinsic dimension falls as n rises -- by construction, with an exponent
that is a property of the level plan rather than a fitted slope.

``dim_decay`` is that knob, and ``dim_decay = 0`` is the control: constant
``m_l`` should reproduce the flat/rising G1 that sank the round-8 family. A
family that contains its own null is the point -- it makes the mechanism
falsifiable rather than merely plausible.

## The tensor reading (they are the same object)

An address ``(b_0, ..., b_{L-1})`` is a multi-index into an order-L tensor with
mode size ``B = 2**log2_branch``. The corpus occupies n entries of that index
space, and the emission rule above is a **hierarchical Tucker / tensor-train**
evaluation: one small transfer factor per tree node, contracted along the path
to the leaf. Storage is linear in L (``sum_l m_l`` floats per path), never the
``B**L`` of a dense core or the ``R**L`` of a flat Tucker core.

Crucially the factored form is the *definition*, not a decomposition fitted to
a materialized tensor -- so there is nothing to compress, and evaluation is
``O(L * m)`` per row with **random access**: any row emits without touching any
other row. That is what makes ``DISTRIBUTION.md``'s "no party ever holds the
corpus" operational rather than aspirational.

## Determinism

Every structural decision -- address, branch, support coordinates, signs -- is
integer arithmetic over ``uint64`` (splitmix64), so it is bit-identical on any
platform with no dependence on RNG stream versions, BLAS threading, or libm.
This is a deliberate contrast with the round-8 families, whose emission path
runs through ``default_rng().standard_normal``, ``np.cos``, ``@`` and
``np.linalg.qr`` -- all four of the hazards ``DISTRIBUTION.md`` §3 names, which
is why regeneration there can only ever be best-effort with a byte fallback.

Two float caveats, stated rather than hidden:

* The **level plan** (the table of ``(m_l, amp_l)``) is computed once from the
  knobs using ``pow``. A one-ULP difference could change a rounded ``m_l``, so
  the plan is exposed by :func:`level_plan` and is intended to travel in the
  manifest's parameter blob as an explicit table, not to be recomputed by each
  consumer. Amplitudes use repeated float32 multiplication (IEEE-deterministic)
  rather than ``pow`` for the same reason.
* Accumulation order is fixed (level by level, distinct coordinates within a
  level), so the float32 sum is reproducible. The byte-exact artifact is the
  pre-normalization array; L2 normalization is applied by the measurement code.
"""

from __future__ import annotations

import math

import numpy as np

from openvector_bench.geometry import normalize

_U64 = np.uint64
_ONE = _U64(1)

# splitmix64 constants (Steele et al.); pure integer, no platform dependence.
_GAMMA = _U64(0x9E3779B97F4A7C15)
_MIX1 = _U64(0xBF58476D1CE4E5B9)
_MIX2 = _U64(0x94D049BB133111EB)

# Domain-separation salts, so the same node hash drives independent decisions.
_SALT_BRANCH = _U64(0xA0761D6478BD642F)
_SALT_STRIDE = _U64(0xE7037ED1A0B428DB)
_SALT_SIGN = _U64(0x8EBC6AF09C88C6E3)
_SALT_LEVEL = _U64(0x589965CC75374CC3)
_SALT_ROW = _U64(0x1D8E4E27C47D124F)


def _sm64(z: np.ndarray) -> np.ndarray:
    """Vectorized splitmix64. Exact uint64 arithmetic, wraps like C."""
    with np.errstate(over="ignore"):
        z = z + _GAMMA
        z = (z ^ (z >> _U64(30))) * _MIX1
        z = (z ^ (z >> _U64(27))) * _MIX2
        return z ^ (z >> _U64(31))


BITMAP_PARAMS: tuple[tuple[str, float, float, float], ...] = (
    ("log2_branch", 1.0, 4.0, 1.0),  # bits per level -> branching B = 2**this
    ("depth", 4.0, 32.0, 20.0),  # tree levels = tensor order L
    ("scale_decay", 1.05, 3.0, 2.0),  # amplitude shrink per level
    ("dim_decay", 0.0, 1.0, 0.12),  # THE G1 KNOB: per-level shrink of m_l; 0 = null
    ("m0_frac", 0.005, 1.0, 0.05),  # level-0 support as a fraction of dim
    ("split_tail", 0.0, 2.5, 1.0),  # Zipf exponent on branch weights -> hubness
    ("noise", 0.0, 0.2, 0.02),  # isotropic floor, off any exact subspace
)


def level_plan(p: dict[str, float], dim: int) -> list[tuple[int, float]]:
    """The ``(support size, amplitude)`` table -- one entry per level.

    ``m_l`` shrinks **geometrically**, ``m0 * exp(-dim_decay * l)``, not as a
    power law. The lever arm is what forces this: neighbours separate at depth
    ``l* ~ log_B(n)``, so across the registered ladder (25k -> 200k at B=2)
    ``l*`` advances only about three levels. A power law is far too flat over
    three levels to move G1 by real's third; a geometric law makes the per-level
    ratio the knob directly, so the achievable drift is ``-dim_decay / ln B``
    per unit ``ln n`` -- a construction constant, which is the entire point.

    ``dim_decay = 0`` gives constant support: the null that must reproduce the
    round-8 failure.

    Belongs in the manifest parameter blob verbatim: recomputing it elsewhere
    reintroduces a ``pow``/``exp`` ULP as a correctness risk (module docstring).
    """
    depth = max(1, int(round(p["depth"])))
    m0 = max(1, int(round(p["m0_frac"] * dim)))
    decay = float(p["dim_decay"])
    plan: list[tuple[int, float]] = []
    amp = np.float32(1.0)
    shrink = np.float32(p["scale_decay"])
    for level in range(depth):
        m = max(1, int(round(m0 * math.exp(-decay * level))))
        plan.append((min(m, dim), float(amp)))
        amp = np.float32(amp / shrink)  # repeated multiply, never pow
    return plan


def _branch_cdf(branch: int, tail: float) -> np.ndarray:
    """Cumulative Zipf branch law -- unbalanced splits are what make hubs.

    A balanced tree gives a near-uniform measure and therefore no hubs at all;
    the heavy tail is what creates the density gradients hubness needs.

    Kept in float64 rather than uint64 thresholds: 2**64-1 is not representable
    in float64 (it rounds up to 2**64), so scaling a cumulative distribution to
    uint64 range overflows the cast. The draw is converted to a float in [0,1)
    by :func:`_unit` instead, which is exact.
    """
    w = np.arange(1, branch + 1, dtype=np.float64) ** (-tail)
    c = np.cumsum(w / w.sum())
    c[-1] = 1.0
    return c


def _unit(h: np.ndarray) -> np.ndarray:
    """uint64 hash -> float64 in [0, 1). Exact: a shift and a power-of-two scale."""
    return (h >> _U64(11)).astype(np.float64) * (1.0 / float(1 << 53))


def _walk(rows: np.ndarray, p: dict[str, float], seed: int, depth: int) -> np.ndarray:
    """Row indices -> the node hash at every level. Shape ``(len(rows), depth)``.

    The address is a biased walk: at each level the row draws a uniform and
    inverse-CDFs it against the node's branch law. The law is one fixed Zipf
    vector *rotated* per node, so which branch is fat varies across the tree
    without a per-node permutation.
    """
    branch = max(2, int(round(2 ** p["log2_branch"])))
    cdf = _branch_cdf(branch, float(p["split_tail"]))
    b64 = _U64(branch)

    row_h = _sm64(rows.astype(np.uint64) ^ (_sm64(_U64(seed)) + _SALT_ROW))
    node = _sm64(_U64(seed) ^ _SALT_LEVEL)
    node = np.full(len(rows), node, dtype=np.uint64)

    out = np.empty((len(rows), depth), dtype=np.uint64)
    for level in range(depth):
        lvl = _U64(level)
        u = _unit(_sm64(row_h ^ _sm64(lvl ^ _SALT_BRANCH)))
        slot = np.searchsorted(cdf, u, side="right").astype(np.uint64)
        with np.errstate(over="ignore"):
            b = (slot + (node % b64)) % b64
            node = _sm64(node ^ _sm64(b ^ (lvl * _GAMMA)))
        out[:, level] = node
    return out


def _emit(
    rows: np.ndarray,
    p: dict[str, float],
    dim: int,
    seed: int,
    plan: list[tuple[int, float]],
) -> np.ndarray:
    """One chunk of rows -> raw (unnormalized) float32 vectors."""
    nodes = _walk(rows, p, seed, len(plan))
    x = np.zeros((len(rows), dim), dtype=np.float32)
    ar = np.arange(len(rows))[:, None]
    dim64 = _U64(dim)

    for level, (m, amp) in enumerate(plan):
        v = nodes[:, level]
        # Support: an affine progression mod dim. dim is a power of two and the
        # stride is forced odd, so the m coordinates are DISTINCT -- which is
        # what lets the scatter below be a plain `+=` (no np.add.at) and keeps
        # accumulation order unambiguous.
        with np.errstate(over="ignore"):
            stride = (_sm64(v ^ _SALT_STRIDE) % (dim64 >> _ONE)) * _U64(2) + _ONE
            base = v % dim64
            idx = (base[:, None] + stride[:, None] * np.arange(m, dtype=np.uint64)) % (
                dim64
            )
        # Signs: 64 per hash call rather than one call per coordinate.
        nblk = (m + 63) // 64
        blocks = np.empty((len(rows), nblk), dtype=np.uint64)
        for k in range(nblk):
            with np.errstate(over="ignore"):
                blocks[:, k] = _sm64(v ^ (_SALT_SIGN + _U64(k) * _GAMMA))
        j = np.arange(m)
        sel = blocks[:, j // 64]
        bits = (sel >> (j % 64).astype(np.uint64)) & _ONE
        sign = np.float32(1.0) - np.float32(2.0) * bits.astype(np.float32)

        x[ar, idx.astype(np.int64)] += np.float32(amp / np.sqrt(m)) * sign

    noise = float(p["noise"])
    if noise > 0.0:
        # Integer-derived too, so the whole emission path stays bit-exact.
        with np.errstate(over="ignore"):
            h = _sm64(nodes[:, -1][:, None] ^ (np.arange(dim, dtype=np.uint64) + _GAMMA))
        x += np.float32(noise) * (_unit(h).astype(np.float32) - np.float32(0.5))
    return x


def emit_rows(
    p: dict[str, float],
    rows: np.ndarray,
    dim: int,
    seed: int,
    chunk: int = 8192,
) -> np.ndarray:
    """**Random access**: emit an arbitrary set of row indices, in any order.

    ``emit_rows(p, [7, 11], ...)`` equals rows 7 and 11 of a full generation.
    This is the property the distribution model needs -- a worker materializes
    only the shard it was assigned, at 10**12 as cheaply as at 10**5.
    """
    rows = np.asarray(rows, dtype=np.int64)
    plan = level_plan(p, dim)
    out = np.empty((len(rows), dim), dtype=np.float32)
    for s in range(0, len(rows), chunk):
        out[s : s + chunk] = _emit(rows[s : s + chunk], p, dim, seed, plan)
    return out


def bitmap_corpus(p: dict[str, float], n: int, dim: int, seed: int) -> np.ndarray:
    """Family entry point, matching ``generator_search.synth_corpus``'s contract.

    Returns unit-normed rows. ``dim`` must be a power of two (the distinct-support
    argument in ``_emit`` relies on it); the registered grid uses 1024.
    """
    if dim & (dim - 1):
        raise ValueError(f"dim must be a power of two, got {dim}")
    return normalize(emit_rows(p, np.arange(n, dtype=np.int64), dim, seed))
