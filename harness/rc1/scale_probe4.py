"""Controls on the 600k pool — is real measurably less scale-free than they are?

`R21B_SCALE_DEPENDENCE.md` established on the corrected pool that real's G1
drift is geometry (curves collapse in radius to 1.9%) and that s(r) ramps from
~15.7 to ~37.8. What it could NOT establish is whether that ramp is larger than
a self-similar or featureless construction produces, because the controls had
only been measured on a discredited 110k head slice.

This runs every corpus through ONE protocol: the registered 600k pool, a single
uniform 10k holdout, uniform per-rung draws, identical k grid and estimator.

Comparability across corpora is the whole point, so the headline statistic is
the scale dependence NORMALIZED by the radius band actually spanned:

    beta = d log s / d log r   =   ln(s_hi/s_lo) / ln(r_hi/r_lo)

Raw ratios are not comparable — each corpus occupies a different, and
differently wide, band of radii on the unit sphere.

Controls:
  null_gaussian  — featureless reference.
  null_lowrank   — the recipe behind the existing 1B/10B synthetic corpora.
  bitmap_L60     — the cascade used as the "flat" reference previously. It is
                   truncated at depth 60 and therefore NOT exactly self-similar,
                   which is why it is a flawed reference and why L90 is added.
  bitmap_L90     — deeper truncation, closer to genuinely scale-free. If beta
                   falls from L60 to L90, the residual slope of the "flat"
                   reference was truncation, and real should be compared to L90.
  strat_as_built — redoes the stratified level on the good pool (its inverted
                   SIGN is already protocol-independent).
"""

from __future__ import annotations

import gc
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.bitmap_gen import BITMAP_PARAMS, bitmap_corpus  # noqa: E402
from openvector_bench.generator_search import (  # noqa: E402
    STRATIFIED_PARAMS,
    decode,
    stratified_corpus,
)
from openvector_bench.geometry import (  # noqa: E402
    id_twonn,
    knn,
    normalize,
    null_gaussian,
    null_lowrank,
    spectrum,
)

TARGET = os.environ.get("SP_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("SP_OUT", "/home/claude/ovb_scale/scale_probe4.json")
NS = json.loads(os.environ.get("SP_NS", "[25000, 50000, 100000, 200000]"))
NQ = int(os.environ.get("SP_NQ", "10000"))
KMAX = int(os.environ.get("SP_KMAX", "500"))
CAP = int(os.environ.get("SP_CAP", "600000"))
SEED = int(os.environ.get("SP_SEED", "11"))
DIM = 1024

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


def bitmap_params(depth: float) -> dict:
    p = dict(zip([s[0] for s in BITMAP_PARAMS], [s[3] for s in BITMAP_PARAMS]))
    p.update(
        log2_branch=1.0,
        scale_decay=1.0,
        noise=0.0,
        m0_frac=0.015,
        depth=depth,
        dim_decay=0.0,
    )
    return p


def main() -> int:
    real = load_real(TARGET, CAP)
    print(f"pool {real.shape}", flush=True)
    eff, _ = spectrum(normalize(real[:50000]))
    rank = max(2, int(round(eff)))
    print(f"effective rank {eff:.1f} -> null_lowrank rank {rank}", flush=True)

    # One holdout mask, reused for every corpus (registered protocol).
    hrng = np.random.default_rng(7)
    hidx = hrng.choice(CAP, size=NQ, replace=False)
    hmask = np.zeros(CAP, dtype=bool)
    hmask[hidx] = True

    def build(name: str) -> np.ndarray:
        if name == "real":
            return real
        if name == "null_gaussian":
            return null_gaussian(real, SEED)
        if name == "null_lowrank":
            return null_lowrank(real, SEED, rank)
        if name.startswith("bitmap_L"):
            return bitmap_corpus(bitmap_params(float(name[8:])), CAP, DIM, SEED)
        if name == "strat_as_built":
            return stratified_corpus(
                decode(np.array([]), STRATIFIED_PARAMS), CAP, DIM, SEED
            )
        raise ValueError(name)

    names = [
        "real",
        "null_gaussian",
        "null_lowrank",
        "bitmap_L60",
        "bitmap_L90",
        "strat_as_built",
    ]
    results: dict[str, dict] = {}

    for name in names:
        x = build(name)
        q = normalize(x[hmask])
        base_pool = x[~hmask]
        per_n = {}
        for n in NS:
            rng = np.random.default_rng(10_000 + n)
            bi = rng.choice(len(base_pool), size=min(n, len(base_pool)), replace=False)
            d, _ = knn(normalize(base_pool[bi]), q, KMAX)
            r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
            s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
            beta = float(np.log(s[-1] / max(s[0], 1e-9)) / np.log(r[-1] / r[0]))
            per_n[str(n)] = {
                "g1_twonn": float(id_twonn(d)),
                "r": r.tolist(),
                "s": s.tolist(),
                "s_lo": float(s[0]),
                "s_hi": float(s[-1]),
                "s_ratio": float(s[-1] / max(s[0], 1e-9)),
                "beta": beta,
            }
            print(
                f"{name:15s} n={n:6d} G1={per_n[str(n)]['g1_twonn']:7.2f} "
                f"s {s[0]:6.1f} -> {s[-1]:6.1f} (x{per_n[str(n)]['s_ratio']:.2f}) "
                f"beta={beta:+7.2f}  r {r[0]:.3f}..{r[-1]:.3f}",
                flush=True,
            )
        # collapse across n on the shared log-r window
        lo = max(np.log(per_n[str(n)]["r"][0]) for n in NS)
        hi = min(np.log(per_n[str(n)]["r"][-1]) for n in NS)
        if hi > lo:
            g = np.linspace(lo, hi, 12)
            M = np.vstack(
                [
                    np.interp(g, np.log(per_n[str(n)]["r"]), per_n[str(n)]["s"])
                    for n in NS
                ]
            )
            coll = float(
                np.mean(np.std(M, 0) / np.maximum(np.abs(np.mean(M, 0)), 1e-9))
            )
        else:
            coll = float("nan")
        results[name] = {
            "per_n": per_n,
            "collapse": coll,
            "beta_mean": float(np.mean([per_n[str(n)]["beta"] for n in NS])),
        }
        print(
            f"  -> {name}: beta_mean {results[name]['beta_mean']:+.2f} "
            f"collapse {coll:.4f}",
            flush=True,
        )
        del x, q, base_pool
        gc.collect()

    rb = results["real"]["beta_mean"]
    print("\n=== normalized scale dependence (beta = dlog s / dlog r) ===", flush=True)
    for name in names:
        b = results[name]["beta_mean"]
        print(
            f"  {name:15s} beta={b:+7.2f}   real/{name} = "
            f"{(rb / b if abs(b) > 1e-9 else float('nan')):+.2f}",
            flush=True,
        )

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "ns": NS,
                    "nq": NQ,
                    "cap": CAP,
                    "kgrid": KGRID,
                    "seed": SEED,
                    "rank": rank,
                    "anchors": ANCHORS,
                },
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("SCALE_PROBE4_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
