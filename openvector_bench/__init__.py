"""OpenVector Bench — a nested, content-addressed vector-search benchmark family.

The package ships the measurement harness (geometry battery, manifest
verification); the benchmark data itself is defined by signed manifests and
fetched or regenerated on demand. See ``spec/`` for the registered
specifications.
"""

from .manifest import (
    build_manifest,
    load_manifest,
    sign_manifest,
    verify_manifest,
    verify_shard_file,
    verify_signature,
    write_manifest,
)
from .reconstruct import reconstruct, reconstruct_shard, summarize

__version__ = "0.0.1"

__all__ = [
    "build_manifest",
    "load_manifest",
    "sign_manifest",
    "verify_manifest",
    "verify_shard_file",
    "verify_signature",
    "write_manifest",
    "reconstruct",
    "reconstruct_shard",
    "summarize",
    "__version__",
]
