"""Manifest, generator, and reconstruction: the DISTRIBUTION.md §2–§3 contract.

Everything here runs offline: the only "mirror" is a ``file://`` URL, which
exercises the same fetch-and-verify path a remote source does.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from openvector_bench.generators import GENERATORS, philox_u8
from openvector_bench.manifest import (
    build_manifest,
    canonical_json,
    load_manifest,
    shard_filename,
    verify_manifest,
    verify_shard_bytes,
    verify_shard_file,
    write_manifest,
)
from openvector_bench.reconstruct import reconstruct, reconstruct_shard, summarize

IMPL = "refcorpus.philox-u8:v0"
PARAMS = {"rows": 1000, "dim": 16, "salt": "test-salt"}


def _publish(tmp_path, n_shards=3, chunk_bytes=4096, with_mirror=True):
    """Materialize shards, mirror them, build the manifest — a tiny Phase 1."""
    orig = tmp_path / "original"
    mirror = tmp_path / "mirror"
    orig.mkdir()
    mirror.mkdir()
    paths = []
    for i in range(n_shards):
        data = philox_u8(i, PARAMS)
        p = orig / f"shard_{i:05d}.bin"
        p.write_bytes(data)
        (mirror / p.name).write_bytes(data)
        paths.append(str(p))
    sources = []
    if with_mirror:
        sources = [{"kind": "mirror", "url": mirror.as_uri(), "role": "cache"}]
    man = build_manifest(
        paths,
        corpus="t-test",
        version="0.0.1",
        metric="cosine",
        dim=PARAMS["dim"],
        dtype="uint8",
        rows_per_shard=PARAMS["rows"],
        n_rows=PARAMS["rows"] * n_shards,
        chunk_bytes=chunk_bytes,
        generator={"impl": IMPL, "params": PARAMS, "seed_scheme": "shard_index"},
        sources=sources,
    )
    return man, orig, mirror


# --------------------------------------------------------------------------- #
# Hash chain and serialization                                                #
# --------------------------------------------------------------------------- #
def test_manifest_roundtrip_and_self_consistency(tmp_path):
    man, orig, _ = _publish(tmp_path)
    verify_manifest(man)
    for s in man["shards"]:
        verify_shard_file(man, s["i"], str(orig / shard_filename(man, s["i"])))
    p = tmp_path / "manifest.json"
    write_manifest(man, str(p))
    reloaded = load_manifest(str(p))
    assert reloaded == man
    assert canonical_json(reloaded) == canonical_json(man)


def test_roots_are_sha256sum_checkable(tmp_path):
    """The spec's interop promise: every root is reproducible with coreutils
    semantics — SHA-256 over the newline-terminated hex list."""
    man, _, _ = _publish(tmp_path)
    s = man["shards"][0]
    text = "".join(c + "\n" for c in s["chunks"])
    assert hashlib.sha256(text.encode()).hexdigest() == s["root"]
    text = "".join(sh["root"] + "\n" for sh in man["shards"])
    assert hashlib.sha256(text.encode()).hexdigest() == man["root"]


def test_tampering_is_detected_and_localized(tmp_path):
    man, orig, _ = _publish(tmp_path, chunk_bytes=1024)
    path = orig / shard_filename(man, 1)
    raw = bytearray(path.read_bytes())
    raw[5000] ^= 1  # one bit, in chunk 4
    path.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="shard 1 chunk 4"):
        verify_shard_file(man, 1, str(path))


def test_truncation_and_extension_are_detected(tmp_path):
    # chunk_bytes divides the shard size exactly (16000 = 16 x 1000), so
    # whole-chunk truncation hits the count check and ragged truncation hits
    # the last chunk's hash — both must reject.
    man, orig, _ = _publish(tmp_path, chunk_bytes=1000)
    path = orig / shard_filename(man, 0)
    data = path.read_bytes()
    path.write_bytes(data[:-1000])
    with pytest.raises(ValueError, match="declares"):
        verify_shard_file(man, 0, str(path))
    path.write_bytes(data[:-512])
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_shard_file(man, 0, str(path))
    path.write_bytes(data + b"\0" * 1000)
    with pytest.raises(ValueError, match="more chunks"):
        verify_shard_file(man, 0, str(path))


def test_params_binding(tmp_path):
    man, _, _ = _publish(tmp_path)
    man["generator"]["params"] = {**PARAMS, "salt": "evil"}
    with pytest.raises(ValueError, match="params"):
        verify_manifest(man)


# --------------------------------------------------------------------------- #
# Generator determinism                                                       #
# --------------------------------------------------------------------------- #
def test_philox_is_deterministic_and_shards_are_distinct():
    a, b = philox_u8(0, PARAMS), philox_u8(0, PARAMS)
    assert a == b and len(a) == PARAMS["rows"] * PARAMS["dim"]
    assert philox_u8(1, PARAMS) != a
    assert philox_u8(0, {**PARAMS, "salt": "other"}) != a
    # Emission is raw counter output, byte-for-byte pinned: freeze one prefix
    # so a silent PRNG or endianness change cannot pass unnoticed.
    # Pinned 2026-07-20 (numpy 2.2.6, x86-64 Linux); Philox raw output is
    # specified by the algorithm, so this must hold on every platform.
    assert philox_u8(0, PARAMS)[:8].hex() == "9cadff00c34b87e8"


# --------------------------------------------------------------------------- #
# Reconstruction with graceful degradation                                    #
# --------------------------------------------------------------------------- #
def test_reconstruct_by_regeneration_alone(tmp_path):
    man, orig, _ = _publish(tmp_path, with_mirror=False)
    originals = {
        s["i"]: (orig / shard_filename(man, s["i"])).read_bytes() for s in man["shards"]
    }
    dest = tmp_path / "recon"
    events = reconstruct(man, str(dest))
    for i, data in originals.items():
        assert (dest / shard_filename(man, i)).read_bytes() == data
    s = summarize(events)
    assert s["regen_hits"] == 3 and s["bytes_moved"] == 0


def test_reconstruct_by_mirror_when_regeneration_disabled(tmp_path):
    man, orig, _ = _publish(tmp_path)
    dest = tmp_path / "recon"
    dest.mkdir()
    events = reconstruct_shard(man, 0, str(dest), generators={})
    assert verify_shard_bytes(man, 0, (dest / shard_filename(man, 0)).read_bytes())
    s = summarize(events)
    assert s["regen_attempts"] == 0 and s["fetch_hits"] == 1
    assert s["bytes_moved"] == PARAMS["rows"] * PARAMS["dim"]


def test_regen_miss_is_a_cache_miss_not_an_error(tmp_path):
    man, _, _ = _publish(tmp_path)

    def wrong(i, p):
        return philox_u8(i, {**p, "salt": "drifted-toolchain"})

    dest = tmp_path / "recon"
    dest.mkdir()
    events = reconstruct_shard(man, 0, str(dest), generators={IMPL: wrong})
    assert [e["method"] for e in events] == ["regenerate", "fetch"]
    assert events[0]["ok"] is False and "cache miss" in events[0]["error"]
    assert events[1]["ok"] is True
    assert verify_shard_bytes(man, 0, (dest / shard_filename(man, 0)).read_bytes())


def test_exhaustion_raises(tmp_path):
    man, _, mirror = _publish(tmp_path)
    for f in mirror.iterdir():
        f.unlink()  # dead mirror

    def wrong(i, p):
        return b"\0"

    with pytest.raises(LookupError, match="no source verified"):
        reconstruct_shard(man, 0, str(tmp_path / "x"), generators={IMPL: wrong})


def test_registry_has_the_reference_impl():
    assert IMPL in GENERATORS


def test_corrupt_mirror_is_rejected_not_written(tmp_path):
    man, _, mirror = _publish(tmp_path)
    bad = bytearray((mirror / shard_filename(man, 0)).read_bytes())
    bad[0] ^= 1
    (mirror / shard_filename(man, 0)).write_bytes(bytes(bad))
    dest = tmp_path / "recon"
    dest.mkdir()
    with pytest.raises(LookupError):
        reconstruct_shard(man, 0, str(dest), generators={})
    assert not (dest / shard_filename(man, 0)).exists()


def test_queries_reshape():
    q = np.frombuffer(philox_u8(7, PARAMS), dtype=np.uint8).reshape(
        PARAMS["rows"], PARAMS["dim"]
    )
    assert q.shape == (1000, 16)
