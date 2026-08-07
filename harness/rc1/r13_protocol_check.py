"""Is the ladder's n-axis confounded by a falling query budget?

The RC-1 count measurements subsample the corpus to each ladder n while
holding the query count fixed at ``geometry.N_QUERY`` (see
``r11v2_stage1.measure_counts``, which draws ``min(N_QUERY, len(q_pool))``
queries regardless of n). Retrieval slots per point are therefore
``N_QUERY * k / n``, which falls by **8x** from n = 25,000 to n = 200,000.

That matters because round 11's central diagnosis was read off exactly this
axis: real holds its count-skew LEVEL while its absolute count maxima FALL
with n (42 -> 9.4 at k10), which was interpreted as real hub mass being a
population law that re-expresses at every sampling scale, and which drove
the round-12 and round-13 architectures. If part of that fall is the query
budget thinning rather than the corpus re-expressing, a generator matched to
it is being matched partly to a protocol artefact.

This measures real under two protocols on the same rows and the same seeds:

  FIXED     queries = N_QUERY at every n            (the current protocol)
  SCALED    queries = N_QUERY * n / n_max at every n (constant slots/point)

and reports the n-drift of S_k and count_max under each. Nothing is scored,
no gate is read, no band is touched. Sealed rows (blake2b(i) % 4 == 3) are
excluded exactly as the reference build excludes them.

If the two protocols agree, the ladder axis is clean and round 11's
diagnosis stands as a corpus property. If they disagree, the amount of
disagreement is the size of the artefact.

Env: R13P_OUT, R13_REAL_DIR, R13P_NS (JSON ladder), R13P_NQ (query budget at
the largest n), R13P_SUBS (draws per cell), R13P_KS.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.geometry import knn, normalize  # noqa: E402

OUT = os.environ.get("R13P_OUT", "results/r13_protocol_check.json")
REAL_DIR = os.environ.get("R13_REAL_DIR", "/archive/tqp_real/wiki1024")
NS = json.loads(os.environ.get("R13P_NS", "[12500, 25000, 50000, 100000]"))
NQ_AT_MAX = int(os.environ.get("R13P_NQ", "2000"))
SUBS = int(os.environ.get("R13P_SUBS", "3"))
KS = json.loads(os.environ.get("R13P_KS", "[10, 30]"))


def log(m: str) -> None:
    print(m, flush=True)


def sealed(i: int) -> bool:
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def load_pool(n_rows: int, rng) -> np.ndarray:
    """Rows sampled ACROSS parts, sealed rows excluded.

    Sampling across parts rather than from the head of part_000 because
    Wikipedia row order is topically clustered; the round-2 admission run
    measured what that does to a query marginal.
    """
    parts = sorted(glob.glob(os.path.join(REAL_DIR, "part_*.npy")))
    per = max(1, n_rows // len(parts))
    out, taken = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        idx = np.sort(rng.choice(len(a), size=min(per * 2, len(a)), replace=False))
        keep = np.array([i for i in idx if not sealed(int(i))], dtype=np.int64)
        if len(keep):
            out.append(np.asarray(a[keep], dtype=np.float32))
            taken += len(keep)
        if taken >= n_rows:
            break
    return np.concatenate(out)[:n_rows]


def count_stats(idx: np.ndarray, n_base: int, k: int) -> dict:
    c = np.bincount(idx[:, :k].ravel(), minlength=n_base).astype(np.float64)
    s = c.std()
    return {
        "s_k": float(((c - c.mean()) ** 3).mean() / max(s**3, 1e-12)),
        "count_max": float(c.max()),
        "count_mean": float(c.mean()),
        "zero_frac": float((c == 0).mean()),
    }


def drift(ns: list[int], vals: list[float]) -> float:
    """Slope per decade of n — the statistic round 11 read off this axis."""
    x = np.log10(np.asarray(ns, dtype=float))
    y = np.asarray(vals, dtype=float)
    ok = np.isfinite(y) & (y > 0)
    if ok.sum() < 2:
        return float("nan")
    return float(np.polyfit(x[ok], np.log10(y[ok]), 1)[0])


def main() -> None:
    log("R13 PROTOCOL CHECK — is the ladder's n-axis confounded by query budget?")
    rng = np.random.default_rng(4242)
    n_max = max(NS)
    pool = load_pool(int(n_max * 1.4), rng)
    log(f"non-sealed pool {pool.shape}")
    # Disjoint query pool, drawn once and shared by both protocols.
    q_pool = pool[n_max:]
    base_pool = pool[:n_max]
    log(f"base pool {base_pool.shape}, query pool {q_pool.shape}")

    rows = []
    for proto in ("FIXED", "SCALED"):
        for n in NS:
            nq = NQ_AT_MAX if proto == "FIXED" else max(50, int(NQ_AT_MAX * n / n_max))
            nq = min(nq, len(q_pool))
            for sub in range(SUBS):
                r = np.random.default_rng(10_000 * sub + n)
                b = normalize(base_pool[r.choice(len(base_pool), n, replace=False)])
                q = normalize(q_pool[r.choice(len(q_pool), nq, replace=False)])
                _, idx = knn(b, q, max(KS))
                for k in KS:
                    rows.append(
                        {
                            "protocol": proto,
                            "n": n,
                            "nq": nq,
                            "sub": sub,
                            "k": k,
                            "slots_per_point": nq * k / n,
                        }
                        | count_stats(idx, n, k)
                    )
            log(
                f"  {proto:6s} n={n:7d} nq={nq:6d} slots/pt={nq * max(KS) / n:.2f} done"
            )

    summary = {}
    for proto in ("FIXED", "SCALED"):
        for k in KS:
            sel = [r for r in rows if r["protocol"] == proto and r["k"] == k]
            by_n = {}
            for n in NS:
                cells = [r for r in sel if r["n"] == n]
                by_n[n] = {
                    "s_k": float(np.mean([c["s_k"] for c in cells])),
                    "count_max": float(np.mean([c["count_max"] for c in cells])),
                    "zero_frac": float(np.mean([c["zero_frac"] for c in cells])),
                }
            summary[f"{proto}_k{k}"] = {
                "by_n": by_n,
                "drift_s_k": drift(NS, [by_n[n]["s_k"] for n in NS]),
                "drift_count_max": drift(NS, [by_n[n]["count_max"] for n in NS]),
            }
            log(
                f"{proto:6s} k={k:3d}: S_k drift/decade="
                f"{summary[f'{proto}_k{k}']['drift_s_k']:+.3f}  "
                f"count_max drift/decade="
                f"{summary[f'{proto}_k{k}']['drift_count_max']:+.3f}  "
                f"cmax {[round(by_n[n]['count_max'], 1) for n in NS]}"
            )

    verdict = {}
    for k in KS:
        f = summary[f"FIXED_k{k}"]
        s = summary[f"SCALED_k{k}"]
        verdict[f"k{k}"] = {
            "count_max_drift_fixed": f["drift_count_max"],
            "count_max_drift_scaled": s["drift_count_max"],
            "count_max_drift_gap": f["drift_count_max"] - s["drift_count_max"],
            "s_k_drift_fixed": f["drift_s_k"],
            "s_k_drift_scaled": s["drift_s_k"],
            "s_k_drift_gap": f["drift_s_k"] - s["drift_s_k"],
        }
    log(json.dumps(verdict, indent=1))

    out = {
        "meta": {
            "question": "does the fixed-query-count protocol confound the "
            "ladder's n-axis, on which round 11's diagnosis was read?",
            "protocols": {
                "FIXED": "nq = N_QUERY at every n (current RC-1 protocol)",
                "SCALED": "nq proportional to n (constant slots per point)",
            },
            "ns": NS,
            "nq_at_max": NQ_AT_MAX,
            "subs": SUBS,
            "ks": KS,
            "sealed_rows": "excluded (blake2b(i) % 4 == 3)",
            "scored": "nothing — no gate, no band, no candidate",
        },
        "rows": rows,
        "summary": summary,
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    log("R13_PROTOCOL_CHECK_DONE")


if __name__ == "__main__":
    main()
