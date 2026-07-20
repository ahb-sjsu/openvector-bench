"""Signed Merkle manifests: the corpus as a cryptographically defined object.

Implements ``spec/DISTRIBUTION.md`` §2. The design goal is that every hash in
the chain is checkable with nothing but ``sha256sum``:

* **chunk hash** — SHA-256 of the chunk's raw bytes;
* **shard root** — SHA-256 of the shard's chunk hashes as a newline-terminated
  ASCII-hex list (``printf '%s\\n' $chunks | sha256sum``);
* **corpus root** — the same construction over the shard roots.

The root therefore commits to the data only. Binding the metadata (metric,
dim, generator spec, sources) is the job of the detached signature, which
covers the canonical JSON serialization of the whole manifest — the same
GPG identity that signs the repository's commits.

Partial verification is the point: a worker holding shard *i* verifies shard
*i* against its root and the root list against the corpus root, and never
needs the other 128 TB.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from typing import Iterable, Iterator

CHUNK_BYTES_DEFAULT = 8 * 1024 * 1024
SHARD_FORMAT_DEFAULT = "shard_{i:05d}.bin"


# --------------------------------------------------------------------------- #
# The hash chain                                                              #
# --------------------------------------------------------------------------- #
def _hex_list_root(hexes: Iterable[str]) -> str:
    return hashlib.sha256(("".join(h + "\n" for h in hexes)).encode()).hexdigest()


def chunk_hashes(data: bytes, chunk_bytes: int = CHUNK_BYTES_DEFAULT) -> list[str]:
    return [
        hashlib.sha256(data[o : o + chunk_bytes]).hexdigest()
        for o in range(0, len(data), chunk_bytes)
    ]


def shard_root(chunks: Iterable[str]) -> str:
    return _hex_list_root(chunks)


def corpus_root(shard_roots: Iterable[str]) -> str:
    return _hex_list_root(shard_roots)


def _iter_file_chunks(path: str, chunk_bytes: int) -> Iterator[bytes]:
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_bytes)
            if not chunk:
                return
            yield chunk


def hash_shard_file(
    path: str, chunk_bytes: int = CHUNK_BYTES_DEFAULT
) -> tuple[str, list[str]]:
    """Streaming ``(shard_root, chunk_hashes)`` — peak memory is one chunk."""
    chunks = [
        hashlib.sha256(c).hexdigest() for c in _iter_file_chunks(path, chunk_bytes)
    ]
    return shard_root(chunks), chunks


# --------------------------------------------------------------------------- #
# Building and serializing                                                    #
# --------------------------------------------------------------------------- #
def build_manifest(
    shard_files: list[str],
    *,
    corpus: str,
    version: str,
    metric: str,
    dim: int,
    dtype: str,
    rows_per_shard: int,
    n_rows: int,
    chunk_bytes: int = CHUNK_BYTES_DEFAULT,
    generator: dict | None = None,
    sources: list[dict] | None = None,
) -> dict:
    """Hash materialized shards into a schema-v0 manifest (spec §2).

    ``generator`` and ``sources`` are recorded verbatim; if the generator
    carries an inline ``params`` blob its ``params_sha256`` binding is
    computed here so it cannot drift from the blob.
    """
    shards = []
    for i, path in enumerate(shard_files):
        root, chunks = hash_shard_file(path, chunk_bytes)
        rows = min(rows_per_shard, n_rows - i * rows_per_shard)
        shards.append({"i": i, "rows": rows, "root": root, "chunks": chunks})
    man: dict = {
        "corpus": corpus,
        "version": version,
        "metric": metric,
        "dim": dim,
        "dtype": dtype,
        "n_rows": n_rows,
        "rows_per_shard": rows_per_shard,
        "chunk_bytes": chunk_bytes,
        "hash": "sha256",
        "shards": shards,
        "root": corpus_root(s["root"] for s in shards),
    }
    if generator is not None:
        generator = dict(generator)
        if "params" in generator:
            generator["params_sha256"] = params_sha256(generator["params"])
        man["generator"] = generator
    if sources:
        man["sources"] = sources
    return man


def params_sha256(params: dict) -> str:
    return hashlib.sha256(canonical_json(params).encode()).hexdigest()


def canonical_json(obj: dict) -> str:
    """The byte-stable serialization that signatures cover."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"


def write_manifest(man: dict, path: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(canonical_json(man))
    os.replace(tmp, path)


def load_manifest(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Verification                                                                #
# --------------------------------------------------------------------------- #
def verify_manifest(man: dict) -> None:
    """Internal consistency: declared roots match the declared hash lists.

    Raises ``ValueError`` naming the first inconsistency. This checks the
    manifest against itself; checking *bytes* is ``verify_shard_file``.
    """
    for s in man["shards"]:
        if shard_root(s["chunks"]) != s["root"]:
            raise ValueError(f"shard {s['i']}: root does not match chunk list")
    if corpus_root(s["root"] for s in man["shards"]) != man["root"]:
        raise ValueError("corpus root does not match shard roots")
    gen = man.get("generator")
    if (
        gen
        and "params" in gen
        and params_sha256(gen["params"]) != gen.get("params_sha256")
    ):
        raise ValueError("generator params do not match params_sha256 binding")


def verify_shard_file(man: dict, i: int, path: str) -> None:
    """Verify shard *i*'s bytes chunk-by-chunk, streaming.

    Raises ``ValueError`` naming the first failing chunk — a deliberately
    corrupted chunk must be *detected and rejected*, not averaged away
    (spec §6 pass criterion 4).
    """
    declared = man["shards"][i]["chunks"]
    count = 0
    for idx, chunk in enumerate(_iter_file_chunks(path, man["chunk_bytes"])):
        if idx >= len(declared):
            raise ValueError(f"shard {i}: more chunks than declared ({idx + 1})")
        if hashlib.sha256(chunk).hexdigest() != declared[idx]:
            raise ValueError(f"shard {i} chunk {idx}: hash mismatch")
        count = idx + 1
    if count != len(declared):
        raise ValueError(
            f"shard {i}: {count} chunks, manifest declares {len(declared)}"
        )


def verify_shard_bytes(man: dict, i: int, data: bytes) -> bool:
    return chunk_hashes(data, man["chunk_bytes"]) == man["shards"][i]["chunks"]


def shard_filename(man: dict, i: int) -> str:
    return man.get("shard_format", SHARD_FORMAT_DEFAULT).format(i=i)


# --------------------------------------------------------------------------- #
# Detached signature over the canonical JSON (spec §2 item 3)                 #
# --------------------------------------------------------------------------- #
def sign_manifest(path: str, key: str | None = None) -> str:
    """GPG detached armored signature next to the manifest (``.asc``)."""
    sig = path + ".asc"
    cmd = ["gpg", "--batch", "--yes", "--armor", "--detach-sign", "-o", sig]
    if key:
        cmd += ["--local-user", key]
    subprocess.run(cmd + [path], check=True)
    return sig


def verify_signature(path: str, sig: str | None = None) -> None:
    """Raises ``CalledProcessError`` if the signature does not verify."""
    subprocess.run(
        ["gpg", "--batch", "--verify", sig or path + ".asc", path],
        check=True,
        capture_output=True,
    )
