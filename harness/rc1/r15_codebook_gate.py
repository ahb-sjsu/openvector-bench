"""Presence gate for the Dirichlet-codebook family: is it subsample-covariant?

One question, asked before anything else is built on this family, because it
is the property that killed rounds 9, 11 and 12: does hub mass re-express at
every sampling scale, or does it sit with owners that either keep their
counts or vanish?

Measured the way the campaign now knows how to measure it. Raw counts and raw
maxima are budget-bound (`spec/QUERY_BUDGET.md`), so the readouts are the
invariant forms: ``attractiveness_skew`` for the skew route and
``tail_excess`` for the mass route, with rho reported on every cell. The
ladder is run at CONSTANT rho, so any slope is the corpus and not the budget.

Registered before running (this file is the registration; nothing here reads
a band or claims admission):

  P-15A  the family is subsample-covariant: |slope of attractiveness_skew|
         <= 0.05/decade across the ladder, on >= 3 seeds. Real's own value is
         the comparison, not a band.
  P-15B  r and mu decouple: doubling r moves G3 by >= 25% while moving G1 by
         <= 10%; doubling mu moves G1 by >= 25% while moving G3 by <= 10%.
         This is the G1/G3 separation rounds 1-2 concluded the manifold
         family did not have.
  P-15C  atom_tail buys hubness without paying G1 or G3: raising it moves
         attractiveness_skew by >= 50% while G1 and G3 each move <= 10%.

Failure of P-15A closes the family on the spot — no tuning, no second
parameterization. That is the whole point of gating first.

Env: R15_OUT, R15_NS, R15_DIM, R15_SEEDS, R15_RHO, R15_K.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.generator_search import (  # noqa: E402
    dirichlet_codebook_corpus,
    geometry_vector,
)
from openvector_bench.geometry import knn, normalize  # noqa: E402
from openvector_bench.hubness import (  # noqa: E402
    attractiveness_skew,
    rho,
    tail_excess,
)

OUT = os.environ.get("R15_OUT", "results/r15_codebook_gate.json")
NS = json.loads(os.environ.get("R15_NS", "[12500, 25000, 50000, 100000]"))
DIM = int(os.environ.get("R15_DIM", "1024"))
SEEDS = json.loads(os.environ.get("R15_SEEDS", "[0, 1, 2]"))
RHO = float(os.environ.get("R15_RHO", "4.0"))  # constant slots per point
K = int(os.environ.get("R15_K", "10"))

BASE = {"log2_atoms": 7.55, "concentration": 0.28, "atom_tail": 0.8, "noise": 0.05}


def log(m: str) -> None:
    print(m, flush=True)


def slope(xs, ys) -> float:
    x = np.log10(np.asarray(xs, dtype=float))
    y = np.asarray(ys, dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return float("nan")
    return float(np.polyfit(x[ok], y[ok], 1)[0])


def counts_at(params: dict, n: int, seed: int) -> np.ndarray:
    """Corpus of n rows plus a query block sized to hold rho constant."""
    nq = max(50, int(round(RHO * n / K)))
    x = dirichlet_codebook_corpus(params, n + nq, DIM, seed)
    base, q = normalize(x[:n]), normalize(x[n:])
    _, idx = knn(base, q, K)
    return np.bincount(idx[:, :K].ravel(), minlength=n).astype(float), nq


def main() -> None:
    log("R15 CODEBOOK GATE — subsample covariance first (P-15A)")
    log(f"ladder {NS} at constant rho={RHO}, dim={DIM}, seeds={SEEDS}")

    # ---- P-15A: does hub mass re-express under the sampling operator? ----
    per_seed_slopes, cells = [], []
    for sd in SEEDS:
        askew, texc = [], []
        for n in NS:
            c, nq = counts_at(BASE, n, sd)
            a = attractiveness_skew(c)
            t = tail_excess(c, n, 0.01)
            askew.append(a)
            texc.append(t)
            cells.append(
                {
                    "seed": sd,
                    "n": n,
                    "nq": nq,
                    "rho": rho(nq, K, n),
                    "attractiveness_skew": a,
                    "tail_excess": t,
                    "zero_frac": float((c == 0).mean()),
                }
            )
            log(
                f"  seed {sd} n={n:7d} rho={rho(nq, K, n):.2f} "
                f"attr_skew={a:.3f} tail_exc={t:.3f}"
            )
        per_seed_slopes.append(slope(NS, askew))
    a_slope = float(np.mean(per_seed_slopes))
    p15a = bool(abs(a_slope) <= 0.05)
    log(
        f"\nP-15A: attractiveness_skew slope/decade = {a_slope:+.4f} "
        f"(per seed {[round(s, 3) for s in per_seed_slopes]}) -> "
        f"{'PASS' if p15a else 'FAIL'}"
    )

    out = {
        "meta": {
            "registered": "harness/rc1/r15_codebook_gate.py docstring",
            "family": "dirichlet_codebook_corpus",
            "base_params": BASE,
            "ns": NS,
            "dim": DIM,
            "seeds": SEEDS,
            "rho_held_constant": RHO,
            "k": K,
            "readouts": "invariant forms only (spec/QUERY_BUDGET.md)",
        },
        "cells": cells,
        "P15A": {
            "slope_per_decade": a_slope,
            "per_seed": per_seed_slopes,
            "threshold": 0.05,
            "passes": p15a,
        },
    }

    if not p15a:
        out["verdict"] = (
            "P-15A fails: hub mass does not re-express under the sampling "
            "operator. The family is closed here, as registered — no tuning, "
            "no second parameterization."
        )
        log(out["verdict"])
    else:
        # ---- P-15B / P-15C only run on a passing gate ----
        log("\ngate passed; measuring knob separation (P-15B, P-15C)")
        n_probe = NS[1]

        def gates(params, seed):
            nq = max(50, int(round(RHO * n_probe / K)))
            x = dirichlet_codebook_corpus(params, n_probe + nq, DIM, seed)
            b, q = normalize(x[:n_probe]), normalize(x[n_probe:])
            gv = geometry_vector(b, q, K, 100)
            _, idx = knn(b, q, K)
            c = np.bincount(idx[:, :K].ravel(), minlength=n_probe).astype(float)
            return {
                "g1": float(gv["g1_id_twonn"]),
                "g3": float(gv["g3_eff_rank"]),
                "attr_skew": attractiveness_skew(c),
            }

        arms = {
            "base": BASE,
            "r_doubled": dict(BASE, log2_atoms=BASE["log2_atoms"] + 1.0),
            "mu_doubled": dict(BASE, concentration=BASE["concentration"] * 2),
            "tail_raised": dict(BASE, atom_tail=BASE["atom_tail"] + 0.7),
        }
        meas = {}
        for name, pr in arms.items():
            vals = [gates(pr, sd) for sd in SEEDS[:2]]
            meas[name] = {
                key: float(np.mean([v[key] for v in vals])) for key in vals[0]
            }
            log(
                f"  {name:12s} g1={meas[name]['g1']:.3g} "
                f"g3={meas[name]['g3']:.3g} attr={meas[name]['attr_skew']:.3g}"
            )

        def rel(a, b):
            return abs(a / max(b, 1e-12) - 1.0)

        b0 = meas["base"]
        p15b = bool(
            rel(meas["r_doubled"]["g3"], b0["g3"]) >= 0.25
            and rel(meas["r_doubled"]["g1"], b0["g1"]) <= 0.10
            and rel(meas["mu_doubled"]["g1"], b0["g1"]) >= 0.25
            and rel(meas["mu_doubled"]["g3"], b0["g3"]) <= 0.10
        )
        p15c = bool(
            rel(meas["tail_raised"]["attr_skew"], b0["attr_skew"]) >= 0.50
            and rel(meas["tail_raised"]["g1"], b0["g1"]) <= 0.10
            and rel(meas["tail_raised"]["g3"], b0["g3"]) <= 0.10
        )
        out["knob_separation"] = meas
        out["P15B"] = {"passes": p15b}
        out["P15C"] = {"passes": p15c}
        log(f"\nP-15B (r/mu decouple G3/G1): {'PASS' if p15b else 'FAIL'}")
        log(f"P-15C (tail buys hubness free): {'PASS' if p15c else 'FAIL'}")

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log("R15_CODEBOOK_GATE_DONE")


if __name__ == "__main__":
    main()
