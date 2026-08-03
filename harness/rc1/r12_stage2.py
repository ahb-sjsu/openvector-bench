"""Round-12 PRE-FREEZE stage 2: the decoupling check (PREREG_ROUND12 v2, draft).

Stage 1 mapped the two mechanisms independently. Stage 2 is the cross-sweep the
prereg gates stage 3 on: the G1 mechanism at its band setting must be
COUNT-QUIET, the G6 mechanism at its band setting must be ID-QUIET, and running
both must not move either gate. If either moves the other, H12's premise fails
at that point and it is reported before any joint fit.

Two things make this run necessary rather than a repeat:

1. The committed ``r12_stage1.json`` has ``grid_c = None`` — the cascade sweep
   was added to the stage-1 driver after that result was produced, so **the
   cascade has never been measured on the ladder.** Its only evidence is the
   unit-scale presence gate (n = 3000, dim = 64) in R12_PREFREEZE_AUDIT §6.
   P-A''s target statistic is G1 n-drift across the ladder, which nothing has
   measured yet.
2. The audit's §1 mixture arithmetic requires ``cascade_frac >= ~0.79``, and its
   §6 gate found that the only setting satisfying both the arithmetic and the
   presence gate is ``frac 0.85 / smin 0.05 / alpha 3`` (audit recommendation 6).
   Stage 1's ``GRID_C`` tops out at ``frac 0.7`` and never visits it. A stage-2
   pass at ``frac 0.5`` would not license the operating point P-A' needs
   (audit recommendation 2).

So the grid below is centred on the audited candidate. ``CASC_A1`` is the same
point at ``alpha = 1``, included because the audit's §6(b) withdrawal rests on a
unit-scale KS reading: if the realized-spectrum story is right, the alpha-3 point
should show the flatter G1 drift on the ladder too, and if the drift is the same
for both then flatness-of-spectrum is not what is driving drift and §6(b) needs
revisiting. That is a real prediction this run can falsify.

Instruments are stage 1's, imported rather than reimplemented, so cells stay
aligned with ``r11v2_real_ref.json`` and with the stage-1 maps. The subsample
operator (``rng(10_000*sub + n)``), holdout, pool size and ladder are unchanged.

Calibration only. Nothing here freezes the prereg, no bands are adjusted, no
admission is run, the sealed rows stay untouched (the real side is read from the
committed 5-draw reference, never regenerated).

Env: R12_DIR, R12_PARAMS, R12_REAL, R12_SPECTRUM, R12_NS, R12_SUBS, R12_POOL,
R12_OUT2 (output; default results/r12_stage2.json), R12_CAND_SUBS (draws for the
freeze candidate; default 5 per the prereg's freeze-candidate rule).
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import r12_stage1 as S  # noqa: E402  (instruments; import after path fix)

from openvector_bench import geometry as G  # noqa: E402
from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    hier_r12_corpus,
    set_spectrum_target,
)

OUT = os.environ.get("R12_OUT2", os.path.join(S.R12, "r12_stage2.json"))
CAND_SUBS = tuple(
    int(s) for s in os.environ.get("R12_CAND_SUBS", "0,1,2,3,4").split(",")
)

# The level dial stays on in every arm so the comparison isolates the mechanism
# under test rather than the dial. This is stage 1's sweep-C control.
DIAL = {"grad_decay": 0.5}
CASCADE = {"cascade_frac": 0.85, "cascade_smin": 0.05, "cascade_alpha": 3.0}
CASCADE_A1 = {"cascade_frac": 0.85, "cascade_smin": 0.05, "cascade_alpha": 1.0}
OCCUPANCY = {"occ_mix": 1.0, "occ_tail": 1.8, "dens_span": 0.3}

# (tag, overrides, draws). The candidate and its control get the prereg's
# 5-draw freeze-candidate treatment; the rest get the 2-draw map treatment.
ARMS: list[tuple[str, dict, tuple[int, ...]]] = [
    ("ctrl", dict(DIAL), CAND_SUBS),
    ("casc", DIAL | CASCADE, CAND_SUBS),
    ("casc_a1", DIAL | CASCADE_A1, S.SUBS),
    ("occ", DIAL | OCCUPANCY, S.SUBS),
    ("both", DIAL | CASCADE | OCCUPANCY, CAND_SUBS),
]
if os.environ.get("R12_ARMS"):
    ARMS = [
        (a["tag"], a["over"], tuple(a["subs"]))
        for a in json.loads(os.environ["R12_ARMS"])
    ]


def draw_noise(rows: list[dict], name: str, field: str) -> dict:
    """Between-draw spread per (n, k), as a fraction of the mean.

    The prereg's quietness criterion is "within draw noise", so the noise has to
    be measured from the draws themselves rather than assumed.
    """
    acc: dict = {}
    for r in rows:
        if r["corpus"] == name:
            acc.setdefault((r["n"], r["k"]), []).append(r[field])
    out = {}
    for (n, k), v in sorted(acc.items()):
        m = float(np.mean(v))
        out[f"n{n}_k{k}"] = round(float(np.std(v)) / max(abs(m), 1e-12), 4)
    return out


def quietness(rows: list[dict], name: str, control: str, field: str) -> dict:
    """Is `name` within control draw noise on `field` at every ladder cell?

    Returns the worst cell and a verdict. A mechanism is quiet when the shift it
    causes is not distinguishable from the control's own draw-to-draw scatter.
    """
    m = S._mean_by_nk(rows, name, field)
    c = S._mean_by_nk(rows, control, field)
    noise = draw_noise(rows, control, field)
    # POOLED noise, not per-cell. With 2-5 draws a cell whose control draws
    # happen to land on top of each other gets a near-zero sigma, and dividing
    # by it reports an astronomical z from what is actually a quiet cell (the
    # screening run produced 495 this way). Draw noise is not expected to vary
    # sharply cell to cell, so the median across cells is the better estimate of
    # the scale, and the per-cell values stay in the output to be inspected.
    vals = [v for v in noise.values() if v > 0]
    pooled = float(np.median(vals)) if vals else 0.0
    scale = max(pooled, 1e-3)
    cells, worst, worst_cell = {}, 0.0, None
    for key in sorted(set(m) & set(c)):
        n, k = key
        ratio = m[key] / max(abs(c[key]), 1e-12)
        z = abs(ratio - 1.0) / scale
        cells[f"n{n}_k{k}"] = {
            "ratio": round(ratio, 3),
            "z_vs_draw_noise": round(z, 2),
            "cell_sigma": noise.get(f"n{n}_k{k}"),
        }
        if z > worst:
            worst, worst_cell = z, f"n{n}_k{k}"
    return {
        "field": field,
        "pooled_sigma": round(pooled, 5),
        "worst_z": round(worst, 2),
        "worst_cell": worst_cell,
        "quiet": bool(worst <= 2.0),
        "cells": cells,
    }


def gate_at_ladder(
    x_base: np.ndarray, n: int, sub: int, ref_r1: float | None
) -> tuple[dict, float]:
    """Run the audit's mechanism-presence gate at ladder scale, not unit scale.

    §6 of the audit established the gate at n = 3000 / dim = 64. The claim P-A'
    makes is about the corpus we actually measure, so the gate is re-read on the
    same subsample operator the gates are scored on.

    Call convention follows the gate's own test: query base against base with
    k = 4 and drop the self column, since the gate wants base-to-base neighbour
    distances excluding self. Querying with held-out rows instead would measure
    a different object. The query side is subsampled because the full n x n
    problem is not needed for a distributional reading.

    Returns the gate dict and this arm's median r1, so the control can supply
    ``ref_r1_median`` to every other arm. Passing it matters: the gate's
    docstring warns that falling back to each sample's own median conflates the
    cascade with the ambient scale, which would make every arm look alike.
    """
    rng = np.random.default_rng(10_000 * sub + n)
    bi = rng.choice(len(x_base), size=min(n, len(x_base)), replace=False)
    base = G.normalize(x_base[bi])
    qi = rng.choice(len(base), size=min(4000, len(base)), replace=False)
    d, _ = G.knn(base, base[qi], 4)
    d = d[:, 1:]  # drop the self column
    return G.cascade_spectrum_gate(d, ref_r1_median=ref_r1), float(np.median(d[:, 0]))


def main() -> None:
    set_spectrum_target(S.SPECTRUM)
    base_params = json.load(open(S.PARAMS_PATH, encoding="utf-8"))["params"]
    real_rows = json.load(open(S.REAL_REF, encoding="utf-8"))["rows"]
    real = {(r["scope"], r["sub"], r["k"]): r for r in real_rows}
    S.log(f"stage2 ladder ns={S.NS} pool={S.POOL} instance={S.M_ROWS}")
    S.log(f"arms: {[(t, sorted(o), len(sb)) for t, o, sb in ARMS]}")

    meta = {
        "prereg": "results/PREREG_ROUND12.md v2 (draft; stage-2 decoupling check)",
        "audit": "results/R12_PREFREEZE_AUDIT.md (recommendations 1, 2, 6)",
        "why": (
            "committed r12_stage1.json has grid_c=None, so the cascade has never "
            "been measured on the ladder; P-A' target statistic is undecided"
        ),
        "params_path": S.PARAMS_PATH,
        "real_ref": S.REAL_REF,
        "arch_off": S.ARCH_OFF,
        "ns": S.NS,
        "pool": S.POOL,
        "instance_rows": S.M_ROWS,
        "dim": S.DIM,
        "seed": S.SEED,
        "arms": [{"tag": t, "over": o, "subs": list(sb)} for t, o, sb in ARMS],
        "screening": bool(
            os.environ.get("R12_NS")
            or os.environ.get("R12_POOL")
            or os.environ.get("R12_SUBS")
        ),
        "n_query": G.N_QUERY,
        "quiet_rule": "|ratio-1| <= 2 x control between-draw sigma at every cell",
    }
    cells: list[dict] = []
    gates: dict[str, dict] = {}
    names: dict[str, str] = {}
    ref_r1: float | None = None

    def flush(extra: dict | None = None) -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "cells": cells, "gates": gates} | (extra or {}), f)

    for tag, over, subs in ARMS:
        name = f"{tag}_" + ("_".join(f"{k}{v:g}" for k, v in sorted(over.items())))
        names[tag] = name
        params = base_params | S.ARCH_OFF | over
        S.log(f"{name}: generating pool instance ({S.M_ROWS} rows), {len(subs)} draws")
        x = hier_r12_corpus(params, S.M_ROWS, S.DIM, S.SEED)
        base_blk = x[: S.M_ROWS - int(round(S.M_ROWS * QUERY_FRAC))]
        hmask = S.uniform_holdout_mask(len(base_blk), S.HOLD, seed=70)
        pool_base, pool_q = base_blk[~hmask], base_blk[hmask]

        # Mechanism presence at ladder scale, read on the largest ladder cell.
        # The control runs first and sets the sub-ambient cut for every arm.
        g, med_r1 = gate_at_ladder(pool_base, max(S.NS), 0, ref_r1)
        if tag == "ctrl":
            ref_r1 = med_r1
            # Re-read the control against its own established cut so the
            # reported control row is comparable with the arms that follow.
            g, _ = gate_at_ladder(pool_base, max(S.NS), 0, ref_r1)
        gates[tag] = g | {"median_r1": round(med_r1, 6), "ref_r1_used": ref_r1}
        S.log(f"{name}: presence gate {g}")

        saved = S.SUBS
        S.SUBS = subs  # instruments read the module global; set it per arm
        try:
            rows = S.measure_counts(name, pool_base, pool_q)
        finally:
            S.SUBS = saved
        cells.extend({"overrides": over, "arm": tag} | r for r in rows)
        del x, base_blk, pool_base, pool_q
        flush()

    ctrl, casc, occ, both = (
        names["ctrl"],
        names["casc"],
        names["occ"],
        names["both"],
    )
    verdict = {
        # P-A': does the cascade flatten G1 drift, and is it count-quiet?
        "pa_prime": {
            "dslope_g1_ctrl": S.summarize(cells, ctrl, ctrl, real)["dslope_g1"],
            "dslope_g1_casc": S.summarize(cells, casc, ctrl, real)["dslope_g1"],
            "dslope_g1_casc_a1": S.summarize(cells, names["casc_a1"], ctrl, real)[
                "dslope_g1"
            ],
            "bound": 0.05,
            "count_quiet": quietness(cells, casc, ctrl, "s_k"),
        },
        # P-B': is the occupancy law ID-quiet?
        "pb_prime": {
            "id_quiet": quietness(cells, occ, ctrl, "g1_id_twonn"),
            "dslope_sk": S.summarize(cells, occ, ctrl, real)["dslope_sk_per_k"],
        },
        # Decoupling: does running both move either gate off its single-arm value?
        "interaction": {
            "both_vs_casc_on_g1": quietness(cells, both, casc, "g1_id_twonn"),
            "both_vs_occ_on_sk": quietness(cells, both, occ, "s_k"),
        },
        "summaries": {t: S.summarize(cells, names[t], ctrl, real) for t, _, _ in ARMS},
    }
    flush({"verdict": verdict})
    S.log(f"wrote {OUT} ({len(cells)} rows)")
    print(json.dumps(verdict["pa_prime"], indent=2)[:1200], flush=True)
    print("R12_STAGE2_DONE", flush=True)


if __name__ == "__main__":
    main()
