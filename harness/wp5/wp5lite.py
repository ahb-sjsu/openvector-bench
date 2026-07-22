"""WP5-lite driver: does matched geometry+anatomy transfer to matched ANN behavior?

Registered protocol: results/WP5LITE_PREDICTION.md (written before this driver ran).
Four corpora x {HNSW, IVF-Flat} at FIXED grids; recall-work curves; D = sup-log work
gap over recall in [0.80, 0.99]; P3 tail + hub-rank measurements at the operating
point nearest recall 0.95. Train/validation rows only; the sealed 25% never loaded.

Work measures (declared): IVF = faiss ndis/query (aggregate stats, reset per sweep
point); HNSW = mean per-query latency at num_threads=1 (hnswlib exposes no hop
counts). Same measure for every corpus within a system; cross-system comparison is
out of scope by registration.

Winning knobs embedded verbatim from the repo record:
  RD8 = gen_round8_anatomy.json shards[0] (shard 0, the round-8 warm-start winner)
  RD6 = gen_round6_coloured.json shards[0] (shard 11, the round-6 winner)
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np

t0 = time.time()


def log(m):
    print(f"[{time.time() - t0:7.0f}s] {m}", flush=True)


import faiss  # noqa: E402
import hnswlib  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    hier_coloured_corpus,
    hier_query_corpus,
)
from openvector_bench.geometry import normalize  # noqa: E402

TARGET = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
N_BASE, N_Q, DIM, K = 16000, 1000, 1024, 10
EFS = [10, 16, 24, 32, 48, 64, 96, 128, 192, 256]
NPROBES = [1, 2, 4, 8, 16, 32, 64, 128]
HNSW_SEEDS = [100, 200, 300]
R_LO, R_HI = 0.80, 0.99

RD8 = {"local_dim": 93.69715965226524, "log2_clusters": 6.281211232664926, "n_levels": 2.9624839351579957, "level_decay": 0.3583120511459201, "branch_tail": 1.0814563547833536, "within_scale": 0.5496126709750907, "size_tail": 0.15691675381713233, "noise": 0.04023716392232566, "spectrum_decay": 0.54, "reshape_mix": 0.9563312073493949, "query_tail": 2.3517230297419927, "equalize": 0.217048309017571}  # noqa: E501
RD6 = {"local_dim": 75.16057028759155, "log2_clusters": 10.758928364116365, "n_levels": 4.306002392707525, "level_decay": 0.5063159082799275, "branch_tail": 0.5813727254625963, "within_scale": 0.4731687690337984, "size_tail": 1.3482923049279365, "noise": 0.012747409078290884, "spectrum_decay": 0.41687422159058096, "reshape_mix": 0.7895225155402837}  # noqa: E501


def sealed(i: int) -> bool:
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def load_real_pool():
    parts = sorted(
        p for p in os.listdir(TARGET) if p.startswith("part_") and p.endswith(".npy")
    )
    arr = np.load(os.path.join(TARGET, parts[0]), mmap_mode="r")
    keep = np.fromiter(
        (i for i in range(min(200000, len(arr))) if not sealed(i)), np.int64
    )
    q = normalize(np.asarray(np.load(os.path.join(TARGET, "queries.npy"))[:N_Q], np.float32))
    return arr, keep, q


def corpus_instances():
    """Yield (tag, seed_id, base[N_BASE], queries[N_Q]) for all 12 instances."""
    arr, keep, real_q = load_real_pool()
    for s in range(3):
        rng = np.random.default_rng(1000 + s)
        pick = np.sort(rng.choice(keep, size=N_BASE, replace=False))
        yield "real", s, normalize(np.asarray(arr[pick], np.float32)), real_q
    for s in range(3):
        # n=18000 -> QUERY_FRAC gives 16000 base + 2000 query block; take 1000.
        n_gen = int(round(N_BASE / (1 - QUERY_FRAC)))
        x = hier_query_corpus(RD8, n_gen, DIM, 500 + s)
        yield "rd8", s, x[:N_BASE], x[N_BASE : N_BASE + N_Q]
    for s in range(3):
        # round-6 family has no query block: held-out same-instance rows.
        x = hier_coloured_corpus(RD6, N_BASE + N_Q, DIM, 700 + s)
        yield "rd6", s, x[:N_BASE], x[N_BASE:]
    rng = np.random.default_rng(42)
    ref = normalize(np.asarray(arr[np.sort(rng.choice(keep, 20000, replace=False))], np.float32))
    sd = float(ref.std())
    for s in range(3):
        g = np.random.default_rng(900 + s)
        x = normalize((g.standard_normal((N_BASE + N_Q, DIM)) * sd).astype(np.float32))
        yield "null", s, x[:N_BASE], x[N_BASE:]


def exact_gt(base, q):
    sims = q @ base.T
    idx = np.argpartition(-sims, K, axis=1)[:, :K]
    row = np.take_along_axis(sims, idx, 1)
    order = np.argsort(-row, axis=1)
    return np.take_along_axis(idx, order, 1)


def recall_at_10(retr, gt):
    return float(np.mean([len(set(a) & set(b)) / K for a, b in zip(retr, gt)]))


def run_hnsw(base, q, gt):
    """Curve points (work=mean per-query latency sec, recall) per build seed."""
    curves = []
    for bs in HNSW_SEEDS:
        ix = hnswlib.Index(space="cosine", dim=DIM)
        ix.init_index(max_elements=N_BASE, ef_construction=200, M=16, random_seed=bs)
        ix.set_num_threads(1)
        ix.add_items(base, np.arange(N_BASE))
        pts = []
        for ef in EFS:
            ix.set_ef(max(ef, K))
            t = time.perf_counter()
            labels, _ = ix.knn_query(q, k=K, num_threads=1)
            dt = (time.perf_counter() - t) / len(q)
            pts.append({"knob": ef, "work": dt, "recall": recall_at_10(labels, gt)})
        curves.append(pts)
    return curves


def run_ivf(base, q, gt):
    quant = faiss.IndexFlatIP(DIM)
    ix = faiss.IndexIVFFlat(quant, DIM, 128, faiss.METRIC_INNER_PRODUCT)
    ix.train(base)
    ix.add(base)
    pts = []
    stats = faiss.cvar.indexIVF_stats
    for npb in NPROBES:
        ix.nprobe = npb
        stats.reset()
        _, labels = ix.search(q, K)
        pts.append(
            {"knob": npb, "work": float(stats.ndis) / len(q), "recall": recall_at_10(labels, gt)}
        )
    return [pts]


def log_work_at(curve, r):
    """log(work) at recall r by linear interp in (recall, log work); None if unreachable."""
    pts = sorted(curve, key=lambda p: p["recall"])
    rs = [p["recall"] for p in pts]
    ws = [np.log(max(p["work"], 1e-12)) for p in pts]
    if r > rs[-1] or r < rs[0]:
        return None
    return float(np.interp(r, rs, ws))


def curve_D(c1, c2):
    """sup over registered recall grid of |log w1 - log w2|; None-aware."""
    grid = np.linspace(R_LO, R_HI, 20)
    gaps = []
    for r in grid:
        a, b = log_work_at(c1, r), log_work_at(c2, r)
        if a is not None and b is not None:
            gaps.append(abs(a - b))
    return float(max(gaps)) if gaps else float("nan")


def median_curve(curves):
    """Median work at each knob across build seeds -> one curve."""
    out = []
    for i in range(len(curves[0])):
        out.append(
            {
                "knob": curves[0][i]["knob"],
                "work": float(np.median([c[i]["work"] for c in curves])),
                "recall": float(np.median([c[i]["recall"] for c in curves])),
            }
        )
    return out


def tail_and_hubrank(base, q, gt, curve):
    """P3 measurements at the operating point nearest recall 0.95 (HNSW, seed 100)."""
    pts = sorted(curve, key=lambda p: abs(p["recall"] - 0.95))
    ef = int(pts[0]["knob"])
    ix = hnswlib.Index(space="cosine", dim=DIM)
    ix.init_index(max_elements=N_BASE, ef_construction=200, M=16, random_seed=100)
    ix.set_num_threads(1)
    ix.add_items(base, np.arange(N_BASE))
    ix.set_ef(max(ef, K))
    lat = np.empty(len(q))
    labels = np.empty((len(q), K), dtype=np.int64)
    for i in range(len(q)):
        t = time.perf_counter()
        lab, _ = ix.knn_query(q[i : i + 1], k=K, num_threads=1)
        lat[i] = time.perf_counter() - t
        labels[i] = lab[0]
    n_exact = np.bincount(gt.ravel(), minlength=N_BASE)
    n_appr = np.bincount(labels.ravel(), minlength=N_BASE)
    res = spearmanr(n_exact, n_appr)
    rho = float(getattr(res, "statistic", getattr(res, "correlation", np.nan)))
    return {
        "ef_at_r95": ef,
        "p50_lat": float(np.quantile(lat, 0.50)),
        "p95_lat": float(np.quantile(lat, 0.95)),
        "hubrank_spearman": rho,
    }


def main():
    out = {"protocol": "results/WP5LITE_PREDICTION.md", "curves": {}, "p3": {}}
    for tag, s, base, q in corpus_instances():
        key = f"{tag}_{s}"
        log(f"{key}: exact GT")
        gt = exact_gt(base, q)
        log(f"{key}: HNSW ({len(HNSW_SEEDS)} build seeds x {len(EFS)} ef)")
        h = run_hnsw(base, q, gt)
        log(f"{key}: IVF ({len(NPROBES)} nprobe)")
        v = run_ivf(base, q, gt)
        hm = median_curve(h)
        out["curves"][key] = {"hnsw": h, "hnsw_median": hm, "ivf": v[0]}
        log(f"{key}: P3 tail + hub-rank")
        out["p3"][key] = tail_and_hubrank(base, q, gt, hm)
        with open("wp5lite.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)

    # D matrix vs real mean curve, plus real noise floor, per system
    verdict = {}
    for sysname in ("hnsw_median", "ivf"):
        reals = [out["curves"][f"real_{s}"][sysname] for s in range(3)]
        floor = max(
            curve_D(reals[i], reals[j]) for i in range(3) for j in range(i + 1, 3)
        )
        band = max(2 * floor, np.log(1.5))
        vs = {"noise_floor": floor, "band": float(band), "D": {}}
        for tag in ("rd8", "rd6", "null"):
            ds = []
            for s in range(3):
                cand = out["curves"][f"{tag}_{s}"][sysname]
                ds.append(float(np.median([curve_D(cand, r) for r in reals])))
            vs["D"][tag] = {"per_seed": ds, "median": float(np.median(ds))}
        verdict[sysname] = vs
    out["verdict"] = verdict
    with open("wp5lite.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("wrote wp5lite.json")
    print("WP5LITE_DONE", flush=True)


if __name__ == "__main__":
    main()
