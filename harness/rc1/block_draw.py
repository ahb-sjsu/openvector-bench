"""Is the registered ladder head-specific, or just dense-sampling-specific?

## Why this run exists

`uniform_draw.py` compared the registered pool (600k CONTIGUOUS rows from the
head) against 600k drawn UNIFORMLY from all 41M rows, and found the ladder
gone: G1 flat near 49 instead of falling 26 -> 18, and s_ratio flat near 1.05
instead of rising 1.29 -> 2.37.

That test was **confounded**, which is a flaw in its design and not a result.
It changed two variables at once:

* **position** — head of the corpus vs everywhere;
* **density** — 600k consecutive paragraphs vs 600k rows scattered through 41M
  at 1.5% sampling.

Thin sampling destroys the local structure the profile measures: at 1.5% you
rarely draw two rows from the same tight cluster, so near-duplicate and
same-article neighbours simply are not in the sample. That is
`CAPACITY_CONJECTURE.md` C3 ("sampling and generation do not commute … ladders
thin") appearing in real data, and it means the uniform result cannot be read
as "the target is a head-sampling artifact".

It also matters which object the benchmark is about. A deployed 41M or 10^12
index is DENSE; its local geometry is the dense geometry. A thin uniform sample
of a big corpus is not a small corpus, so preserving density is the right call
and the registered protocol was right to take a contiguous block.

## Design — hold density fixed, vary position only

Draw a **contiguous 600k-row block starting at a random offset** in the 41M,
repeated at several offsets, and run the registered protocol unchanged on each.
Same density as the registered pool, different position.

* **Ladder reproduces at every offset** -> the target is a property of dense
  Wikipedia-like text and the head was an arbitrary but harmless choice. The
  registered anchors stand; only their provenance needs a sentence.
* **Ladder appears only at the head** -> the target really is position-specific
  and the anchors need restating.
* **Ladder varies a lot across offsets** -> the target is a property of local
  topical composition, which would mean the anchors carry a sampling variance
  nobody has quantified — reportable either way.

Env: BD_OFFSETS (list of start rows, or "random"), BD_CAP, BD_NS, BD_NQ.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("BD_THREADS", "4"))

from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

TARGET = os.environ.get("BD_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("BD_OUT", "/home/claude/ovb_scale/block_draw.json")
CAP = int(os.environ.get("BD_CAP", "600000"))
NS = json.loads(os.environ.get("BD_NS", "[25000, 50000, 100000, 200000]"))
NQ = int(os.environ.get("BD_NQ", "10000"))
KMAX = int(os.environ.get("BD_KMAX", "500"))

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})
ANCHORS = {25000: 26.64, 50000: 22.78, 100000: 19.92, 200000: 18.42}


def read_block(parts: list[str], start: int, count: int) -> np.ndarray:
    """Contiguous rows [start, start+count) across part boundaries, via mmap."""
    out, need, pos = [], count, start
    for p in parts:
        a = np.load(p, mmap_mode="r")
        if pos >= len(a):
            pos -= len(a)
            continue
        take = min(need, len(a) - pos)
        out.append(np.asarray(a[pos:pos + take]))
        need -= take
        pos = 0
        if need <= 0:
            break
    return np.concatenate(out)


def ladder(x: np.ndarray) -> dict:
    hrng = np.random.default_rng(7)
    hidx = hrng.choice(len(x), size=NQ, replace=False)
    hmask = np.zeros(len(x), dtype=bool)
    hmask[hidx] = True
    q = normalize(x[hmask])
    base_pool = x[~hmask]
    per_n, g1s, ratios = {}, [], []
    for n in NS:
        rng = np.random.default_rng(10_000 + n)
        bi = rng.choice(len(base_pool), size=min(n, len(base_pool)), replace=False)
        d, _ = knn(normalize(base_pool[bi]), q, KMAX)
        r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
        s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
        g1 = float(id_twonn(d))
        ratio = float(s[-1] / max(s[0], 1e-9))
        per_n[str(n)] = {"g1": g1, "s_lo": float(s[0]), "s_hi": float(s[-1]),
                         "s_ratio": ratio, "r_lo": float(r[0]), "r_hi": float(r[-1])}
        g1s.append(g1)
        ratios.append(ratio)
        print(f"    n={n:6d} G1={g1:6.2f} (anchor {ANCHORS.get(n)})  "
              f"s {s[0]:5.1f}->{s[-1]:5.1f} ratio {ratio:.2f}", flush=True)
    ln = np.log(NS)
    return {"per_n": per_n,
            "g1_exponent": float(np.polyfit(ln, np.log(g1s), 1)[0]),
            "s_ratio_trend": float(np.polyfit(ln, ratios, 1)[0])}


def main() -> int:
    parts = sorted(glob.glob(os.path.join(TARGET, "part_*.npy")))
    total = sum(len(np.load(p, mmap_mode="r")) for p in parts)
    print(f"{len(parts)} parts, {total} rows", flush=True)

    spec = os.environ.get("BD_OFFSETS", "random")
    if spec == "random":
        rng = np.random.default_rng(2026)
        offsets = [0] + sorted(int(v) for v in
                               rng.choice(total - CAP, size=3, replace=False))
    else:
        offsets = json.loads(spec)

    results = {}
    for off in offsets:
        tag = "head" if off == 0 else f"offset_{off}"
        print(f"\n[{tag}] rows {off}..{off + CAP}", flush=True)
        x = read_block(parts, off, CAP)
        results[tag] = ladder(x)
        results[tag]["offset"] = int(off)
        print(f"  -> {tag}: G1 exponent {results[tag]['g1_exponent']:+.3f}, "
              f"s_ratio trend {results[tag]['s_ratio_trend']:+.3f}", flush=True)
        del x

    print("\n=== ladder across positions (density held fixed) ===", flush=True)
    print(f"{'block':16s} {'G1 exp':>8s} {'ratio trend':>12s}", flush=True)
    for k, v in results.items():
        print(f"{k:16s} {v['g1_exponent']:+8.3f} {v['s_ratio_trend']:+12.3f}",
              flush=True)
    print("registered head pool: G1 exp -0.168, ratio trend +0.511", flush=True)
    print("uniform 1.5% draw:    G1 exp ~-0.02, ratio trend ~0.00", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"config": {"cap": CAP, "ns": NS, "nq": NQ, "kmax": KMAX,
                              "offsets": offsets, "total_rows": int(total)},
                   "results": results}, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("BLOCK_DRAW_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
