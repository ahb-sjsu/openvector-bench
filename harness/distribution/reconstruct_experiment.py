# OpenVector Bench
# Copyright (c) 2026 Andrew H. Bond
# MIT License

"""The reconstruction experiment (spec/DISTRIBUTION.md §6), registered form.

Publish → delete everything but the signed manifest → reconstruct from a
deliberate mixture of regeneration, cache hits, and forced cache misses →
check the four registered pass criteria:

1. every shard verifies against its Merkle root;
2. reconstructed bytes are identical to the originals (independent SHA-256
   of the whole file, not the manifest's own chunk hashes);
3. exact k-NN over the reconstructed corpus returns identical ids for a
   fixed query set (byte-identity makes any index identical; this is the
   end-to-end restatement);
4. the root signature verifies, and a deliberately corrupted chunk is
   detected and rejected.

Run small locally, at T7 for the registered result::

    python harness/distribution/reconstruct_experiment.py \
        --rows 10000000 --dim 128 --rows-per-shard 1000000 \
        --work /archive/ovb_recon [--sign KEYID]

The mixture is forced, not hoped for: reconstruction runs with a generator
registry that deliberately mis-generates odd shards (wrong salt → hash
mismatch → recorded cache miss → mirror fallback), so the event log always
contains regeneration hits, misses, and fetches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from openvector_bench.generators import philox_u8  # noqa: E402
from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.manifest import (  # noqa: E402
    build_manifest,
    load_manifest,
    shard_filename,
    sign_manifest,
    verify_manifest,
    verify_shard_file,
    verify_signature,
    write_manifest,
)
from openvector_bench.reconstruct import reconstruct, summarize  # noqa: E402

IMPL = "refcorpus.philox-u8:v0"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--rows-per-shard", type=int, default=100_000)
    ap.add_argument("--queries", type=int, default=256)
    ap.add_argument("--work", default="ovb_recon_work")
    ap.add_argument("--salt", default="ovb-recon-v0")
    ap.add_argument("--sign", default=None, help="GPG key id; omit to skip")
    ap.add_argument("--out", default="reconstruction_report.json")
    a = ap.parse_args()

    n_shards = -(-a.rows // a.rows_per_shard)
    orig, mirror, recon = (
        os.path.join(a.work, d) for d in ("original", "mirror", "recon")
    )
    for d in (orig, mirror, recon):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)

    # -- publish: materialize, mirror, hash into a manifest, sign ----------- #
    params = {"rows": a.rows_per_shard, "dim": a.dim, "salt": a.salt}
    paths = []
    for i in range(n_shards):
        rows = min(a.rows_per_shard, a.rows - i * a.rows_per_shard)
        data = philox_u8(i, {**params, "rows": rows})
        p = os.path.join(orig, f"shard_{i:05d}.bin")
        with open(p, "wb") as f:
            f.write(data)
        shutil.copy(p, mirror)
        paths.append(p)
    man = build_manifest(
        paths,
        corpus="rc1-recon-exp",
        version="0.1.0",
        metric="cosine",
        dim=a.dim,
        dtype="uint8",
        rows_per_shard=a.rows_per_shard,
        n_rows=a.rows,
        generator={"impl": IMPL, "params": params, "seed_scheme": "shard_index"},
        sources=[
            {
                "kind": "mirror",
                "url": Path(mirror).resolve().as_uri(),
                "role": "cache",
            }
        ],
    )
    man_path = os.path.join(a.work, "manifest.json")
    write_manifest(man, man_path)
    if a.sign:
        sign_manifest(man_path, a.sign)
    original_sha = {i: sha256_file(p) for i, p in enumerate(paths)}
    queries = np.frombuffer(
        philox_u8(10**9, {**params, "rows": a.queries}), dtype=np.uint8
    ).reshape(-1, a.dim)
    # k-NN reference over a bounded shard prefix; identity, not recall, is
    # the test, so the prefix size only bounds cost.
    n_prefix = max(1, min(n_shards, 2_000_000 // a.rows_per_shard))
    base = np.vstack(
        [np.fromfile(p, dtype=np.uint8).reshape(-1, a.dim) for p in paths[:n_prefix]]
    )
    _, ref_ids = knn(normalize(base), normalize(queries), k=10)

    # -- the deletion: retain only the manifest (and the mirror, which plays
    #    the remote cache) ---------------------------------------------------- #
    shutil.rmtree(orig)

    # -- reconstruct from a forced mixture: odd shards mis-regenerate ------- #
    def bad_salt(i: int, p: dict) -> bytes:
        return philox_u8(i, {**p, "salt": p["salt"] + ("-miss" if i % 2 else "")})

    man = load_manifest(man_path)
    verify_manifest(man)
    if a.sign:
        verify_signature(man_path)
    events = reconstruct(man, recon, generators={IMPL: bad_salt})

    # -- registered pass criteria ------------------------------------------- #
    crit: dict[str, bool] = {}
    try:
        for s in man["shards"]:
            verify_shard_file(
                man, s["i"], os.path.join(recon, shard_filename(man, s["i"]))
            )
        crit["1_merkle"] = True
    except ValueError:
        crit["1_merkle"] = False
    crit["2_byte_identity"] = all(
        sha256_file(os.path.join(recon, shard_filename(man, i))) == h
        for i, h in original_sha.items()
    )
    rebase = np.vstack(
        [
            np.fromfile(
                os.path.join(recon, shard_filename(man, i)), dtype=np.uint8
            ).reshape(-1, a.dim)
            for i in range(n_prefix)
        ]
    )
    _, got_ids = knn(normalize(rebase), normalize(queries), k=10)
    crit["3_identical_answers"] = bool(np.array_equal(ref_ids, got_ids))
    tampered = os.path.join(a.work, "tampered.bin")
    shutil.copy(os.path.join(recon, shard_filename(man, 0)), tampered)
    with open(tampered, "r+b") as f:
        f.seek(1000)
        b = f.read(1)
        f.seek(1000)
        f.write(bytes([b[0] ^ 1]))
    try:
        verify_shard_file(man, 0, tampered)
        crit["4_tamper_detected"] = False
    except ValueError:
        crit["4_tamper_detected"] = True
    if a.sign:
        crit["4_signature"] = True  # verify_signature above raised otherwise

    report = {
        "params": vars(a),
        "n_shards": n_shards,
        "criteria": crit,
        "passed": all(crit.values()),
        "events": summarize(events),
    }
    with open(a.out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["criteria"], indent=2))
    print("PASS" if report["passed"] else "FAIL", "-", a.out)


if __name__ == "__main__":
    main()
