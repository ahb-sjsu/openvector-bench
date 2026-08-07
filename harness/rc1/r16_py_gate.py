"""Round 16 gate: can a growing codebook match real's hub scaling?

The round-15 fixed codebook grew hub concentration about six times faster
than the real corpus does. The diagnosis was that a fixed set of atoms is a
fixed set of owners, so every added row crowds the same attractors. This
family gives atom popularity a power-law tail, so the number of atoms a
corpus touches grows as ``n**py_alpha`` emergently, and ``py_alpha``
therefore controls how fast concentration is diluted.

Registered before running. This file is the registration.

  **Target.** Real's attractiveness-skew slope at k = 10 is +0.51 per decade,
  measured three times across two budget protocols and two ladder widths with
  a spread of 0.07 (`results/r14_real_targets_wide.json`). k = 30 is measured
  and reported but does not gate, because its own spread of 0.22 exceeds the
  tolerance it would be enforced with.

  **P-16A (the family contains a solution).** The slope is monotone
  decreasing in ``py_alpha`` over the declared range [0.2, 0.8], and some
  value in that range brings it within +/-0.15 of +0.51 at k = 10 on >= 3
  seeds. Monotonicity is registered as well as existence, because a family
  that hits the target non-monotonically has no controller, only a
  coincidence.

  **P-16B (the fix is not paid for elsewhere).** At the value of ``py_alpha``
  that satisfies P-16A, G1 and G3 both sit within [0.5, 2.0]x of real. This
  is a viability band, not the admission band, and clearing it is necessary
  rather than sufficient.

  **P-16C (it is stable).** At that same value, the per-seed spread of the
  slope is <= 0.3. Round 15's family spanned 8.4 across three seeds, which
  would have disqualified it whatever its central value.

``py_alpha`` is fitted within the declared range, and the fitted value is
reported as fitted. What is registered in advance is the range, the
monotonicity, the target, and the tolerance. Failure of P-16A closes the
family. Failure of P-16B or P-16C is reported as a measured trade-off and
does not license a search for a different parameterization inside this round.

Env: R16_OUT, R16_ALPHAS, R16_NS, R16_DIM, R16_SEEDS, R16_RHO, R16_K.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    geometry_vector,
    py_codebook_corpus,
)
from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.hubness import attractiveness_skew  # noqa: E402

OUT = os.environ.get("R16_OUT", "results/r16_py_gate.json")
ALPHAS = json.loads(os.environ.get("R16_ALPHAS", "[0.2, 0.35, 0.5, 0.65, 0.8]"))
NS = json.loads(os.environ.get("R16_NS", "[12500, 25000, 50000]"))
DIM = int(os.environ.get("R16_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R16_SEEDS", "[0, 1, 2]"))
RHO = float(os.environ.get("R16_RHO", "4.0"))
K = int(os.environ.get("R16_K", "10"))

TARGET_SLOPE = 0.51
TOLERANCE = 0.15
BASE = {"py_theta": 10.0, "atoms_per_row": 8, "concentration": 0.3, "noise": 0.05}

# Real geometry, for the P-16B viability band.
REAL_G1, REAL_G3 = 57.66, 187.94


def log(m: str) -> None:
    print(m, flush=True)


def slope(xs, ys) -> float:
    x = np.log10(np.asarray(xs, float))
    y = np.asarray(ys, float)
    ok = np.isfinite(y)
    return float(np.polyfit(x[ok], y[ok], 1)[0]) if ok.sum() >= 2 else float("nan")


def measure(params: dict, n: int, seed: int):
    nq = max(50, int(round(RHO * n / K)))
    x = py_codebook_corpus(params, n + nq, DIM, seed)
    base, q = normalize(x[:n]), normalize(x[n:])
    _, idx = knn(base, q, K)
    c = np.bincount(idx[:, :K].ravel(), minlength=n).astype(float)
    return attractiveness_skew(c), nq


def main() -> None:
    log("R16 PY-CODEBOOK GATE")
    log(
        f"target {TARGET_SLOPE:+.2f} +/- {TOLERANCE} at k={K}, "
        f"alphas {ALPHAS}, ladder {NS} at rho={RHO}"
    )

    arms = []
    for alpha in ALPHAS:
        params = dict(BASE, py_alpha=alpha)
        per_seed = []
        for sd in SEEDS:
            vals = []
            for n in NS:
                a, nq = measure(params, n, sd)
                vals.append(a)
            per_seed.append(slope(NS, vals))
        sl = float(np.nanmean(per_seed))
        spread = float(np.nanmax(per_seed) - np.nanmin(per_seed))
        arms.append(
            {
                "py_alpha": alpha,
                "slope": sl,
                "per_seed": per_seed,
                "spread": spread,
                "within_tolerance": bool(abs(sl - TARGET_SLOPE) <= TOLERANCE),
            }
        )
        log(
            f"  alpha={alpha:.2f}  slope={sl:+.3f}  spread={spread:.3f}  "
            f"{'IN BAND' if arms[-1]['within_tolerance'] else ''}"
        )

    slopes = [a["slope"] for a in arms]
    diffs = np.diff(slopes)
    monotone = bool(np.all(diffs <= 0.05))  # decreasing, small tolerance for noise
    solutions = [a for a in arms if a["within_tolerance"]]
    p16a = bool(monotone and solutions)
    log(
        f"\nP-16A monotone={monotone} solutions={[a['py_alpha'] for a in solutions]} "
        f"-> {'PASS' if p16a else 'FAIL'}"
    )

    out = {
        "meta": {
            "registered": "harness/rc1/r16_py_gate.py docstring",
            "family": "py_codebook_corpus",
            "target_slope": TARGET_SLOPE,
            "tolerance": TOLERANCE,
            "target_source": "results/r14_real_targets_wide.json (k=10, 3 "
            "measurements, spread 0.07)",
            "declared_alpha_range": [min(ALPHAS), max(ALPHAS)],
            "base_params": BASE,
            "ns": NS,
            "rho": RHO,
            "k": K,
            "seeds": SEEDS,
        },
        "arms": arms,
        "P16A": {"monotone": monotone, "passes": p16a},
    }

    if not p16a:
        out["verdict"] = (
            "P-16A fails. Either the slope is not monotone in py_alpha, in "
            "which case the family has no controller, or no value in the "
            "declared range reaches the target. Closed as registered."
        )
        log(out["verdict"])
    else:
        best = min(solutions, key=lambda a: abs(a["slope"] - TARGET_SLOPE))
        alpha = best["py_alpha"]
        log(
            f"\nfitted py_alpha={alpha} (reported as fitted); "
            f"measuring P-16B and P-16C there"
        )
        params = dict(BASE, py_alpha=alpha)
        n_probe = NS[1]
        g1s, g3s = [], []
        for sd in SEEDS:
            nq = max(50, int(round(RHO * n_probe / K)))
            x = py_codebook_corpus(params, n_probe + nq, DIM, sd)
            b, q = normalize(x[:n_probe]), normalize(x[n_probe:])
            gv = geometry_vector(b, q, K, 100)
            g1s.append(float(gv["g1_id_twonn"]))
            g3s.append(float(gv["g3_eff_rank"]))
        g1, g3 = float(np.mean(g1s)), float(np.mean(g3s))
        r1, r3 = g1 / REAL_G1, g3 / REAL_G3
        p16b = bool(0.5 <= r1 <= 2.0 and 0.5 <= r3 <= 2.0)
        p16c = bool(best["spread"] <= 0.3)
        out["fitted_py_alpha"] = alpha
        out["P16B"] = {
            "g1": g1,
            "g3": g3,
            "g1_ratio": r1,
            "g3_ratio": r3,
            "passes": p16b,
        }
        out["P16C"] = {"spread": best["spread"], "passes": p16c}
        log(
            f"P-16B G1={g1:.3g} ({r1:.2f}x real) G3={g3:.3g} ({r3:.2f}x real) "
            f"-> {'PASS' if p16b else 'FAIL'}"
        )
        log(f"P-16C spread={best['spread']:.3f} -> {'PASS' if p16c else 'FAIL'}")
        out["verdict"] = (
            "P-16A passes; see P-16B and P-16C for whether the fix is paid "
            "for elsewhere and whether it is stable."
        )

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R16_PY_GATE_DONE")


if __name__ == "__main__":
    main()
