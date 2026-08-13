"""Does the stratified (Whitney) family reproduce real's dimension PROFILE?

**Exploratory, not a registered round.** Train/validation only; the RC-2 seal is
untouched and nothing here is an admission claim.

`R21B_SCALE_DEPENDENCE.md` measured the target as a curve rather than a number:
real's local growth dimension runs s = 9.5 -> 36.4 across k = 4..500 at n = 100k
(3.84x), while every control -- including a self-similar cascade -- is flat to
~1.25x. The indicated structure is a flag of nested subspaces, which is exactly
what `stratified_corpus` builds and what rounds 3-5 recorded as matching G1, G3,
G7 and G8 while failing only G6 hubness.

The sharp question is whether that family reproduces the profile's SHAPE or only
the median G1 that earlier rounds scored. Its defaults (top_dim 88, bottom_dim
38) were calibrated against an older target near ~52-dim; the current measured
spectrum is roughly 10 -> 36, so the flag is swept to bracket it rather than
tested only as built.

Arms are compared to real through an identical protocol: same k grid, same
query count, same estimator, same n.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    STRATIFIED_PARAMS,
    decode,
    stratified_corpus,
)
from openvector_bench.geometry import id_twonn, knn, normalize, spectrum  # noqa: E402

TARGET = os.environ.get("SP_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("SP_OUT", "/home/claude/ovb_scale/scale_probe2.json")
NS = json.loads(os.environ.get("SP_NS", "[25000, 50000, 100000]"))
NQ = int(os.environ.get("SP_NQ", "10000"))
KMAX = int(os.environ.get("SP_KMAX", "500"))
SEED = int(os.environ.get("SP_SEED", "11"))

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})

# (label, top_dim, bottom_dim, n_strata). "as_built" is the shipped default,
# calibrated to the older ~52-dim target; the rest bracket the measured 10->36.
ARMS = [
    ("as_built_88_38", 88.0, 38.0, 4.0),
    ("bracket_38_9", 38.0, 9.0, 4.0),
    ("bracket_38_9_s6", 38.0, 9.0, 6.0),
    ("bracket_50_15", 50.0, 15.0, 4.0),
    ("wide_36_6", 36.0, 6.0, 5.0),
]


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


def curve(base: np.ndarray, q: np.ndarray) -> dict:
    d, _ = knn(base, q, KMAX)
    r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
    lk, lr = np.log(np.array(KGRID, dtype=float)), np.log(r)
    s = np.gradient(lk, lr)
    return {
        "k": KGRID,
        "r": r.tolist(),
        "s": s.tolist(),
        "s_lo": float(s[0]),
        "s_hi": float(s[-1]),
        "s_ratio": float(s[-1] / max(s[0], 1e-9)),
        "g1_twonn": float(id_twonn(d)),
    }


def main() -> int:
    pool = max(NS) + NQ
    real = load_real(TARGET, pool)
    rng = np.random.default_rng(SEED)
    real = real[rng.permutation(len(real))]
    eff, _ = spectrum(normalize(real[:50000]))
    print(f"real {real.shape} effective rank {eff:.1f}", flush=True)

    results: dict[str, dict] = {}

    def measure(name: str, x: np.ndarray) -> None:
        xn = normalize(x)
        q = xn[-NQ:]
        results[name] = {}
        for n in NS:
            c = curve(xn[:n], q)
            results[name][str(n)] = c
            print(
                f"{name:16s} n={n:6d} s {c['s_lo']:6.1f} -> {c['s_hi']:6.1f} "
                f"(x{c['s_ratio']:.2f})  G1={c['g1_twonn']:6.2f}  "
                f"r {c['r'][0]:.3f}..{c['r'][-1]:.3f}",
                flush=True,
            )

    measure("real", real)

    for label, top, bot, nst in ARMS:
        p = decode(np.array([]), STRATIFIED_PARAMS)
        p.update(top_dim=top, bottom_dim=bot, n_strata=nst)
        measure(label, stratified_corpus(p, pool, real.shape[1], SEED))

    # Shape match against real at matched n: RMS log-ratio of s(k) over the grid,
    # which is scale-free in the level and so scores SHAPE, plus the level error.
    real_curves = {n: np.array(results["real"][str(n)]["s"]) for n in NS}
    shape: dict[str, dict] = {}
    for label, *_ in ARMS:
        per_n = {}
        for n in NS:
            cand = np.array(results[label][str(n)]["s"])
            rr = real_curves[n]
            lr_ratio = np.log(np.maximum(cand, 1e-9) / np.maximum(rr, 1e-9))
            per_n[str(n)] = {
                "rms_log_shape": float(np.std(lr_ratio)),  # shape only (level removed)
                "mean_log_level": float(np.mean(lr_ratio)),  # level offset
                "ratio_err": float(
                    results[label][str(n)]["s_ratio"]
                    / max(results["real"][str(n)]["s_ratio"], 1e-9)
                ),
            }
        shape[label] = per_n
        m = per_n[str(NS[-1])]
        print(
            f"SHAPE {label:16s} rms_log(shape)={m['rms_log_shape']:.3f} "
            f"level={m['mean_log_level']:+.2f} ratio_err={m['ratio_err']:.2f}",
            flush=True,
        )

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {"config": {"ns": NS, "nq": NQ, "kmax": KMAX, "kgrid": KGRID, "seed": SEED,
                        "arms": ARMS},
             "results": results, "shape": shape},
            f, indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("SCALE_PROBE2_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
