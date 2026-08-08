"""Round 20 — does one growth exponent satisfy both G1 and hub scaling?

Registered in ``results/PREREG_ROUND20.md``. Read that first.

Two independent gate failures pointed at the same knob. R19b found cluster
count sets G1 as roughly 253 * k**-0.368, implying a growth exponent of 0.482
to reproduce real's falling intrinsic dimension. Round 17c found hub scaling
indistinguishable across exponents 0.22 to 0.55, pooling onto real's value.
0.482 lies inside that range.

So the exponent is FIXED at 0.48 here and the LEVEL is swept, because the
extrapolation that produced 450 clusters runs past its measured range, which
stopped at 256.

The two gates keep their own protocols, because each target was measured under
one and a target only means anything under the protocol that produced it.
G1 runs the battery ladder at 10,000 queries per rung, matching real's budget
exactly, which is the defect that invalidated P-17cG. Hub scaling runs round
17c's ladder at rho 4.0 with 32 seeds and the median.

The decisive part is that both predictions descend from one parameter. A level
passing one and failing the other REFUTES the convergence rather than half
confirming it, and the verdict branches say so.

Env: R20_OUT, R20_FROZEN, R20_ALPHA, R20_LOCALDIM, R20_LEVELS, R20_G1_NS,
R20_HUB_NS, R20_SEEDS, R20_G1_SEEDS, R20_DIM, R20_K, R20_NQ, R20_RHO.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    emergent_cluster_sizes,
    hier_query_corpus,
)
from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402
from openvector_bench.hubness import attractiveness_skew  # noqa: E402

OUT = os.environ.get("R20_OUT", "results/r20_convergence.json")
FROZEN = os.environ.get("R20_FROZEN", "results/r14_frozen_corpus.json")
ALPHA = float(os.environ.get("R20_ALPHA", "0.48"))
LOCALDIM = float(os.environ.get("R20_LOCALDIM", "24"))
LEVELS = json.loads(os.environ.get("R20_LEVELS", "[300, 450, 650]"))
G1_NS = json.loads(os.environ.get("R20_G1_NS", "[25000, 50000, 100000, 200000]"))
HUB_NS = json.loads(os.environ.get("R20_HUB_NS", "[12500, 25000, 50000]"))
SEEDS = json.loads(os.environ.get("R20_SEEDS", json.dumps(list(range(300, 332)))))
G1_SEEDS = json.loads(os.environ.get("R20_G1_SEEDS", "[300, 301, 302]"))
DIM = int(os.environ.get("R20_DIM", "1024"))
K = int(os.environ.get("R20_K", "10"))
NQ = int(os.environ.get("R20_NQ", "10000"))
RHO = float(os.environ.get("R20_RHO", "4.0"))

REAL_G1 = {25000: 26.64, 50000: 22.78, 100000: 19.92, 200000: 18.42}
G1_BAND = (0.85, 1.15)
HUB_TARGET, HUB_TOL = 0.51, 0.15
NREF = 25000


def log(m: str) -> None:
    print(m, flush=True)


def nbase(n: int) -> int:
    return n - int(round(n * QUERY_FRAC))


def calibrate(level: int) -> float:
    """Capacity giving `level` clusters at the reference rung. Fixed pre-run."""
    lo, hi = 1e-9, 1e6
    for _ in range(52):
        mid = math.sqrt(lo * hi)
        k = len(
            emergent_cluster_sizes(
                {"log2_clusters": 6.0, "cluster_capacity": mid},
                ALPHA,
                nbase(NREF),
                np.random.default_rng(0),
            )
        )
        if k > level:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def slope(xs, ys) -> float:
    x, y = np.log10(np.asarray(xs, float)), np.asarray(ys, float)
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
    log("R20 CONVERGENCE - one exponent, two gates")
    log(
        f"alpha={ALPHA} fixed, local_dim={LOCALDIM}, levels {LEVELS}, "
        f"seeds {SEEDS[0]}..{SEEDS[-1]}"
    )

    caps = {lv: calibrate(lv) for lv in LEVELS}

    # ---- preconditions ---------------------------------------------------
    pre = []
    for lv in LEVELS:
        base = {**params0, "local_dim": LOCALDIM, "cluster_capacity": caps[lv]}
        levels, subs = [], []
        for n in G1_NS:
            c = emergent_cluster_sizes(base, ALPHA, nbase(n), np.random.default_rng(0))
            levels.append(int(len(c)))
            subs.append(float(c[c < LOCALDIM].sum() / c.sum()))
        exp = float(np.polyfit(np.log10(G1_NS), np.log10(levels), 1)[0])
        ok_lv = abs(levels[0] - lv) / lv <= 0.10
        ok_ex = abs(exp - ALPHA) <= 0.05
        ok_fl = max(subs) <= 0.15
        pre.append(
            {
                "level": lv,
                "capacity": caps[lv],
                "achieved": levels,
                "exponent": exp,
                "worst_sub_floor": max(subs),
                "level_ok": ok_lv,
                "exponent_ok": ok_ex,
                "floor_ok": ok_fl,
            }
        )
        log(
            f"  level {lv:>4}: achieved {levels} exp={exp:+.3f} "
            f"sub-floor={max(subs):.1%}  "
            f"{'ok' if (ok_lv and ok_ex and ok_fl) else 'FAIL'}"
        )

    if not all(p["level_ok"] and p["exponent_ok"] and p["floor_ok"] for p in pre):
        out = {
            "meta": {"registered": "results/PREREG_ROUND20.md"},
            "precondition": pre,
            "verdict": "Precondition fails. No outcome is read.",
        }
        log(out["verdict"])
        _write(out)
        return

    # ---- P-20G, intrinsic dimension --------------------------------------
    g1_rows = []
    for lv in LEVELS:
        per_n = {}
        for n in G1_NS:
            vals = []
            for sd in G1_SEEDS:
                pr = {
                    **params0,
                    "local_dim": LOCALDIM,
                    "cluster_growth": ALPHA,
                    "cluster_capacity": caps[lv],
                }
                gen_n = int(round((n + NQ) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, sd)
                b, q = normalize(x[:n]), normalize(x[n : n + NQ])
                d, _ = knn(b, q, K)
                vals.append(id_twonn(d))
            g1 = float(np.mean(vals))
            r = g1 / REAL_G1[n]
            per_n[n] = {
                "g1": g1,
                "target": REAL_G1[n],
                "ratio": r,
                "in_band": bool(G1_BAND[0] <= r <= G1_BAND[1]),
            }
        allin = all(v["in_band"] for v in per_n.values())
        g1_rows.append({"level": lv, "per_n": per_n, "all_rungs_in_band": allin})
        log(
            f"  G1 level {lv:>4}  "
            + "  ".join(
                f"n={n}:{v['ratio']:.2f}{'*' if v['in_band'] else ' '}"
                for n, v in per_n.items()
            )
            + f"   all-in-band={allin}"
        )

    # ---- P-20H, hub scaling ----------------------------------------------
    hub_rows = []
    for lv in LEVELS:
        per_seed = []
        for sd in SEEDS:
            vals = []
            for n in HUB_NS:
                pr = {
                    **params0,
                    "local_dim": LOCALDIM,
                    "cluster_growth": ALPHA,
                    "cluster_capacity": caps[lv],
                }
                nq = max(50, int(round(RHO * n / K)))
                gen_n = int(round((n + nq) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, sd)
                b, q = normalize(x[:n]), normalize(x[n : n + nq])
                _, idx = knn(b, q, K)
                cnt = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
                vals.append(attractiveness_skew(cnt))
            per_seed.append(slope(HUB_NS, vals))
        m, se = median_boot(per_seed)
        ok = bool(abs(m - HUB_TARGET) <= HUB_TOL)
        hub_rows.append(
            {"level": lv, "slope": m, "sem": se, "in_tol": ok, "per_seed": per_seed}
        )
        log(
            f"  HUB level {lv:>4}  slope={m:+.3f} +/- {se:.3f}  "
            f"{'ok' if ok else 'out'}"
        )

    g1_pass = {r["level"] for r in g1_rows if r["all_rungs_in_band"]}
    hub_pass = {r["level"] for r in hub_rows if r["in_tol"]}
    both = sorted(g1_pass & hub_pass)

    log(
        f"P-20G passes at {sorted(g1_pass) or 'no level'};  "
        f"P-20H passes at {sorted(hub_pass) or 'no level'};  "
        f"P-20C both at {both or 'NO LEVEL'}"
    )

    if both:
        verdict = (
            f"P-20C holds. Cluster level {both} satisfies both gates from a "
            f"single growth exponent of {ALPHA}. Real's falling intrinsic "
            f"dimension and its hub scaling are two consequences of one "
            f"mechanism, which is the first time this campaign has reached two "
            f"mandatory gates at once. A full battery run on both batteries "
            f"follows, not another diagnostic."
        )
    elif g1_pass and hub_pass:
        verdict = (
            f"The convergence is REFUTED, and refuted in the specific way the "
            f"registration named. G1 passes at {sorted(g1_pass)} and hub "
            f"scaling at {sorted(hub_pass)}, with no level in common. The two "
            f"gates are governed by cluster count in incompatible ways, so the "
            f"family needs a second independent parameter. Each gate being "
            f"individually satisfiable is not progress toward satisfying both."
        )
    elif g1_pass or hub_pass:
        which = "G1" if g1_pass else "hub scaling"
        verdict = (
            f"Only {which} passes anywhere. The convergence fails, and the "
            f"gate that fails everywhere is not reachable by cluster level at "
            f"this exponent."
        )
    else:
        verdict = (
            "Neither gate passes at any level. The G1 extrapolation did not "
            "survive outside its measured range, and this family has been "
            "pursued far enough."
        )
    log(verdict)

    _write(
        {
            "meta": {
                "registered": "results/PREREG_ROUND20.md",
                "alpha": ALPHA,
                "local_dim": LOCALDIM,
                "levels": LEVELS,
                "capacities": caps,
                "g1_ns": G1_NS,
                "hub_ns": HUB_NS,
                "seeds": SEEDS,
                "g1_seeds": G1_SEEDS,
                "dim": DIM,
                "k": K,
                "n_query": NQ,
                "rho": RHO,
                "real_g1": REAL_G1,
                "hub_target": HUB_TARGET,
                "hub_tol": HUB_TOL,
            },
            "precondition": pre,
            "P_20G": {"rows": g1_rows, "passing_levels": sorted(g1_pass)},
            "P_20H": {"rows": hub_rows, "passing_levels": sorted(hub_pass)},
            "P_20C": {"pass": bool(both), "levels": both},
            "verdict": verdict,
        }
    )


def _write(out: dict) -> None:
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R20_DONE")


if __name__ == "__main__":
    main()
