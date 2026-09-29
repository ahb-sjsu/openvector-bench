# openvector-bench
# MIT License

"""L1 ground truth and difficulty strata for one real tier (FAMILY.md §2-§3).

    python -m harness.tiers.gt_strata --tier-dir /data/ovb/wiki1024-t7 \\
        --data-root /data --dataset ovb-wiki1024-t7

Two sequential passes over the tier's parts (CPU, one exhaustive pass is the
cost the family pays once per tier): exact top-100 cosine for every query,
then the true top-10 rows of each query, which the dispersion stratum needs.
Writes, beside the tier, ``gt_top100.npy`` (int64 tier positions, best first),
``gt_sims.npy``, ``strata.json`` and ``measures.npz``; and, for harnesses that
keep ground truth by dataset name, ``<data-root>/gt/<dataset>.npy`` and
``<data-root>/strata/<dataset>.json``. Memory is one block of scores
(``nq x BLOCK``), sized for a 2 GiB pod at 10,000 queries.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time

import numpy as np

from openvector_bench import tiers as T

BLOCK = 10_000


def _parts(d: str) -> list[np.ndarray]:
    names = sorted(
        p for p in os.listdir(d) if p.startswith("part_") and p.endswith(".npy")
    )
    return [np.load(os.path.join(d, p), mmap_mode="r") for p in names]


def _blocks(parts, block=BLOCK):
    start = 0
    for a in parts:
        for s in range(0, len(a), block):
            yield start + s, np.asarray(a[s : s + block], np.float32)
        start += len(a)


def _rows(parts, positions: np.ndarray, dim: int) -> np.ndarray:
    """Rows at tier ``positions`` (any shape), gathered in one sequential pass."""
    flat = positions.ravel()
    order = np.argsort(flat, kind="stable")
    out = np.empty((len(flat), dim), np.float32)
    offsets = np.cumsum([0] + [len(a) for a in parts])
    for i, a in enumerate(parts):
        lo, hi = np.searchsorted(flat[order], [offsets[i], offsets[i + 1]])
        sel = order[lo:hi]
        if len(sel):
            out[sel] = np.asarray(a[flat[sel] - offsets[i]], np.float32)
    return out.reshape(positions.shape + (dim,))


def run(tier_dir: str, data_root: str | None, dataset: str | None) -> None:
    t0 = time.time()
    parts = _parts(tier_dir)
    n = sum(len(a) for a in parts)
    dim = parts[0].shape[1]
    q = np.load(os.path.join(tier_dir, "queries.npy"))
    gt_path = os.path.join(tier_dir, "gt_top100.npy")
    if os.path.exists(gt_path):
        ids, sims = np.load(gt_path), np.load(os.path.join(tier_dir, "gt_sims.npy"))
    else:
        ids, sims = T.exact_topk(_blocks(parts), q, T.GT_K)
        np.save(os.path.join(tier_dir, "gt_sims.npy"), sims)
        np.save(gt_path + ".tmp.npy", ids)
        os.replace(gt_path + ".tmp.npy", gt_path)
    print(f"gt {ids.shape} in {time.time() - t0:.0f}s", flush=True)
    nb = _rows(parts, ids[:, : T.STRATA_K], dim)
    meas = T.measures(ids, sims, nb, n)
    st = T.strata(meas)
    with open(os.path.join(tier_dir, "manifest.json"), encoding="utf-8") as f:
        man = json.load(f)
    st.update(
        tier=man["tier"],
        row_ids_sha256=man["row_ids_sha256"],
        n_queries=int(len(q)),
        gt_k=T.GT_K,
        strata_k=T.STRATA_K,
        metric="angular (cosine on L2-normalised rows)",
    )
    np.savez_compressed(os.path.join(tier_dir, "measures.npz"), **meas)
    with open(os.path.join(tier_dir, "strata.json"), "w", encoding="utf-8") as f:
        json.dump(st, f)
    if data_root and dataset:
        for sub, src, dst in (
            ("gt", gt_path, f"{dataset}.npy"),
            ("strata", os.path.join(tier_dir, "strata.json"), f"{dataset}.json"),
        ):
            os.makedirs(os.path.join(data_root, sub), exist_ok=True)
            shutil.copyfile(src, os.path.join(data_root, sub, dst))
    print(
        f"strata {sorted(st['strata'])[:4]}... done in {time.time() - t0:.0f}s",
        flush=True,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier-dir", required=True)
    ap.add_argument("--data-root")
    ap.add_argument("--dataset")
    a = ap.parse_args()
    run(a.tier_dir, a.data_root, a.dataset)


if __name__ == "__main__":
    main()
