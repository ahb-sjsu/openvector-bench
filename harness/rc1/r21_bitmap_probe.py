"""Probe — is the bit-address family's G1 drift a construction constant?

**NOT A REGISTERED ROUND.** No prereg, no admission claim, no gate. R20 closed
the round-8 lineage and advised against a round 21 built on it; this probes a
*different construction* (``openvector_bench.bitmap_gen``) to decide whether
registering anything is justified. Exploratory: not citable for RC-1.

## What this measures, and why the arms are what they are

The family was built on one claim: support size ``m_l`` shrinks with tree
depth, neighbours separate at depth ``l* ~ log_B(n)``, so intrinsic dimension
should fall as ``G1 ~ m0 * n**(-dim_decay/ln B)`` -- an exponent fixed by the
level plan rather than fitted, which is the property R19b's extrapolation
lacked.

Three exploratory sweeps (2026-08-08) refuted that mechanism and identified the
real driver, so the arms here are chosen to *confirm the refutation* rather than
to hunt for a passing setting:

* ``dim_decay`` is **inert**. G1 is unchanged across 0.00 / 0.12 / 0.25 and
  across a 2x change in ``m0``. The knob the family was designed around does
  nothing.
* G1 drift is **finite-depth truncation**. With ``G1 ~ c * (L - log_B n)``,
  measured exponents fell -0.705 / -0.151 / -0.087 / -0.051 at L = 20 / 30 /
  45 / 60 -- i.e. -> 0 as the depth budget grows, which is the signature of an
  artifact and the opposite of scale-free.

So the registered readout is the **depth sweep**: an exponent that tracks
``-1/(ln B * (L - log_B n))`` is truncation; one stable in L would be a genuine
construction constant. ``dim_decay = 0`` is carried as the null that must
behave identically to the decayed arm if the knob is truly inert.

Env: R21_OUT, R21_NS, R21_ARMS (list of [depth, dim_decay]), R21_SEEDS,
R21_DIM, R21_NQ, R21_K.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.bitmap_gen import (  # noqa: E402
    BITMAP_PARAMS,
    bitmap_corpus,
    emit_rows,
    level_plan,
)
from openvector_bench.generator_search import decode  # noqa: E402
from openvector_bench.geometry import hubness, id_twonn, knn  # noqa: E402

OUT = os.environ.get("R21_OUT", "results/r21_bitmap_probe.json")
NS = json.loads(os.environ.get("R21_NS", "[25000, 50000, 100000]"))
ARMS = json.loads(
    os.environ.get("R21_ARMS", "[[30,0.0],[30,0.25],[45,0.0],[45,0.25],[60,0.0]]")
)
SEEDS = json.loads(os.environ.get("R21_SEEDS", "[700, 701, 702]"))
DIM = int(os.environ.get("R21_DIM", "1024"))
NQ = int(os.environ.get("R21_NQ", "10000"))
K = int(os.environ.get("R21_K", "10"))

# R20_CONVERGENCE.md, reference rung protocol (10k queries per rung).
REAL_G1 = {25000: 26.64, 50000: 22.78, 100000: 19.92, 200000: 18.42}
LOG_B = math.log(2.0)  # log2_branch is pinned at 1.0 below


def _params(depth: float, dim_decay: float) -> dict[str, float]:
    """Corrected base config. The three constants below were each wrong on the
    first pass and are fixed by measurement, not by argument:

    ``scale_decay = 1.0`` -- at 2.0 the structured displacement is ~1e-4 by the
    depth where neighbours separate, three orders under the noise floor, so
    TwoNN read 1024-d noise in every arm (G1 pinned at ~220 regardless of knobs).
    ``noise = 0`` -- same reason; reinstate only once a mechanism survives.
    ``m0_frac = 0.015`` -- with flat amplitudes the neighbour difference spans
    the whole tail, so G1 ~ m_l*/(1-exp(-dim_decay)), not m_l*.
    """
    p = decode(np.array([]), BITMAP_PARAMS)
    p.update(
        log2_branch=1.0,
        scale_decay=1.0,
        noise=0.0,
        m0_frac=0.015,
        depth=float(depth),
        dim_decay=float(dim_decay),
    )
    return p


def _log_slope(ns: list[int], vals: list[float]) -> float:
    ok = [(n, v) for n, v in zip(ns, vals) if np.isfinite(v) and v > 0]
    if len(ok) < 2:
        return float("nan")
    return float(
        np.polyfit(np.log([n for n, _ in ok]), np.log([v for _, v in ok]), 1)[0]
    )


def _truncation_exponent(depth: float, ns: list[int]) -> float:
    """-1 / (ln B * (L - log_B n)) at the ladder midpoint."""
    mid = math.log(ns[len(ns) // 2]) / LOG_B
    return -1.0 / (LOG_B * max(depth - mid, 1e-9))


def preconditions() -> dict:
    """Determinism, random access, and the estimator domain check.

    The domain check is the precondition R20_CONVERGENCE.md named as missing:
    establish the estimator is usable across the WHOLE swept range before the
    run, not only at its starting point.
    """
    p = _params(30, 0.25)
    out: dict[str, object] = {}

    a = emit_rows(p, np.arange(64), DIM, 1)
    out["bit_exact_repeat"] = bool((a == emit_rows(p, np.arange(64), DIM, 1)).all())
    pick = np.array([7, 11, 63, 5])
    out["random_access"] = bool((emit_rows(p, pick, DIM, 1) == a[pick]).all())
    out["seed_separation"] = bool(not (emit_rows(p, np.arange(64), DIM, 2) == a).all())

    dom = {}
    for depth, dd in ARMS:
        x = bitmap_corpus(_params(depth, dd), 4000, DIM, 900)
        dist, _ = knn(x[:3000], x[3000:], K)
        r1, r2 = dist[:, 0], dist[:, 1]
        mu = r2[r1 > 0] / np.maximum(r1[r1 > 0], 1e-12)
        dom[f"L{int(depth)}_dd{dd}"] = {
            "usable_mu_frac": float((mu > 1.0).mean()),
            "g1_smoke": float(id_twonn(dist)),
        }
    out["estimator_domain"] = dom
    out["domain_ok"] = bool(
        all(v["usable_mu_frac"] > 0.5 and np.isfinite(v["g1_smoke"]) for v in dom.values())
    )
    return out


def main() -> int:
    print(f"dim={DIM} ns={NS} arms={ARMS} seeds={SEEDS} nq={NQ} k={K}", flush=True)

    pre = preconditions()
    for flag in ("bit_exact_repeat", "random_access", "seed_separation", "domain_ok"):
        print(f"  {flag}: {pre[flag]}", flush=True)
    if not all(pre[f] for f in ("bit_exact_repeat", "random_access", "seed_separation")):
        print("PRECONDITION FAILED - not measuring", flush=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"preconditions": pre}, f, indent=2)
        return 1

    arms: list[dict] = []
    for depth, dd in ARMS:
        p = _params(depth, dd)
        per_seed = []
        for seed in SEEDS:
            g1s, hubs = [], []
            for n in NS:
                x = bitmap_corpus(p, n + NQ, DIM, seed)
                dist, idx = knn(x[:n], x[n:], K)
                g1s.append(id_twonn(dist))
                hubs.append(hubness(idx, n, K))
            per_seed.append(
                {"seed": seed, "g1": g1s, "hub_skew": hubs, "exp": _log_slope(NS, g1s)}
            )
            print(
                f"  L={int(depth)} dd={dd} seed={seed} "
                f"G1={[round(v,2) for v in g1s]} exp={per_seed[-1]['exp']:+.3f}",
                flush=True,
            )
        exps = [s["exp"] for s in per_seed]
        mean_g1 = [float(np.mean([s["g1"][i] for s in per_seed])) for i in range(len(NS))]
        # G1 ~ c * (L - log_B n): recover c, the truncation model's one constant.
        c = float(
            np.mean([mean_g1[i] / max(depth - math.log(NS[i]) / LOG_B, 1e-9)
                     for i in range(len(NS))])
        )
        arms.append(
            {
                "depth": depth,
                "dim_decay": dd,
                "support_plan": [m for m, _ in level_plan(p, DIM)][:8],
                "per_seed": per_seed,
                "mean_g1": mean_g1,
                "exp_mean": float(np.mean(exps)),
                "exp_sd": float(np.std(exps, ddof=1)) if len(exps) > 1 else 0.0,
                "truncation_pred": _truncation_exponent(depth, NS),
                "truncation_c": c,
            }
        )
        a = arms[-1]
        print(
            f"ARM L={int(depth)} dd={dd}: G1 {[round(v,2) for v in mean_g1]} "
            f"exp {a['exp_mean']:+.3f} +/- {a['exp_sd']:.3f} "
            f"trunc_pred {a['truncation_pred']:+.3f} c={c:.2f}",
            flush=True,
        )

    real_exp = _log_slope(
        [n for n in NS if n in REAL_G1], [REAL_G1[n] for n in NS if n in REAL_G1]
    )
    by_depth: dict[float, list[dict]] = {}
    for a in arms:
        by_depth.setdefault(a["depth"], []).append(a)
    depths = sorted(by_depth)
    null_arms = {a["depth"]: a for a in arms if a["dim_decay"] == 0.0}
    decayed = {a["depth"]: a for a in arms if a["dim_decay"] > 0.0}
    shared = [d for d in depths if d in null_arms and d in decayed]

    verdict = {
        "real_exponent": real_exp,
        # Refutation 1: the designed knob does nothing.
        "dim_decay_inert": bool(
            shared
            and all(
                abs(decayed[d]["exp_mean"] - null_arms[d]["exp_mean"])
                < 2
                * max(decayed[d]["exp_sd"], null_arms[d]["exp_sd"], 1e-3)
                for d in shared
            )
        ),
        # Refutation 2: the drift is the depth budget, not the construction.
        "exponent_decays_with_depth": bool(
            len(depths) > 1
            and all(
                abs(null_arms[depths[i]]["exp_mean"])
                > abs(null_arms[depths[i + 1]]["exp_mean"])
                for i in range(len(depths) - 1)
                if depths[i] in null_arms and depths[i + 1] in null_arms
            )
        ),
        "g1_tracks_depth_budget": {
            str(int(a["depth"])): round(a["truncation_c"], 3) for a in arms
        },
        # The consequence that matters: at 1e12 the ladder runs off the tree.
        "log2_1e12": math.log(1e12) / LOG_B,
        "depth_needed_for_real_level_g1": None,
    }
    print("VERDICT " + json.dumps(verdict, indent=2), flush=True)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {"dim": DIM, "ns": NS, "arms": ARMS, "seeds": SEEDS,
                           "nq": NQ, "k": K, "real_g1": REAL_G1},
                "preconditions": pre,
                "arms": arms,
                "verdict": verdict,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("R21_BITMAP_PROBE_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
