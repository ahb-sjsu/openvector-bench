"""memguard: eviction helpers must be transparent to the data they carry.

The fadvise calls are Linux-only (no-ops elsewhere), so these tests assert
the part that must hold everywhere: bytes in == bytes out, queue semantics
enforced, files cleaned up. The cgroup-level effect is measured in
production, not simulated here (see the module docstring's numbers).
"""

from __future__ import annotations

import os

import pytest

from openvector_bench.memguard import SpillFile, drop_page_cache, evicting_reader


def test_spill_roundtrip_exact(tmp_path):
    chunks = [os.urandom(n) for n in (1, 4096, 65536, 3)]
    with SpillFile(dir=str(tmp_path)) as sp:
        for ch in chunks:
            sp.write(ch)
        for ch in chunks:
            assert sp.read(len(ch)) == ch
        assert sp.read(1) == b""  # exhausted
    assert not os.path.exists(sp.path)  # cleaned up


def test_spill_is_a_queue_not_scratch(tmp_path):
    with SpillFile(dir=str(tmp_path)) as sp:
        sp.write(b"abc")
        assert sp.read(3) == b"abc"
        with pytest.raises(RuntimeError):
            sp.write(b"more")


def test_evicting_reader_streams_whole_file(tmp_path):
    p = tmp_path / "blob"
    data = os.urandom(300_000)
    p.write_bytes(data)
    out = b"".join(evicting_reader(str(p), chunk=65536))
    assert out == data


def test_drop_page_cache_noop_or_works(tmp_path):
    p = tmp_path / "f"
    p.write_bytes(b"x" * 8192)
    drop_page_cache(str(p))  # must not raise on any platform
    assert p.read_bytes() == b"x" * 8192
