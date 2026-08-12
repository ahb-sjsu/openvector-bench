"""Is a float-heavy emitter cross-toolchain reproducible? — `R48`.

`R22` showed `philox_u8` regenerates byte-identically across toolchains, and the
reason is structural: pure integer arithmetic, no floating point in the path.
The geometry generators use QR factorisations, normal draws and matrix products,
so the guarantee has to be tested rather than inherited.

Run on two platforms and compare. Measured Windows/numpy 2.3.5 vs
Linux glibc2.39/numpy 2.4.4:

    QR alone            identical
    float32 A @ B       DIFFERS      <- SIMD width and blocking reorder the sum
    float64 A @ B       identical
    fixed-order loop    identical

`geometry.reproducible_matmul` implements the fixed-order accumulation and is
applied to `twoscale_gen`; after that both generators agree across platforms.

Usage:
    python harness/rc1/float_repro.py            # emit this platform's hashes
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys

import numpy as np

from openvector_bench.geometry import normalize, reproducible_matmul


def _h(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]


def probe() -> dict:
    rng = np.random.default_rng(7)
    a = rng.standard_normal((512, 64)).astype(np.float32)
    b = rng.standard_normal((64, 128)).astype(np.float32)

    out = {
        "toolchain": {"platform": platform.platform(),
                      "python": platform.python_version(),
                      "numpy": np.__version__},
        "rng_inputs": {"a": _h(a), "b": _h(b)},
        "matmul_f32": _h(a @ b),
        "matmul_f64": _h(a.astype(np.float64) @ b.astype(np.float64)),
        "reproducible_matmul": _h(reproducible_matmul(a, b)),
    }

    # The QR alone, which is reproducible, separated from the product that is not.
    r2 = np.random.default_rng(41)
    q = np.linalg.qr(r2.standard_normal((128, 32)))[0].astype(np.float32)
    out["qr_only"] = _h(q)

    coef = r2.standard_normal((8000, 32)).astype(np.float32)
    coef /= np.maximum(np.linalg.norm(coef, axis=1, keepdims=True), 1e-12)
    out["build_matmul_f32"] = _h(normalize(coef @ q.T))
    out["build_reproducible"] = _h(normalize(reproducible_matmul(coef, q.T)))
    return out


def main() -> int:
    json.dump(probe(), sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
