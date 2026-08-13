"""Integer-exact, random-access pseudo-randomness for corpus emitters.

`DISTRIBUTION.md` §3 makes regeneration a first-class source, and `R48` measured
what that costs a float-heavy emitter: a float32 matrix product is not
bit-reproducible across platforms, because SIMD width and cache blocking reorder
the inner sum. `R22`/`R48` also measured why ``philox_u8`` *is* exact across
toolchains — it is pure integer arithmetic, with no floating point in the path.

This module supplies the same guarantee to a structured emitter. Every draw is a
deterministic function of its **key**, so:

* row ``i`` is computable without generating row ``i - 1``, at any index;
* the result does not depend on chunk size, thread count, RNG stream version,
  BLAS vendor, or libm;
* the same key gives the same bytes on any platform.

The pattern follows `bitmap_gen`, which established it, and generalises
`learned_gen.hash_noise` from ``(row, column)`` to arbitrary key tuples so a
construction with several nested levels can key each one independently.

**Why Irwin-Hall rather than Box-Muller.** The sum of 12 uniforms on [0,1) has
mean 6 and variance 1, so subtracting 6 gives a unit-variance approximately
normal variate using only additions. Box-Muller needs ``log``, ``sqrt`` and
``cos``, and libm is not bit-identical across platforms. The cost is tail
truncation at +-6 sigma, which is immaterial for geometry and is stated rather
than hidden.
"""

from __future__ import annotations

import numpy as np

_U64 = np.uint64
_MASK = _U64(0xFFFFFFFFFFFFFFFF)

# splitmix64 constants (Steele, Lea & Flood 2014). Pure integer.
_GAMMA = _U64(0x9E3779B97F4A7C15)
_MIX1 = _U64(0xBF58476D1CE4E5B9)
_MIX2 = _U64(0x94D049BB133111EB)

# Domain-separation salts, so one key drives independent decisions.
SALT_GAUSS = _U64(0x1D8E4E27C47D124F)
SALT_INDEX = _U64(0xA0761D6478BD642F)

UNIFORMS_PER_NORMAL = 12


def splitmix64(x: np.ndarray | int) -> np.ndarray:
    """The splitmix64 finaliser. Integer-exact on any platform."""
    z = (np.asarray(x, dtype=_U64) + _GAMMA) & _MASK
    with np.errstate(over="ignore"):
        z = ((z ^ (z >> _U64(30))) * _MIX1) & _MASK
        z = ((z ^ (z >> _U64(27))) * _MIX2) & _MASK
    return z ^ (z >> _U64(31))


def mix_keys(*keys) -> np.ndarray:
    """Fold several integer keys into one hash, order-dependently.

    Each key is folded through the finaliser in turn rather than XOR-ed
    together, so ``mix_keys(a, b) != mix_keys(b, a)`` and a level index cannot
    collide with a row index.
    """
    acc = None
    for k in keys:
        k64 = np.asarray(k, dtype=np.int64).astype(_U64)
        acc = k64 if acc is None else splitmix64(acc ^ splitmix64(k64))
    return splitmix64(acc)


def hash_uniform(*keys, count: int = 1, salt: int = 0) -> np.ndarray:
    """``count`` uniforms on [0,1) per key, as float32. Deterministic."""
    base = splitmix64(mix_keys(*keys) ^ _U64(np.uint64(salt)))
    cols = np.arange(count, dtype=_U64)
    with np.errstate(over="ignore"):
        h = splitmix64(base[..., None] ^ (cols + splitmix64(cols)))
    # Top 53 bits -> a double in [0,1), then narrow. The shift keeps the
    # high-quality bits and the division is an exact power of two.
    return ((h >> _U64(11)).astype(np.float64) / float(1 << 53)).astype(np.float32)


def hash_gaussian(*keys, count: int = 1, salt: int = 0) -> np.ndarray:
    """``count`` unit-variance pseudo-Gaussian draws per key, as float32.

    Irwin-Hall over :func:`hash_uniform`; additions only, no transcendentals.
    Truncated at +-6 sigma by construction.
    """
    base = splitmix64(mix_keys(*keys) ^ _U64(np.uint64(salt)) ^ SALT_GAUSS)
    cols = np.arange(count, dtype=_U64)
    shape = base.shape + (count,)
    out = np.zeros(shape, dtype=np.float32)
    with np.errstate(over="ignore"):
        for t in range(UNIFORMS_PER_NORMAL):
            tt = _U64(t)
            h = splitmix64(base[..., None] ^ (cols + tt * splitmix64(tt + SALT_GAUSS)))
            out += ((h >> _U64(11)).astype(np.float64) / float(1 << 53)).astype(
                np.float32
            )
    return out - np.float32(UNIFORMS_PER_NORMAL / 2)


def hash_index(*keys, count: int = 1, modulus: int, salt: int = 0) -> np.ndarray:
    """``count`` uniform integers in ``[0, modulus)`` per key, as int64.

    Used to select directions from a shared pool. The modulo introduces a bias
    of order ``modulus / 2**64``, which is below 2**-40 for any pool size in use
    here and is preferred to rejection sampling because it keeps the draw a pure
    function of the key.
    """
    base = splitmix64(mix_keys(*keys) ^ _U64(np.uint64(salt)) ^ SALT_INDEX)
    cols = np.arange(count, dtype=_U64)
    with np.errstate(over="ignore"):
        h = splitmix64(base[..., None] ^ (cols + splitmix64(cols + SALT_INDEX)))
    return (h % _U64(np.uint64(modulus))).astype(np.int64)
