# openvector-bench
# MIT License

"""Materialise real tiers (T6, T7) from a source in row order, and their queries.

    python -m harness.tiers.build_real_tiers --source npy:/archive/tqp_real/wiki1024 \\
        --n-source 41000000 --out /data/ovb --name wiki1024 --tiers 6 7
    python -m harness.tiers.build_real_tiers --source hf --n-source 41000000 ...

The source is streamed once, in row order, from either its local ``.npy`` parts
(Atlas) or the Hugging Face parquet files it was downloaded from (NRP), which
give the same row order (``generic_download.py``: parquet files sorted, rows in
file order). Every row's slot is known before the stream starts
(:func:`openvector_bench.tiers.plan`), so each kept row is written straight to
its place with ``pwrite`` into preallocated part files: no memory map, whose
written pages an exempt pod cannot evict (turboquant-pro NRP notes,
2026-09-15), and memory stays one source batch plus the slot map.

Output: ``<out>/<name>-t<k>/part_###.npy`` (1M rows each, permutation order),
``queries.npy`` and ``manifest.json`` per tier. The smaller tier's files are
hard links to the larger tier's first parts, which is the nesting made literal.
Resumable: progress is recorded per finished source file, and a rewrite of a
slot writes the same bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time

import numpy as np

from openvector_bench import tiers as T

PART = 1_000_000
HF_REPO = "CohereLabs/wikipedia-2023-11-embed-multilingual-v3"
HF_CONFIG, HF_COL = "en", "emb"
SYNC_EVERY = 50_000


def _npy_header(path: str, rows: int, dim: int) -> int:
    """Preallocate a float32 ``.npy`` of ``rows x dim``; return the data offset."""
    with open(path, "wb") as f:
        np.lib.format.write_array_header_1_0(
            f, dict(descr="<f4", fortran_order=False, shape=(rows, dim))
        )
        off = f.tell()
        f.truncate(off + rows * dim * 4)
    return off


def stream_npy(d: str, done_files: int):
    parts = sorted(
        p for p in os.listdir(d) if p.startswith("part_") and p.endswith(".npy")
    )
    start = 0
    for i, p in enumerate(parts):
        a = np.load(os.path.join(d, p), mmap_mode="r")
        if i >= done_files:
            for s in range(0, len(a), 100_000):
                yield i, start + s, np.asarray(a[s : s + 100_000], np.float32)
            yield i, None, len(a)  # file finished
        start += len(a)


def stream_hf(done_files: int, file_rows: list):
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download, list_repo_files

    files = sorted(
        f
        for f in list_repo_files(HF_REPO, repo_type="dataset")
        if f.startswith(f"{HF_CONFIG}/") and f.endswith(".parquet")
    )
    start = 0
    for i, fname in enumerate(files):
        if i < done_files:  # finished before a restart: its row count is recorded
            start += file_rows[i]
            continue
        local = hf_hub_download(HF_REPO, fname, repo_type="dataset")
        pf = pq.ParquetFile(local)
        s = start
        for batch in pf.iter_batches(batch_size=20_000, columns=[HF_COL]):
            emb = np.stack(batch.column(0).to_numpy(zero_copy_only=False))
            yield i, s, emb.astype(np.float32)
            s += len(emb)
        yield i, None, s - start
        os.unlink(local)
        start = s


def build(source: str, n_source: int, out: str, name: str, tiers, nq: int) -> None:
    p = T.plan(n_source, tuple(tiers), nq)
    top = max(tiers)
    big = os.path.join(out, f"{name}-t{top}")
    os.makedirs(big, exist_ok=True)
    state_path = os.path.join(big, "BUILD_STATE.json")
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    if state.get("done"):
        print("already built", big, flush=True)
        return
    # slot of every source row: tier position, or -(query index + 2), else -1
    slot = np.full(n_source, -1, np.int64)
    slot[p["rows"]] = np.arange(len(p["rows"]))
    slot[p["queries"]] = -(np.arange(nq) + 2)
    n_rows, nparts = len(p["rows"]), -(-len(p["rows"]) // PART)
    dim = state.get("dim")
    fds, offs = [], []
    queries = None
    qpath = os.path.join(big, "queries.partial.npy")
    done_files = state.get("done_files", 0)
    file_rows = state.get("file_rows", [])
    it = (
        stream_hf(done_files, file_rows)
        if source == "hf"
        else stream_npy(source.split(":", 1)[1], done_files)
    )
    written, t0 = 0, time.time()
    for fi, start, blk in it:
        if start is None:  # a source file finished; blk is its row count
            file_rows = file_rows[:fi] + [int(blk)]
            for fd in fds:
                os.fsync(fd)
            if queries is not None:
                np.save(qpath, queries)
            state.update(done_files=fi + 1, dim=dim, file_rows=file_rows)
            with open(state_path + ".tmp", "w") as f:
                json.dump(state, f)
            os.replace(state_path + ".tmp", state_path)
            print(
                f"source file {fi} done; {written:,} rows written; "
                f"{time.time() - t0:.0f}s",
                flush=True,
            )
            continue
        if not fds:
            dim = blk.shape[1]
            for k in range(nparts):
                path = os.path.join(big, f"part_{k:03d}.npy")
                rows = min(PART, n_rows - k * PART)
                exists = os.path.exists(path) and done_files > 0
                off = (
                    np.load(path, mmap_mode="r").offset
                    if exists
                    else _npy_header(path, rows, dim)
                )
                fds.append(os.open(path, os.O_WRONLY))
                offs.append(off)
            queries = (
                np.load(qpath)
                if os.path.exists(qpath) and done_files > 0
                else np.zeros((nq, dim), np.float32)
            )
        sl = slot[start : start + len(blk)]
        for j in np.flatnonzero(sl >= 0):
            pos = int(sl[j])
            k, r = divmod(pos, PART)
            os.pwrite(fds[k], blk[j].tobytes(), offs[k] + r * dim * 4)
            written += 1
            if written % SYNC_EVERY == 0:
                os.fsync(fds[k])
                os.posix_fadvise(fds[k], 0, 0, os.POSIX_FADV_DONTNEED)
        qj = np.flatnonzero(sl < -1)
        if len(qj):
            queries[-(sl[qj] + 2)] = blk[qj]
    for fd in fds:
        os.fsync(fd)
        os.close(fd)
    if sum(file_rows) != n_source:
        raise SystemExit(
            f"the source streamed {sum(file_rows):,} rows, not --n-source "
            f"{n_source:,}: the slot plan does not describe this source"
        )
    np.save(os.path.join(big, "queries.npy"), queries)
    if os.path.exists(qpath):
        os.unlink(qpath)
    source_rec = dict(
        name=name,
        hf_repo=HF_REPO,
        hf_config=HF_CONFIG,
        column=HF_COL,
        row_order="parquet files sorted, rows in file order",
        read_from=source,
    )
    for t in sorted(tiers):
        d = os.path.join(out, f"{name}-t{t}")
        os.makedirs(d, exist_ok=True)
        files = {}
        rows_t = 10**t
        for k in range(-(-rows_t // PART)):
            f = f"part_{k:03d}.npy"
            src, dst = os.path.join(big, f), os.path.join(d, f)
            if d != big and not os.path.exists(dst):
                keep = min(PART, rows_t - k * PART)
                if keep == PART:  # a whole part: the larger tier's file is this one
                    os.link(src, dst)
                else:  # a tier smaller than a part: its own truncated copy
                    np.save(dst, np.load(src, mmap_mode="r")[:keep])
            files[f] = _payload_sha(dst)
        if d != big and not os.path.exists(os.path.join(d, "queries.npy")):
            os.link(os.path.join(big, "queries.npy"), os.path.join(d, "queries.npy"))
        files["queries.npy"] = _payload_sha(os.path.join(d, "queries.npy"))
        rec = T.manifest_record(p, source_rec, t, files)
        with open(os.path.join(d, "manifest.json"), "w") as f:
            f.write(T.dumps(rec))
        print("tier", d, rec["row_ids_sha256"][:12], flush=True)
    state["done"] = True
    with open(state_path, "w") as f:
        json.dump(state, f)


def _payload_sha(path: str) -> str:
    a = np.load(path, mmap_mode="r")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        f.seek(a.offset)
        while b := f.read(64 << 20):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source", required=True, help="'hf' or 'npy:<dir of part_###.npy>'"
    )
    ap.add_argument("--n-source", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="wiki1024")
    ap.add_argument("--tiers", type=int, nargs="+", default=[6, 7])
    ap.add_argument("--nq", type=int, default=10_000)
    a = ap.parse_args()
    build(a.source, a.n_source, a.out, a.name, a.tiers, a.nq)


if __name__ == "__main__":
    main()
