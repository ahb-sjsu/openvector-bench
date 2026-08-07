"""Round 17c gate — the same family, powered.

Registered in ``results/PREREG_ROUND17C.md``. Read that first; the predictions
and the closure rule live there and are not restated here.

The family is a capacity-limited growth process over cluster membership. Each
row joins a uniformly chosen cluster unless that cluster is at capacity
``c * K**beta``, in which case it starts a new one. The count follows
``n ~ c * K**(1+beta)``, so ``alpha = 1/(1+beta)`` sets the growth exponent and
``c`` sets the level independently. ``c`` is a family constant calibrated
before the run and read from the calibration record.

Round 17b showed this family is mechanically sound and could not measure its
outcome, because 12 seeds gave a worst-case power of 0.72 against the effect
it needed to resolve. This is the same family under the registered estimator
rule in ``spec/ESTIMATOR.md``: the median of per-seed slopes, its bootstrap
standard error, 32 seeds, and no outlier discarded.

The seeds are disjoint from round 17b's, because 17b's medians were seen
before the estimator was chosen and no result may rest on those draws.

Three outcomes are registered rather than one. A monotone decline crossing
target confirms the intervention's mechanism. A flat sweep with every arm on
target means the growth exponent is not the lever and cluster size regularity
is doing the work. Neither closes the family.

Env: R17C_OUT, R17C_FROZEN, R17C_CALIB, R17C_NS, R17C_DIM, R17C_SEEDS,
R17C_RHO, R17C_K, R17C_LEVEL_TOL, R17C_FLOOR_TOL.
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

OUT = os.environ.get("R17C_OUT", "results/r17c_gate.json")
FROZEN = os.environ.get("R17C_FROZEN", "results/r14_frozen_corpus.json")
CALIB = os.environ.get("R17C_CALIB", "results/r17b_calibration.json")
NS = json.loads(os.environ.get("R17C_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R17C_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R17C_SEEDS", json.dumps(list(range(100, 132)))))
RHO = float(os.environ.get("R17C_RHO", "4.0"))
K = int(os.environ.get("R17C_K", "10"))
LEVEL_TOL = float(os.environ.get("R17C_LEVEL_TOL", "0.10"))
FLOOR_TOL = float(os.environ.get("R17C_FLOOR_TOL", "0.15"))
TARGET, TOL = 0.51, 0.15


def log(m: str) -> None:
    print(m, flush=True)


def median_boot(vals, resamples: int = 2000, seed: int = 7):
    """Median and its bootstrap standard error, per ``spec/ESTIMATOR.md``.

    The mean does not converge under contamination here: at a 4 percent
    contamination rate its power moves only from 0.66 to 0.74 between 12 and
    64 seeds, while the median moves from 0.75 to 0.94. So the summary is the
    median and its uncertainty is bootstrapped rather than assumed normal.
    """
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.choice(v, size=(resamples, len(v)), replace=True)
    return float(np.median(v)), float(np.median(draws, axis=1).std(ddof=1))


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

    log("R17c GATE - emergent cluster growth at matched level")
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
            "registered": "results/PREREG_ROUND17C.md",
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

    # ---- P-17cM and P-17cO ----------------------------------------------
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
        m, sem = median_boot(per_seed)
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
    all_on_target = bool(all(abs(v - TARGET) <= TOL for v in sl))
    spread = float(max(sl) - min(sl))
    # A sweep that varies by less than the tolerance it is judged against
    # supports no ordering claim in either direction.
    flat = bool(spread <= TOL)
    outcome = "A" if (monotone and hit) else ("B" if (flat and all_on_target) else "C")

    out["arms"] = rows
    out["P_17cM"] = {"pass": mech}
    out["P_17cO"] = {
        "outcome": outcome,
        "pass": outcome in ("A", "B"),
        "monotone": monotone,
        "flat": flat,
        "slope_spread": spread,
        "all_on_target": all_on_target,
        "best_growth": best["growth"],
        "best_slope": best["slope"],
        "predicted_winner_A": 0.38,
    }
    log(
        f"P-17cM {'PASS' if mech else 'FAIL'};  P-17cO outcome {outcome} "
        f"(monotone={monotone}, flat={flat}, spread={spread:.3f}, "
        f"all_on_target={all_on_target}, best alpha={best['growth']:.2f} at "
        f"{best['slope']:+.3f})"
    )

    if mech and outcome == "A":
        out["verdict"] = (
            f"P-17cO-A. The slope falls monotonically with the growth exponent "
            f"and reaches real corpora's hub scaling at {best['growth']:.2f}, "
            f"measured {best['slope']:+.3f} +/- {best['sem']:.3f}. The "
            f"intervention's mechanism is confirmed, so cluster-count growth "
            f"is the operative variable. P-17cG and the seed-disjoint "
            f"confirmation follow before anything is claimed."
        )
    elif mech and outcome == "B":
        out["verdict"] = (
            f"P-17cO-B. The sweep is flat, varying by {spread:.3f} across the "
            f"whole range, and every arm sits within tolerance of real "
            f"corpora's {TARGET:+.2f}. The family reaches real's hub scaling "
            f"but the growth exponent is not the lever. The capacity process "
            f"also bounds cluster sizes to a common capacity instead of "
            f"letting a multinomial spread them, and that size regularity is "
            f"the remaining candidate. This refines the intervention rather "
            f"than refuting it, and earns a follow-up isolating regularity at "
            f"a fixed cluster count."
        )
    elif not mech:
        out["verdict"] = (
            "The process did not deliver the growth it promised, so the "
            "outcome is uninterpretable and the family is closed unmeasured."
        )
    else:
        out["verdict"] = (
            "P-17cO-C. Neither a monotone decline nor consistent agreement "
            "with target, with preconditions holding and the design powered to "
            "0.83 worst-case at 32 seeds. This is the family and not the "
            "experiment. The family is closed as registered."
        )
    log(out["verdict"])
    _write(out)


def _write(out: dict) -> None:
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R17C_GATE_DONE")


if __name__ == "__main__":
    main()
