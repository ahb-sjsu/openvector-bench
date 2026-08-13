"""Does the registered G1 ladder survive a UNIFORM draw from the whole corpus?

This is the experiment that decides whether the generator problem is well-posed.

## The problem

`R23_F2_TRANSFER.md` recorded that the profile is protocol-dependent. Same
corpus, same estimator:

| pool | G1 @25k | G1 exponent | s_ratio @25k |
|---|---|---|---|
| 600k CONTIGUOUS head rows (registered) | 25.97 | **-0.168** | 1.29 |
| 60k spread, 600 rows from each of ~100 blobs | 16.14 | **+0.006** | 3.34 |

`geometry.py:load_target` reads `part_*.npy` in order until `cap` rows, so the
registered pool is the contiguous **head** of a corpus that arrives in
Wikipedia's own topical order. `geometry.py` already warns about exactly this
hazard — but only for the query holdout, not for the pool itself.

If the falling ladder is an artifact of sampling the head, then R19 and R20
spent three rounds chasing an artifact and six family exclusions were measured
against a target that is not the corpus's geometry. That has to be settled
before anything is pre-registered, published, or searched against.

## Design

Draw uniformly across **all 41 parts** (41M rows) rather than the head: an
equal quota from each part at random offsets, via mmap so no part is fully
read. Then run the registered protocol unchanged — uniform 10k holdout,
uniform per-rung draws, k grid 4..500, rungs 25k/50k/100k/200k — so the ONLY
difference from `scale_probe3.py` is which rows enter the pool.

## Registered reading, before the run

* **Ladder survives** (G1 exponent near -0.17, s_ratio near 1.3 rising): the
  target is a property of the corpus, the registered anchors stand, and the
  campaign's premise is sound.
* **Ladder vanishes** (exponent near 0): the registered target is an artifact
  of head-sampling. The anchors, and every family exclusion measured against
  them, would need restating — and the right target becomes whatever a uniform
  draw shows.
* **Something between**: report it as such; do not round toward either story.

Env: UD_CAP, UD_NS, UD_NQ, UD_KMAX, UD_OUT, UD_TARGET.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("UD_THREADS", "4"))

from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

TARGET = os.environ.get("UD_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("UD_OUT", "/home/claude/ovb_scale/uniform_draw.json")
CAP = int(os.environ.get("UD_CAP", "600000"))
NS = json.loads(os.environ.get("UD_NS", "[25000, 50000, 100000, 200000]"))
NQ = int(os.environ.get("UD_NQ", "10000"))
KMAX = int(os.environ.get("UD_KMAX", "500"))
SEED = 11

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})
ANCHORS = {25000: 26.64, 50000: 22.78, 100000: 19.92, 200000: 18.42}
CONTIGUOUS = {25000: 25.97, 50000: 22.84, 100000: 20.40, 200000: 18.28}


def load_uniform(path: str, cap: int) -> np.ndarray:
    """Equal quota from every part, at random offsets, via mmap."""
    parts = sorted(glob.glob(os.path.join(path, "part_*.npy")))
    if not parts:
        raise SystemExit(f"no parts under {path}")
    per = cap // len(parts) + 1
    rng = np.random.default_rng(SEED)
    out = []
    got = 0
    for i, p in enumerate(parts):
        a = np.load(p, mmap_mode="r")
        take = min(per, len(a), cap - got)
        if take <= 0:
            break
        idx = np.sort(rng.choice(len(a), size=take, replace=False))
        out.append(np.asarray(a[idx]))
        got += take
        if i % 10 == 0:
            print(f"  part {i+1}/{len(parts)}: {got} rows", flush=True)
    x = np.concatenate(out)
    print(f"uniform pool {x.shape} from {len(parts)} parts", flush=True)
    return x


def main() -> int:
    corpus = load_uniform(TARGET, CAP)

    hrng = np.random.default_rng(7)
    hidx = hrng.choice(len(corpus), size=NQ, replace=False)
    hmask = np.zeros(len(corpus), dtype=bool)
    hmask[hidx] = True
    q = normalize(corpus[hmask])
    base_pool = corpus[~hmask]
    print(f"base {base_pool.shape} queries {q.shape}", flush=True)

    per_n, g1s, ratios = {}, [], []
    for n in NS:
        rng = np.random.default_rng(10_000 + n)
        bi = rng.choice(len(base_pool), size=min(n, len(base_pool)), replace=False)
        d, _ = knn(normalize(base_pool[bi]), q, KMAX)
        r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
        s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
        g1 = float(id_twonn(d))
        ratio = float(s[-1] / max(s[0], 1e-9))
        per_n[str(n)] = {
            "g1": g1,
            "s_lo": float(s[0]),
            "s_hi": float(s[-1]),
            "s_ratio": ratio,
            "r_lo": float(r[0]),
            "r_hi": float(r[-1]),
            "r": r.tolist(),
            "s": s.tolist(),
            "anchor": ANCHORS.get(n),
            "contiguous": CONTIGUOUS.get(n),
        }
        g1s.append(g1)
        ratios.append(ratio)
        print(
            f"n={n:6d} G1={g1:6.2f} (anchor {ANCHORS.get(n)}, contiguous "
            f"{CONTIGUOUS.get(n)})  s {s[0]:5.1f}->{s[-1]:5.1f} ratio {ratio:.2f} "
            f"r [{r[0]:.3f},{r[-1]:.3f}]",
            flush=True,
        )

    ln = np.log(NS)
    g1_exp = float(np.polyfit(ln, np.log(g1s), 1)[0])
    ratio_trend = float(np.polyfit(ln, ratios, 1)[0])
    anchor_exp = float(
        np.polyfit(
            np.log([n for n in NS if n in ANCHORS]),
            np.log([ANCHORS[n] for n in NS if n in ANCHORS]),
            1,
        )[0]
    )
    verdict = (
        "LADDER SURVIVES"
        if g1_exp < -0.10
        else "LADDER VANISHES" if g1_exp > -0.04 else "INTERMEDIATE"
    )
    print(
        f"\nG1 exponent {g1_exp:+.3f}  (registered anchors {anchor_exp:+.3f}, "
        f"contiguous pool -0.168)",
        flush=True,
    )
    print(f"s_ratio trend {ratio_trend:+.3f}  (contiguous pool +0.511)", flush=True)
    print(f"VERDICT: {verdict}", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "cap": CAP,
                    "ns": NS,
                    "nq": NQ,
                    "kmax": KMAX,
                    "kgrid": KGRID,
                    "seed": SEED,
                    "draw": "uniform-all-parts",
                },
                "per_n": per_n,
                "g1_exponent": g1_exp,
                "s_ratio_trend": ratio_trend,
                "anchor_exponent": anchor_exp,
                "verdict": verdict,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("UNIFORM_DRAW_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
