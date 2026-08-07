"""Round 18 — which factor moves hub scaling, count growth or size spread?

Registered in ``results/PREREG_ROUND18.md``. An intervention, not a family
gate: arms may read n and no admissible generator follows directly. Its
registered use is to decide which factor a later family is built around.

Round 17c left cluster size regularity as the surviving hypothesis. That was
checked before it was built on and is wrong in the direction proposed. The
frozen family's size CV is 0.19 while the capacity family's arms run 0.357 to
0.615, so the capacity family is LESS regular and has the LOWER slope. And
across 17c's arms the CV nearly doubled while the slope stayed flat.

What 17c could not see is that every one of its arms grew, from 78 clusters to
between 105 and 168, while the frozen family is pinned at 78. The difference
between +0.905 and +0.514 may be the PRESENCE of growth rather than its rate,
and a sweep over rates is blind to a threshold by construction.

So this separates the two factors instead of testing them in turn.

    COUNT   FIXED k=78 at every n   ·   GROWING k = 78 -> 102 -> 132
    SIZES   LOW  size CV = 0.19     ·   HIGH    size CV = 0.45

``size_tail`` is calibrated per cell and rung so the achieved CV hits target
exactly. FIXED+LOW is the frozen family and should reproduce +0.905;
GROWING+HIGH approximates the capacity family and should land near +0.514.
Both are controls, checked before any main effect is read.

Main effects are tested by permuting one factor's label while holding the
other fixed. That is a valid test of that main effect and assumes nothing
about the distribution, which matters because the per-seed slopes are the
heavy-tailed quantity that defeated round 17b.

Env: R18_OUT, R18_FROZEN, R18_NS, R18_DIM, R18_SEEDS, R18_RHO, R18_K, R18_PERMS.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    hier_query_corpus,
)
from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.hubness import attractiveness_skew  # noqa: E402

OUT = os.environ.get("R18_OUT", "results/r18_factorial.json")
FROZEN = os.environ.get("R18_FROZEN", "results/r14_frozen_corpus.json")
NS = json.loads(os.environ.get("R18_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R18_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R18_SEEDS", json.dumps(list(range(200, 232)))))
RHO = float(os.environ.get("R18_RHO", "4.0"))
K = int(os.environ.get("R18_K", "10"))
PERMS = int(os.environ.get("R18_PERMS", "20000"))

K0 = 78
GROWTH = 0.38  # the trajectory the capacity family actually followed
CV_LOW, CV_HIGH = 0.19, 0.45
CONTROL_FIXED_LOW = 0.905  # frozen family, measured independently twice
CONTROL_GROWING_HIGH = 0.514  # capacity family, round 17c pooled


def log(m: str) -> None:
    print(m, flush=True)


def _cv(k: int, st: float, nb: int, sd: int = 0) -> float:
    w = np.arange(1, k + 1, dtype=np.float64) ** (-st)
    w /= w.sum()
    c = np.random.default_rng(sd).multinomial(nb, w)
    return float(c.std() / c.mean())


def calibrate(k: int, nb: int, target: float) -> float:
    """size_tail giving the target size CV. Fixed before the run, not tuned."""
    lo, hi = 0.0, 2.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if _cv(k, mid, nb) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def cell_params(count_level: str, size_level: str, n: int) -> tuple[int, float]:
    nb = n - int(round(n * QUERY_FRAC))
    k = K0 if count_level == "FIXED" else int(round(K0 * (n / NS[0]) ** GROWTH))
    st = calibrate(k, nb, CV_LOW if size_level == "LOW" else CV_HIGH)
    return k, st


def slope(xs, ys) -> float:
    x = np.log10(np.asarray(xs, float))
    y = np.asarray(ys, float)
    ok = np.isfinite(y)
    return float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float("nan")


def median_boot(vals, resamples: int = 2000, seed: int = 7):
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    d = rng.choice(v, size=(resamples, len(v)), replace=True)
    return float(np.median(v)), float(np.median(d, axis=1).std(ddof=1))


def main() -> None:
    params0 = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    log("R18 FACTORIAL - count growth vs size spread")
    log(
        f"ladder {NS} at rho={RHO}, dim={DIM}, {len(SEEDS)} seeds "
        f"{SEEDS[0]}..{SEEDS[-1]}"
    )

    cells = [(c, s) for c in ("FIXED", "GROWING") for s in ("LOW", "HIGH")]

    # ---- preconditions, before any outcome -------------------------------
    pre = []
    for c, sz in cells:
        row = []
        for n in NS:
            nb = n - int(round(n * QUERY_FRAC))
            k, st = cell_params(c, sz, n)
            row.append(
                {
                    "n": n,
                    "k": k,
                    "size_tail": round(st, 4),
                    "cv": round(_cv(k, st, nb), 4),
                }
            )
        pre.append({"cell": f"{c}+{sz}", "rungs": row})
        log(
            f"  {c}+{sz:<5} "
            + "  ".join(
                f"n={r['n']}: k={r['k']} st={r['size_tail']:.3f} cv={r['cv']:.3f}"
                for r in row
            )
        )

    per_cell: dict[str, list[float]] = {}
    rows = []
    for c, sz in cells:
        name = f"{c}+{sz}"
        per_seed = []
        for sd in SEEDS:
            vals = []
            for n in NS:
                k, st = cell_params(c, sz, n)
                pr = dict(params0)
                pr["log2_clusters"] = float(np.log2(k))
                pr["size_tail"] = float(st)
                pr.pop("cluster_growth", None)
                nq = max(50, int(round(RHO * n / K)))
                gen_n = int(round((n + nq) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, sd)
                b, q = normalize(x[:n]), normalize(x[n : n + nq])
                _, idx = knn(b, q, K)
                cnt = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
                vals.append(attractiveness_skew(cnt))
            per_seed.append(slope(NS, vals))
        m, se = median_boot(per_seed)
        per_cell[name] = per_seed
        rows.append(
            {
                "cell": name,
                "count": c,
                "sizes": sz,
                "slope": m,
                "sem": se,
                "per_seed": per_seed,
            }
        )
        log(f"  {name:<14} slope={m:+.3f} +/- {se:.3f}")

    # ---- controls --------------------------------------------------------
    fl = next(r for r in rows if r["cell"] == "FIXED+LOW")
    gh = next(r for r in rows if r["cell"] == "GROWING+HIGH")
    c1 = abs(fl["slope"] - CONTROL_FIXED_LOW) <= 3 * max(fl["sem"], 1e-9)
    c2 = abs(gh["slope"] - CONTROL_GROWING_HIGH) <= 3 * max(gh["sem"], 1e-9)
    log(
        f"  control FIXED+LOW {fl['slope']:+.3f} vs {CONTROL_FIXED_LOW:+.3f} "
        f"-> {'ok' if c1 else 'MISS'}"
    )
    log(
        f"  control GROWING+HIGH {gh['slope']:+.3f} vs "
        f"{CONTROL_GROWING_HIGH:+.3f} -> {'ok' if c2 else 'MISS'}"
    )

    # ---- main effects, permuting one factor with the other held ----------
    def effect(factor: str) -> tuple[float, float]:
        if factor == "count":
            groups = [
                ("LOW", "FIXED+LOW", "GROWING+LOW"),
                ("HIGH", "FIXED+HIGH", "GROWING+HIGH"),
            ]
        else:
            groups = [
                ("FIXED", "FIXED+LOW", "FIXED+HIGH"),
                ("GROWING", "GROWING+LOW", "GROWING+HIGH"),
            ]
        obs = float(
            np.mean(
                [np.median(per_cell[a]) - np.median(per_cell[b]) for _, a, b in groups]
            )
        )
        rng = np.random.default_rng(1806)
        ge = 0
        for _ in range(PERMS):
            diffs = []
            for _, a, b in groups:
                pool = np.concatenate([per_cell[a], per_cell[b]])
                pool = rng.permutation(pool)
                na = len(per_cell[a])
                diffs.append(np.median(pool[:na]) - np.median(pool[na:]))
            if abs(float(np.mean(diffs))) >= abs(obs) - 1e-12:
                ge += 1
        return obs, (ge + 1) / (PERMS + 1)

    eff_count, p_count = effect("count")
    eff_size, p_size = effect("sizes")
    inter = float(
        (np.median(per_cell["FIXED+LOW"]) - np.median(per_cell["FIXED+HIGH"]))
        - (np.median(per_cell["GROWING+LOW"]) - np.median(per_cell["GROWING+HIGH"]))
    )
    log(
        f"P-18A count effect  {eff_count:+.3f}  p={p_count:.4f}  "
        f"{'PASS' if (eff_count > 0 and p_count < 0.05) else 'fail'}"
    )
    log(
        f"P-18B size effect   {eff_size:+.3f}  p={p_size:.4f}  "
        f"{'PASS' if p_size < 0.05 else 'fail'}"
    )
    log(f"P-18C interaction   {inter:+.3f}")

    a_pass = bool(eff_count > 0 and p_count < 0.05)
    b_pass = bool(p_size < 0.05)
    if not (c1 and c2):
        verdict = (
            "A control missed, so the run is diagnosed before its main effects "
            "are read. The cells do not reproduce values this family has "
            "already been measured at, and a main effect computed from them "
            "would not be about the factors."
        )
    elif a_pass and not b_pass:
        verdict = (
            f"The registered expectation. Cluster count growth lowers hub "
            f"scaling by {eff_count:+.3f} (p={p_count:.4f}) and size spread "
            f"does not (p={p_size:.4f}). Since round 17c showed the growth "
            f"RATE is inert across 0.22 to 0.55, the effect is the presence of "
            f"growth rather than its rate. The target for an admissible family "
            f"is any scale-blind process whose cluster count grows, which the "
            f"capacity-limited process already is."
        )
    elif b_pass and not a_pass:
        verdict = (
            f"Size spread moves the slope by {eff_size:+.3f} (p={p_size:.4f}) "
            f"and count growth does not. This contradicts round 17c's "
            f"within-family flatness, so a factor inert alongside growth is "
            f"active without it. The size law becomes the target."
        )
    elif a_pass and b_pass:
        verdict = (
            f"Both factors move the slope, count by {eff_count:+.3f} and size "
            f"by {eff_size:+.3f}, with interaction {inter:+.3f}. The mechanism "
            f"is joint and no single-factor family will reproduce real's value "
            f"robustly."
        )
    else:
        verdict = (
            "Neither factor moves the slope with both controls intact. Both "
            "candidates are eliminated, and the gap between the frozen "
            "family's +0.905 and the capacity family's +0.514 lies in "
            "something neither round has parameterised. That is the strongest "
            "argument yet for abandoning this family."
        )
    log(verdict)

    out = {
        "meta": {
            "registered": "results/PREREG_ROUND18.md",
            "status": "INTERVENTION - arms may read n; decides which factor a "
            "later family is built around, admits nothing",
            "ns": NS,
            "dim": DIM,
            "rho": RHO,
            "k": K,
            "seeds": SEEDS,
            "growth_trajectory": GROWTH,
            "cv_low": CV_LOW,
            "cv_high": CV_HIGH,
            "permutations": PERMS,
        },
        "precondition": pre,
        "cells": rows,
        "controls": {
            "fixed_low": {
                "observed": fl["slope"],
                "expected": CONTROL_FIXED_LOW,
                "ok": bool(c1),
            },
            "growing_high": {
                "observed": gh["slope"],
                "expected": CONTROL_GROWING_HIGH,
                "ok": bool(c2),
            },
        },
        "P_18A": {"effect": eff_count, "p": p_count, "pass": a_pass},
        "P_18B": {"effect": eff_size, "p": p_size, "pass": b_pass},
        "P_18C": {"interaction": inter},
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R18_DONE")


if __name__ == "__main__":
    main()
