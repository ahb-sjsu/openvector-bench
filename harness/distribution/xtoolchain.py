"""Cross-toolchain regeneration rate — `DISTRIBUTION.md` §6 "reported regardless".

`R22` demonstrated the reconstruction chain but regenerated within a single
Python/numpy build, leaving the reportable §3 actually cares about untested:
regeneration-success rate *across* toolchains. That number decides whether the
regeneration tier is a reliable source or an occasional optimisation.

Run this on two platforms with the same salt and compare the JSON. The emitter
under test must be pure integer arithmetic — `philox_u8` is a counter-based bit
generator with no floating point in the path, so there is nothing for a platform
to round differently. That is a design requirement for any RC-1 emitter, not a
property to be discovered after the fact.

Measured 2026-08-11: 16/16 byte-identical across Windows/numpy 2.3.5 and
Linux glibc2.39/numpy 2.4.4 (`results/xtoolchain.json`).

Usage:
    python harness/distribution/xtoolchain.py > toolchain_a.json
    # on the other platform
    python harness/distribution/xtoolchain.py > toolchain_b.json
    python harness/distribution/xtoolchain.py --compare toolchain_a.json toolchain_b.json
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys

import numpy

from openvector_bench.generators import philox_u8

PARAMS = {"rows": 4096, "dim": 128, "salt": "ovb-xtool-test"}
# Spread across the index space, including past 2**31 and 2**32 where a
# careless implementation would wrap.
SHARDS = [
    0,
    1,
    2,
    3,
    7,
    15,
    63,
    255,
    1000,
    4095,
    65535,
    1_000_000,
    10**7,
    2**31 - 1,
    2**32 + 17,
    10**12,
]


def fingerprint() -> dict:
    return {
        "toolchain": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": numpy.__version__,
        },
        "params": PARAMS,
        "sha256": {
            str(s): hashlib.sha256(philox_u8(s, PARAMS)).hexdigest() for s in SHARDS
        },
    }


def compare(path_a: str, path_b: str) -> int:
    a = json.load(open(path_a, encoding="utf-8"))
    b = json.load(open(path_b, encoding="utf-8"))
    for tag, side in (("A", a), ("B", b)):
        t = side["toolchain"]
        print(f"{tag}: {t['platform']}  python {t['python']}  numpy {t['numpy']}")
    keys = sorted(a["sha256"], key=int)
    match = [k for k in keys if a["sha256"][k] == b["sha256"].get(k)]
    print(
        f"\ncross-toolchain regeneration: {len(match)}/{len(keys)} byte-identical "
        f"({100.0 * len(match) / len(keys):.1f}%)"
    )
    for k in keys:
        if a["sha256"][k] != b["sha256"].get(k):
            print(
                f"  MISMATCH shard {k}: {a['sha256'][k][:16]} vs "
                f"{str(b['sha256'].get(k))[:16]}"
            )
    return 0 if len(match) == len(keys) else 1


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "--compare":
        return compare(argv[2], argv[3])
    json.dump(fingerprint(), sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
