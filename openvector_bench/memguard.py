# openvector-bench
# MIT License

"""Page-cache discipline for memory-capped workers.

Ported from the turboquant-pro 1T fleet (2026-08-04), where every number
below was measured on NRP pods with cgroup-v2 2Gi limits:

- cgroup-v2 ``memory.current`` charges PAGE CACHE, not just the working set.
  A streaming build whose anonymous memory was 292Mi OOMed with 1526Mi of
  file cache — the spill file it had just written plus freshly written
  output.
- DIRTY cache is the unreclaimable kind. Evicting a 640MB spill only after
  the write loop still let a pod reach memory.peak 1928Mi of 2048Mi
  mid-write; the eviction has to happen per chunk, DURING the write.
- MAPPED file pages resist reclaim even when clean. A linear pass that
  memory-mapped hundreds of files (never returning to any) crept to its
  limit and OOMed; dropping each map as soon as its file was finished fixed
  it. Prefer ``read()`` over ``mmap`` for one-pass streams — read cache
  reclaims, mapped pages effectively do not.

Everything degrades to a no-op where ``posix_fadvise`` is absent (Windows
dev boxes), so call sites need no platform guards.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

_HAS_FADVISE = hasattr(os, "posix_fadvise")


def drop_page_cache(path: str) -> None:
    """Flush and evict ``path``'s page cache (no-op where unsupported).

    fsync first: ``POSIX_FADV_DONTNEED`` silently skips dirty pages, so an
    unsynced file would keep its cache and the call would appear to work.
    Use after writing an artifact that will not be re-read soon (or will be
    re-read memory-mapped in a later phase, which re-pages on demand).
    """
    if not _HAS_FADVISE:
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    finally:
        os.close(fd)


class SpillFile:
    """A write-once, read-once spill whose page cache never accumulates.

    For the draw-order problem banded generators have: values produced early
    are needed late, in order, and materializing them all is exactly the
    footprint a capped worker cannot afford. Chunks are synced and evicted as
    they are written (dirty pages are the OOM driver — see module docstring)
    and evicted again as they are read back, so the resident cost is one
    chunk regardless of spill size.

        with SpillFile(dir=...) as sp:
            for chunk in produce():
                sp.write(chunk_bytes)
            for size in sizes:
                data = sp.read(size)   # bytes, evicted behind the read

    ``write`` after the first ``read`` raises — the file is a queue, not a
    scratch space.
    """

    def __init__(self, dir: str | None = None, suffix: str = ".spill"):
        fd, self.path = tempfile.mkstemp(dir=dir, suffix=suffix)
        os.close(fd)
        self._w = open(self.path, "wb")
        self._r = None

    def write(self, data: bytes) -> None:
        if self._r is not None:
            raise RuntimeError("SpillFile is read-phase; writes are closed")
        pos = self._w.tell()
        self._w.write(data)
        if _HAS_FADVISE:
            self._w.flush()
            os.fsync(self._w.fileno())
            os.posix_fadvise(self._w.fileno(), pos, len(data), os.POSIX_FADV_DONTNEED)

    def read(self, n: int) -> bytes:
        if self._r is None:
            self._w.close()
            self._r = open(self.path, "rb")
        pos = self._r.tell()
        data = self._r.read(n)
        if _HAS_FADVISE:
            os.posix_fadvise(self._r.fileno(), pos, len(data), os.POSIX_FADV_DONTNEED)
        return data

    def close(self) -> None:
        for f in (self._w, self._r):
            try:
                if f is not None:
                    f.close()
            except OSError:
                pass
        try:
            os.remove(self.path)
        except OSError:
            pass

    def __enter__(self) -> SpillFile:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def evicting_reader(path: str, chunk: int = 1 << 24) -> Iterator[bytes]:
    """Yield ``path`` in chunks, evicting each from cache behind the read.

    For one-pass consumption of large staged artifacts inside a capped
    worker: the whole file transits the page cache one chunk at a time.
    """
    with open(path, "rb") as fh:
        while True:
            pos = fh.tell()
            data = fh.read(chunk)
            if not data:
                return
            if _HAS_FADVISE:
                os.posix_fadvise(fh.fileno(), pos, len(data), os.POSIX_FADV_DONTNEED)
            yield data
