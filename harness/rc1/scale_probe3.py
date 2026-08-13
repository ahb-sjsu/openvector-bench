"""Does the real G1 ladder reproduce under a properly drawn pool?

`scale_probe.py` loaded the first 110k rows of `wiki1024` and measured real
G1 = 17.5 / 16.9 / 17.4 at n = 25k/50k/100k -- essentially FLAT, against the
registered anchors 26.64 / 22.78 / 19.92 which FALL. Those disagree, and the
disagreement matters: the scale-dependence result was read as explaining the
registered n-drift, and it cannot explain a drift that its own protocol does
not reproduce.

`geometry.py` warns about exactly this failure mode -- Wikipedia arrives
topically ordered, so a head slice is a concentrated, unrepresentative sample.
The registered protocol loads `cap = 3 * max(N_GRID)` rows and draws each rung
uniformly from that pool.

This reproduces the registered draw: a 600k-row pool, each rung sampled
uniformly from it, the full registered ladder including 200k, so all four
anchors can be compared. It reports G1 and the growth profile s(r) together,
so we learn whether the pool changes the ladder, the profile, or both.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

TARGET = os.environ.get("SP_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("SP_OUT", "/home/claude/ovb_scale/scale_probe3.json")
NS = json.loads(os.environ.get("SP_NS", "[25000, 50000, 100000, 200000]"))
NQ = int(os.environ.get("SP_NQ", "10000"))
KMAX = int(os.environ.get("SP_KMAX", "500"))
CAP = int(os.environ.get("SP_CAP", "600000"))
SEED = int(os.environ.get("SP_SEED", "11"))

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})
ANCHORS = {25000: 26.64, 50000: 22.78, 100000: 19.92, 200000: 18.42}


def load_real(path: str, cap: int) -> np.ndarray:
    import glob

    parts = sorted(glob.glob(os.path.join(path, "part_*.npy")))
    out, got = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        take = min(len(a), cap - got)
        out.append(np.asarray(a[:take]))
        got += take
        if got >= cap:
            break
    return np.concatenate(out)


def main() -> int:
    corpus = load_real(TARGET, CAP)
    print(f"pool {corpus.shape}", flush=True)

    # Registered protocol: uniform holdout for queries, uniform draw per rung.
    hrng = np.random.default_rng(7)
    hidx = hrng.choice(len(corpus), size=NQ, replace=False)
    hmask = np.zeros(len(corpus), dtype=bool)
    hmask[hidx] = True
    q = normalize(corpus[hmask])
    base_pool = corpus[~hmask]
    print(f"base pool {base_pool.shape} queries {q.shape}", flush=True)

    out: dict[str, dict] = {}
    for n in NS:
        rng = np.random.default_rng(10_000 + n)
        bi = rng.choice(len(base_pool), size=min(n, len(base_pool)), replace=False)
        base = normalize(base_pool[bi])
        d, _ = knn(base, q, KMAX)
        r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
        s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
        g1 = float(id_twonn(d))
        out[str(n)] = {
            "g1_twonn": g1,
            "anchor": ANCHORS.get(n),
            "k": KGRID,
            "r": r.tolist(),
            "s": s.tolist(),
            "s_lo": float(s[0]),
            "s_hi": float(s[-1]),
            "s_ratio": float(s[-1] / max(s[0], 1e-9)),
        }
        a = ANCHORS.get(n)
        print(
            f"n={n:6d} G1={g1:6.2f} anchor={a}  "
            f"s {s[0]:5.1f} -> {s[-1]:5.1f} (x{out[str(n)]['s_ratio']:.2f})  "
            f"r {r[0]:.3f}..{r[-1]:.3f}",
            flush=True,
        )

    g1s = [out[str(n)]["g1_twonn"] for n in NS]
    exp = float(np.polyfit(np.log(NS), np.log(g1s), 1)[0])
    anch = [ANCHORS[n] for n in NS if n in ANCHORS]
    exp_anchor = float(np.polyfit(np.log([n for n in NS if n in ANCHORS]), np.log(anch), 1)[0])
    print(f"measured G1 exponent {exp:+.3f}   registered anchor exponent {exp_anchor:+.3f}",
          flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"config": {"ns": NS, "nq": NQ, "cap": CAP, "kgrid": KGRID,
                              "seed": SEED},
                   "per_n": out,
                   "g1_exponent": exp, "anchor_exponent": exp_anchor}, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("SCALE_PROBE3_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
