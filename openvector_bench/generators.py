"""Reference procedural generators with a pure-integer emission path.

``spec/DISTRIBUTION.md`` §3 requires the generator to avoid BLAS reductions
and transcendentals in the emission path wherever possible, because bit-exact
regeneration across toolchains is what lets a worker skip the download. The
v0 reference generator emits **raw Philox counter output** — no floats, no
reductions, no libm — so its bytes depend only on the counter-based PRNG
definition, not on threading, SIMD width, or libm version. Endianness is
pinned explicitly.

This is the *distribution* stand-in used by the reconstruction experiment
(spec §6). It is not a validated corpus extension: nothing generated here is
benchmark data until RC-1/RC-2 admit a real generator, and the registry keys
are versioned so an admitted generator arrives as a new ``impl`` string
rather than a mutation of an old one.
"""

from __future__ import annotations

import hashlib

import numpy as np


def shard_key(salt: str, shard_index: int) -> int:
    """128-bit Philox key from the published salt and the shard index."""
    digest = hashlib.sha256(f"{salt}:{shard_index}".encode()).digest()
    return int.from_bytes(digest[:16], "little")


def philox_u8(shard_index: int, params: dict) -> bytes:
    """``rows x dim`` uint8 shard from raw Philox output. Pure integers."""
    n = int(params["rows"]) * int(params["dim"])
    bg = np.random.Philox(key=shard_key(params["salt"], shard_index))
    words = bg.random_raw((n + 7) // 8)
    return np.asarray(words, dtype="<u8").tobytes()[:n]


GENERATORS: dict[str, object] = {
    "refcorpus.philox-u8:v0": philox_u8,
}
