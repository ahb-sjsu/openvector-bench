"""Round 17b gate — emergent cluster growth at matched level.

Registered in ``results/PREREG_ROUND17B.md``. Read that first; the predictions
and the closure rule live there and are not restated here.

The family is a capacity-limited growth process over cluster membership. Each
row joins a uniformly chosen cluster unless that cluster is at capacity
``c * K**beta``, in which case it starts a new one. The count follows
``n ~ c * K**(1+beta)``, so ``alpha = 1/(1+beta)`` sets the growth exponent and
``c`` sets the level independently. ``c`` is a family constant calibrated
before the run and read from the calibration record.

Round 17 compared a family with 13 clusters against one with 816 and read the
slopes anyway. So this gate checks the preconditions first and refuses to look
at any outcome if they fail. The check costs seconds and needs no corpus.

Env: R17B_OUT, R17B_FROZEN, R17B_CALIB, R17B_NS, R17B_DIM, R17B_SEEDS,
R17B_RHO, R17B_K, R17B_LEVEL_TOL, R17B_FLOOR_TOL.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    emergent_cluster_sizes,
    hier_query_corpus,
)
from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.hubness import attractiveness_skew  # noqa: E402

OUT = os.environ.get("R17B_OUT", "results/r17b_gate.json")
FROZEN = os.environ.get("R17B_FROZEN", "results/r14_frozen_corpus.json")
CALIB = os.environ.get("R17B_CALIB", "results/r17b_calibration.json")
NS = json.loads(os.environ.get("R17B_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R17B_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R17B_SEEDS", "[0,1,2,3,4,5,6,7,8,9,10,11]"))
RHO = float(os.environ.get("R17B_RHO", "4.0"))
K = int(os.environ.get("R17B_K", "10"))
LEVEL_TOL = float(os.environ.get("R17B_LEVEL_TOL", "0.10"))
FLOOR_TOL = float(os.environ.get("R17B_FLOOR_TOL", "0.15"))
TARGET, TOL = 0.51, 0.15


def log(m: str) -> None:
    print(m, flush=True)


def slope(xs, ys) -> float:
    x = np.log10(np.asarray(xs, float))
    y = np.asarray(ys, float)
    ok = np.isfinite(y)
    return float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float("nan")


def main() -> None:
    params0 = dict(json.load(open(FROZEN, encoding="utf-8"))["params"])
    calib = json.load(open(CALIB, encoding="utf-8"))
    d_local = int(calib["d_local"])
    arms = calib["arms"]

    log("R17b GATE - emergent cluster growth at matched level")
    log(
        f"ladder {NS} at rho={RHO}, dim={DIM}, {len(SEEDS)} seeds, target "
        f"{TARGET:+.2f}+/-{TOL:.2f}"
    )

    # ---- preconditions, before any outcome ------------------------------
    pre = []
    for arm in arms:
        lv, sub = [], []
        for n in NS:
            nb = n - int(round(n * QUERY_FRAC))
            c = emergent_cluster_sizes(
                {**params0, "cluster_capacity": arm["capacity"]},
                arm["growth"],
                nb,
                np.random.default_rng(0),
            )
            lv.append(int(len(c)))
            sub.append(float(c[c < d_local].sum() / c.sum()))
        pre.append(
            {
                "growth": arm["growth"],
                "levels": lv,
                "sub_floor_share": round(max(sub), 4),
            }
        )
        log(
            f"  precondition alpha={arm['growth']:.2f} levels={lv} "
            f"below-floor={max(sub):.1%}"
        )

    ref = [q["levels"][0] for q in pre]
    spread = (max(ref) - min(ref)) / max(float(np.mean(ref)), 1e-9)
    worst = max(q["sub_floor_share"] for q in pre)
    lvl_ok, flr_ok = bool(spread <= LEVEL_TOL), bool(worst <= FLOOR_TOL)
    log(
        f"  reference-rung spread {spread:.2%} (limit {LEVEL_TOL:.0%}) -> "
        f"{'ok' if lvl_ok else 'FAIL'};  worst below-floor {worst:.1%} "
        f"(limit {FLOOR_TOL:.0%}) -> {'ok' if flr_ok else 'FAIL'}"
    )

    out: dict = {
        "meta": {
            "registered": "results/PREREG_ROUND17B.md",
            "ns": NS,
            "dim": DIM,
            "rho": RHO,
            "k": K,
            "seeds": SEEDS,
            "target": TARGET,
            "tolerance": TOL,
            "statistic": "attractiveness_skew",
        },
        "precondition": {
            "arms": pre,
            "reference_level_spread": spread,
            "worst_sub_floor_share": worst,
            "level_ok": lvl_ok,
            "floor_ok": flr_ok,
        },
    }

    if not (lvl_ok and flr_ok):
        out["verdict"] = (
            "Precondition fails. No outcome is read, because a slope compared "
            "across arms that differ in more than the swept parameter is not a "
            "measurement of that parameter."
        )
        log(out["verdict"])
        _write(out)
        return

    # ---- P-17bM and P-17bO ----------------------------------------------
    rows = []
    for arm in arms:
        a, cap = float(arm["growth"]), float(arm["capacity"])
        per_seed, exps = [], []
        for sd in SEEDS:
            vals, ks = [], []
            for n in NS:
                pr = {**params0, "cluster_growth": a, "cluster_capacity": cap}
                nb = n - int(round(n * QUERY_FRAC))
                ks.append(
                    len(emergent_cluster_sizes(pr, a, nb, np.random.default_rng(sd)))
                )
                nq = max(50, int(round(RHO * n / K)))
                gen_n = int(round((n + nq) / (1.0 - QUERY_FRAC)))
                x = hier_query_corpus(pr, gen_n, DIM, sd)
                b, q = normalize(x[:n]), normalize(x[n : n + nq])
                _, idx = knn(b, q, K)
                cnt = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
                vals.append(attractiveness_skew(cnt))
            per_seed.append(slope(NS, vals))
            exps.append(slope(NS, np.log10(ks)))
        m = float(np.nanmean(per_seed))
        sem = float(np.nanstd(per_seed, ddof=1) / np.sqrt(len(per_seed)))
        me = float(np.nanmean(exps))
        rows.append(
            {
                "growth": a,
                "capacity": cap,
                "slope": m,
                "sem": sem,
                "measured_exponent": me,
                "mechanism_ok": bool(abs(me - a) <= 0.05),
                "per_seed": per_seed,
            }
        )
        log(
            f"  alpha={a:.2f} measured={me:+.3f} "
            f"{'ok' if abs(me - a) <= 0.05 else 'MISMATCH'}  "
            f"slope={m:+.3f} +/- {sem:.3f}"
        )

    mech = all(r["mechanism_ok"] for r in rows)
    sl = [r["slope"] for r in rows]
    monotone = all(sl[i] >= sl[i + 1] for i in range(len(sl) - 1))
    best = min(rows, key=lambda r: abs(r["slope"] - TARGET))
    hit = bool(abs(best["slope"] - TARGET) <= TOL)

    out["arms"] = rows
    out["P_17bM"] = {"pass": mech}
    out["P_17bO"] = {
        "pass": bool(monotone and hit),
        "monotone": monotone,
        "best_growth": best["growth"],
        "best_slope": best["slope"],
        "predicted_winner": 0.38,
    }
    log(
        f"P-17bM {'PASS' if mech else 'FAIL'};  P-17bO "
        f"{'PASS' if (monotone and hit) else 'FAIL'} "
        f"(monotone={monotone}, best alpha={best['growth']:.2f} at "
        f"{best['slope']:+.3f})"
    )

    if mech and monotone and hit:
        out["verdict"] = (
            f"The family reaches real corpora's hub scaling at growth exponent "
            f"{best['growth']:.2f}, measured {best['slope']:+.3f} +/- "
            f"{best['sem']:.3f}. The registration predicted 0.38. P-17bG and "
            f"the seed-disjoint confirmation follow before anything is claimed."
        )
    elif not mech:
        out["verdict"] = (
            "The process did not deliver the growth it promised, so the "
            "outcome is uninterpretable and the family is closed unmeasured."
        )
    else:
        out["verdict"] = (
            "P-17bO fails with preconditions holding, so this is the family "
            "and not the experiment. The family is closed as registered."
        )
    log(out["verdict"])
    _write(out)


def _write(out: dict) -> None:
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R17B_GATE_DONE")


if __name__ == "__main__":
    main()
