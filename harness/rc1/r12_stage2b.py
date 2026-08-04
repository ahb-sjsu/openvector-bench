"""Round-12 stage 2b: buy the missing octaves, then re-ask P-A' (PREREG_ROUND12 v2).

Stage 2 measured the audited operating point on the ladder and found the
mechanism was not there: 1.99 octaves and KS 0.198 against the >= 3 and <= 0.15
the claim requires, where the same knobs passed at n = 3000 / dim = 64. So P-A'
was never actually tested. See GEN_ROUND12_STAGE2.md.

`cascade_smin` sets how fine the attachment offsets go, and offsets span
log2(1/smin) octaves. At 0.05 that is 4.3 nominal and 2.0 realized. The declared
range reaches 0.001, about 10 nominal, so the octaves are buyable.

GATE FIRST. Stage 2's lesson, and rounds 9 and 11's before it, is that this
campaign keeps building predictions on a cheaper proxy that then fails to
transfer. So phase 1 reads only the presence gate across smin, at ladder scale,
and phase 2 spends the expensive full-ladder measurement only on settings whose
mechanism is demonstrably present. Nothing is read for drift or level at a
setting that failed its gate.

Phase 2 also carries a lower-fraction arm. Stage 2's real signal was that the
attachment fraction the mixture arithmetic demands (>= ~0.79) collapses G1 to
0.25-0.35x of real, because rows descended from rows form tight clumps and
clumps read as low dimension. If more octaves fix the spectrum, the open
question is whether a smaller fraction can hold the drift without collapsing
the level. That is the trade-off this maps.

alpha is held at 1. Stage 2 falsified the audit's 6(b) withdrawal: on the ladder
alpha 3 and alpha 1 have the same KS within noise (0.198 vs 0.206) while alpha 3
is far worse on drift (-0.33 vs +0.083), so alpha 3's supposed compensation does
not exist at this scale.

Calibration only. Nothing frozen, no bands adjusted, sealed rows untouched.

Env: R12_OUT2B (output), R12_SMINS (JSON list), R12_FRACS (JSON list for phase
2), plus stage 1's ladder/pool/params variables.
"""

from __future__ import annotations

import gc
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import r12_stage1 as S  # noqa: E402
import r12_stage2 as S2  # noqa: E402

from openvector_bench.generator_search import (  # noqa: E402
    QUERY_FRAC,
    hier_r12_corpus,
    set_spectrum_target,
)

OUT = os.environ.get("R12_OUT2B", os.path.join(S.R12, "r12_stage2b.json"))

# Phase 1 sweeps BOTH knobs, not just smin.
#
# A screening pass showed realized octaves pinned near 2 whether smin was 0.01
# or 0.001, i.e. 3.3 extra nominal octaves bought -0.04 realized. So smin alone
# probably cannot buy the missing octaves, and the reason is likely structural:
# r1 is the distance to the NEAREST neighbour, not to the parent. At 85%
# attachment a row's nearest neighbour is usually a SIBLING, so r1 is set by how
# densely children pile around a parent rather than by the offset law, and the
# scale-free spectrum never reaches the statistic the gate reads.
#
# That single mechanism would explain both stage-2 failures at once, the capped
# octaves and the collapsed G1, since tight sibling clumps read as low
# dimension. It also makes a falsifiable prediction the grid below tests
# directly: LOWER frac should RAISE realized octaves, because fewer siblings per
# parent lets the parent offset be the nearest thing. That is the opposite
# direction from the one the audit's mixture arithmetic wants, so if it holds
# the two requirements are in structural conflict rather than needing a tune.
PHASE1 = json.loads(
    os.environ.get(
        "R12_PHASE1",
        json.dumps(
            [
                {"cascade_frac": 0.85, "cascade_smin": 0.05},  # stage-2 point
                {"cascade_frac": 0.85, "cascade_smin": 0.01},
                {"cascade_frac": 0.85, "cascade_smin": 0.001},
                {"cascade_frac": 0.60, "cascade_smin": 0.01},
                {"cascade_frac": 0.35, "cascade_smin": 0.01},
                {"cascade_frac": 0.15, "cascade_smin": 0.01},
            ]
        ),
    )
)
FRACS = json.loads(os.environ.get("R12_FRACS", "[0.85, 0.7]"))
DIAL = {"grad_decay": 0.5}
ALPHA = 1.0
N_FULL_ARMS = int(os.environ.get("R12_N_FULL_ARMS", "2"))


def instance(over: dict, base_only: bool = False):
    """One pool instance under the registered operator, split base / queries.

    ``base_only`` skips materialising the held-out query block. Phase 1 reads
    only the presence gate, which is a base-to-base statistic, so carrying the
    query copy through seven iterations is pure waste — and holding it in a
    discarded ``_`` binding keeps it alive until the next loop iteration
    rebinds, which is what pushed this over 8Gi and got the job OOMKilled.

    Boolean-mask indexing copies, so peak inside this function is the full
    instance plus the base copy. The instance is freed on return; the caller
    should free the base as soon as it is done with it.
    """
    params = json.load(open(S.PARAMS_PATH, encoding="utf-8"))["params"]
    x = hier_r12_corpus(params | S.ARCH_OFF | over, S.M_ROWS, S.DIM, S.SEED)
    base_blk = x[: S.M_ROWS - int(round(S.M_ROWS * QUERY_FRAC))]
    hmask = S.uniform_holdout_mask(len(base_blk), S.HOLD, seed=70)
    base = base_blk[~hmask]
    if base_only:
        del x, base_blk
        gc.collect()
        return base, None
    return base, base_blk[hmask]


def main() -> None:
    set_spectrum_target(S.SPECTRUM)
    real_rows = json.load(open(S.REAL_REF, encoding="utf-8"))["rows"]
    real = {(r["scope"], r["sub"], r["k"]): r for r in real_rows}
    n_max = max(S.NS)

    meta = {
        "prereg": "results/PREREG_ROUND12.md v2 (draft; stage-2b, gate first)",
        "prior": "results/GEN_ROUND12_STAGE2.md (mechanism absent at ladder scale)",
        "phase1_grid": PHASE1,
        "fracs": FRACS,
        "alpha": ALPHA,
        "ns": S.NS,
        "pool": S.POOL,
        "instance_rows": S.M_ROWS,
        "dim": S.DIM,
        "screening": bool(os.environ.get("R12_NS") or os.environ.get("R12_POOL")),
        "gate_thresholds": {
            "min_octaves": 3.0,
            "max_ks": 0.15,
            "min_logmu_spread": 0.5,
        },
        "rule": "no drift or level is read at a setting whose presence gate failed",
    }
    out: dict = {"meta": meta, "phase1_gates": [], "phase2": {}}

    def flush() -> None:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f)

    # ---- phase 1: presence gate across smin, at ladder scale -----------------
    S.log("PHASE 1 — presence gate vs cascade_smin at n=%d" % n_max)
    pool_base, _ = instance(DIAL, base_only=True)
    _, ref_r1 = S2.gate_at_ladder(pool_base, n_max, 0, None)
    g_ctrl, _ = S2.gate_at_ladder(pool_base, n_max, 0, ref_r1)
    out["phase1_gates"].append({"tag": "ctrl", "smin": None, "gate": g_ctrl})
    S.log(f"ctrl gate {g_ctrl}")
    del pool_base
    gc.collect()
    flush()

    for pt in PHASE1:
        over = DIAL | dict(pt) | {"cascade_alpha": ALPHA}
        frac, smin = pt["cascade_frac"], pt["cascade_smin"]
        pb, _ = instance(over, base_only=True)
        g, _ = S2.gate_at_ladder(pb, n_max, 0, ref_r1)
        out["phase1_gates"].append(
            {
                "tag": f"f{frac:g}_smin{smin:g}",
                "frac": frac,
                "smin": smin,
                "gate": g,
            }
        )
        S.log(
            f"frac={frac:g} smin={smin:g}: octaves={g.get('octaves_spanned'):.2f} "
            f"ks={g.get('ks_uniform'):.3f} mu={g.get('logmu_spread'):.3f} "
            f"passed={g.get('passed')}"
        )
        del pb
        gc.collect()
        flush()

    # Does lowering frac raise realized octaves? This is the sibling-crowding
    # prediction, recorded whether it holds or not.
    at_smin01 = {
        r["frac"]: r["gate"]["octaves_spanned"]
        for r in out["phase1_gates"]
        if r.get("smin") == 0.01
    }
    out["sibling_crowding_test"] = {
        "octaves_by_frac_at_smin0.01": at_smin01,
        "prediction": "octaves rise as frac falls",
        "holds": (
            None
            if len(at_smin01) < 2
            else bool(
                all(
                    a >= b - 1e-9
                    for a, b in zip(
                        [at_smin01[k] for k in sorted(at_smin01)],
                        [at_smin01[k] for k in sorted(at_smin01)][1:],
                    )
                )
            )
        ),
    }
    S.log(f"sibling-crowding: {out['sibling_crowding_test']}")
    flush()

    passing = [
        r
        for r in out["phase1_gates"]
        if r.get("smin") is not None and r["gate"].get("passed")
    ]
    if not passing:
        # Rank by distance to the thresholds so the record says how close it got.
        ranked = sorted(
            (r for r in out["phase1_gates"] if r["smin"] is not None),
            key=lambda r: (
                -min(r["gate"]["octaves_spanned"], 3.0),
                r["gate"]["ks_uniform"],
            ),
        )
        out["phase2"] = {
            "ran": False,
            "why": (
                "no smin in the declared range makes the mechanism present at "
                "ladder scale; reading drift or level here would repeat stage 2's "
                "error. Best attempt: " + json.dumps(ranked[0])
                if ranked
                else "none"
            ),
        }
        S.log("PHASE 2 SKIPPED — no setting passed its presence gate")
        flush()
        print("R12_STAGE2B_DONE", flush=True)
        return

    # Best passing point by spectrum flatness. Phase 2 measures it and, if the
    # sibling-crowding reading is right and octaves came from a lower frac, the
    # arm that matters is whether that same frac still holds the drift.
    best = sorted(passing, key=lambda r: r["gate"]["ks_uniform"])[0]
    smin_best, frac_best = best["smin"], best["frac"]
    fracs = [frac_best] + [f for f in FRACS if abs(f - frac_best) > 1e-9]
    S.log(f"PHASE 2 — full ladder at smin={smin_best:g}, fracs={fracs[:N_FULL_ARMS]}")

    cells: list[dict] = []
    names: dict[str, str] = {}
    arms: list[tuple[str, dict, tuple[int, ...]]] = [("ctrl", dict(DIAL), S2.CAND_SUBS)]
    for fr in fracs[:N_FULL_ARMS]:
        arms.append(
            (
                f"casc_f{fr:g}",
                DIAL
                | {
                    "cascade_frac": fr,
                    "cascade_smin": smin_best,
                    "cascade_alpha": ALPHA,
                },
                S2.CAND_SUBS,
            )
        )

    for tag, over, subs in arms:
        name = f"{tag}_" + "_".join(f"{k}{v:g}" for k, v in sorted(over.items()))
        names[tag] = name
        pb, pq = instance(over)
        g, _ = S2.gate_at_ladder(pb, n_max, 0, ref_r1)
        S.log(
            f"{name}: gate {g.get('octaves_spanned'):.2f}oct "
            f"ks={g.get('ks_uniform'):.3f} passed={g.get('passed')}"
        )
        saved = S.SUBS
        S.SUBS = subs
        try:
            rows = S.measure_counts(name, pb, pq)
        finally:
            S.SUBS = saved
        cells.extend({"overrides": over, "arm": tag} | r for r in rows)
        out["phase2"] = {
            "ran": True,
            "smin": smin_best,
            "cells": cells,
            "gates": out["phase2"].get("gates", {}) | {tag: g},
        }
        del pb, pq
        gc.collect()
        flush()

    ctrl = names["ctrl"]
    summary = {}
    for tag in names:
        s = S.summarize(cells, names[tag], ctrl, real)
        g1 = [c["g1_vs_real"] for c in s["cells"]]
        summary[tag] = {
            "dslope_g1": s["dslope_g1"],
            "g1_level_vs_real": round(sum(g1) / len(g1), 3) if g1 else None,
            "count_quiet": (
                None if tag == "ctrl" else S2.quietness(cells, names[tag], ctrl, "s_k")
            ),
        }
    out["phase2"]["summary"] = summary
    out["phase2"]["bound"] = 0.05
    flush()
    S.log(f"wrote {OUT}")
    print(json.dumps(summary, indent=2)[:1500], flush=True)
    print("R12_STAGE2B_DONE", flush=True)


if __name__ == "__main__":
    main()
