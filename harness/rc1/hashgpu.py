"""Torch splitmix64 on GPU, verified bit-for-bit against the numpy reference.

`R48` established that regeneration must be integer-exact, and `R50` kept the
hashing in numpy for exactly that reason. But NRP kills GPU pods below 40%
utilisation, and a numpy-CPU hash path leaves the GPU idle through the whole
build -- which is what killed the first R55 pod after 36 seconds.

So the hash moves to torch, and correctness is preserved the only honest way:
numpy stays the reference, torch is checked against it at startup, and the run
aborts on any mismatch.

Two care points, both about int64 masquerading as uint64:

* torch's ``>>`` on int64 is **arithmetic** (sign-extending). Every shift here
  is therefore masked to give a logical shift.
* multiplication and addition wrap mod 2**64 in two's complement, so the low 64
  bits agree with uint64 arithmetic without further work.

``hidx`` uses the top 53 bits before the modulo in *both* implementations, so
the two agree exactly rather than approximately -- taking ``h % m`` directly
would differ, because a uint64 above 2**63 is negative as int64.
"""

import numpy as np
import torch

U64 = np.uint64
_MASK = U64(0xFFFFFFFFFFFFFFFF)
_GAMMA_U = U64(0x9E3779B97F4A7C15)
_MIX1_U = U64(0xBF58476D1CE4E5B9)
_MIX2_U = U64(0x94D049BB133111EB)

# Same bit patterns, reinterpreted as int64 for torch.
GAMMA_I = int(np.int64(_GAMMA_U.astype(np.int64)))
MIX1_I = int(np.int64(_MIX1_U.astype(np.int64)))
MIX2_I = int(np.int64(_MIX2_U.astype(np.int64)))


# ---------------------------------------------------------------- numpy ref
def sm64_np(x):
    z = (np.asarray(x, dtype=U64) + _GAMMA_U) & _MASK
    with np.errstate(over="ignore"):
        z = ((z ^ (z >> U64(30))) * _MIX1_U) & _MASK
        z = ((z ^ (z >> U64(27))) * _MIX2_U) & _MASK
    return z ^ (z >> U64(31))


def _base_np(key, salt, extra):
    return sm64_np(sm64_np(np.asarray(key, dtype=np.int64).astype(U64))
                   ^ U64(np.uint64(salt)) ^ U64(np.uint64(extra)))


def hgauss_np(key, count, salt=0):
    base = _base_np(key, salt, 0)
    cols = np.arange(count, dtype=U64)
    out = np.zeros(base.shape + (count,), dtype=np.float32)
    with np.errstate(over="ignore"):
        for t in range(12):
            tt = U64(t)
            h = sm64_np(base[..., None] ^ (cols + tt * sm64_np(tt + U64(7))))
            out += ((h >> U64(11)).astype(np.float64) / float(1 << 53)).astype(np.float32)
    return out - np.float32(6.0)


def hunif_np(key, count, salt=0):
    base = _base_np(key, salt, 99)
    cols = np.arange(count, dtype=U64)
    with np.errstate(over="ignore"):
        h = sm64_np(base[..., None] ^ (cols + sm64_np(cols)))
    return ((h >> U64(11)).astype(np.float64) / float(1 << 53)).astype(np.float32)


def hidx_np(key, count, modulus, salt=0):
    base = _base_np(key, salt, 31)
    cols = np.arange(count, dtype=U64)
    with np.errstate(over="ignore"):
        h = sm64_np(base[..., None] ^ (cols + sm64_np(cols + U64(31))))
    return ((h >> U64(11)) % U64(np.uint64(modulus))).astype(np.int64)


# ---------------------------------------------------------------- torch/GPU
def _lsr(x, n):
    """Logical right shift. torch's >> on int64 sign-extends."""
    return (x >> n) & ((1 << (64 - n)) - 1)


def sm64_t(x):
    z = x + GAMMA_I
    z = (z ^ _lsr(z, 30)) * MIX1_I
    z = (z ^ _lsr(z, 27)) * MIX2_I
    return z ^ _lsr(z, 31)


def _base_t(key, salt, extra):
    return sm64_t(sm64_t(key) ^ int(np.int64(np.uint64(salt))) ^ int(np.int64(np.uint64(extra))))


def hgauss_t(key, count, salt=0):
    base = _base_t(key, salt, 0)
    cols = torch.arange(count, dtype=torch.int64, device=key.device)
    out = torch.zeros(base.shape + (count,), dtype=torch.float32, device=key.device)
    for t in range(12):
        tt = torch.tensor(t, dtype=torch.int64, device=key.device)
        h = sm64_t(base.unsqueeze(-1) ^ (cols + tt * sm64_t(tt + 7)))
        out += (_lsr(h, 11).double() / float(1 << 53)).float()
    return out - 6.0


def hunif_t(key, count, salt=0):
    base = _base_t(key, salt, 99)
    cols = torch.arange(count, dtype=torch.int64, device=key.device)
    h = sm64_t(base.unsqueeze(-1) ^ (cols + sm64_t(cols)))
    return (_lsr(h, 11).double() / float(1 << 53)).float()


def hidx_t(key, count, modulus, salt=0):
    base = _base_t(key, salt, 31)
    cols = torch.arange(count, dtype=torch.int64, device=key.device)
    h = sm64_t(base.unsqueeze(-1) ^ (cols + sm64_t(cols + 31)))
    return _lsr(h, 11) % int(modulus)


def verify(device):
    """Abort the run rather than trust an unverified hash path."""
    key = np.array([0, 1, 7, 1000, 10 ** 7, 2 ** 31 - 1, 10 ** 12,
                    -5, 123456789], dtype=np.int64)
    kt = torch.from_numpy(key).to(device)
    checks = [
        ("sm64", sm64_np(key.astype(U64)).astype(np.int64),
         sm64_t(kt).cpu().numpy()),
        ("hidx", hidx_np(key, 16, 8192), hidx_t(kt, 16, 8192).cpu().numpy()),
    ]
    for name, a, b in checks:
        if not np.array_equal(a, b):
            raise SystemExit("HASH MISMATCH in %s -- aborting (R48 guarantee)" % name)
    for name, a, b in (("hgauss", hgauss_np(key, 16), hgauss_t(kt, 16).cpu().numpy()),
                       ("hunif", hunif_np(key, 16), hunif_t(kt, 16).cpu().numpy())):
        if not np.array_equal(a, b):
            d = np.abs(a - b).max()
            raise SystemExit("HASH MISMATCH in %s (max |d| %g) -- aborting" % (name, d))
    print("hash verify: torch == numpy, bit-for-bit, on all four entry points",
          flush=True)
