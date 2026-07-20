# OpenVector Bench — MIT License
"""Score the RC-1 battery against the registered admission rule.

Applies PREREG_RC1 v2 §5 exactly: per-diagnostic equivalence tests (the 95%
subsampling interval of the ratio must lie *inside* the band — a point
estimate inside with an interval crossing it is a FAIL), the mandatory gates
G1/G5/G6, and the "all but two" count. Also reports, per §8, which nulls each
gate separates, because a gate that separates nothing is informative about
the battery rather than grounds for silently deleting it.

At this stage there is no fitted generator, so the candidates are the three
frozen nulls. The registered expectation is that **none of them satisfies the
admission rule**; a null that did would mean the battery is insufficient.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict

import numpy as np

GATES = {
    "g1_id_twonn": (0.85, 1.15, True),
    "g2_id_ballgrowth": (0.80, 1.20, False),
    "g3_eff_rank": (0.85, 1.15, False),
    "g4_dims90": (0.85, 1.15, False),
    "g5_relative_contrast": (0.85, 1.15, True),
    "g6_hubness_skew": (0.85, 1.15, True),
    "g7_local_id_iqr": (0.80, 1.20, False),
    "g8_pca_retention": (0.85, 1.15, False),
}
BOOT = 10000


def ratio_ci(cand: list[float], ref: list[float], seed: int = 0):
    """Percentile-bootstrap interval for the ratio of means.

    Resamples subsamples, which is what we have: the draws are overlapping
    subsamples of one corpus, so this is a subsampling interval and is
    labelled as such — not independent replication.
    """
    c, r = np.asarray(cand, float), np.asarray(ref, float)
    c, r = c[np.isfinite(c)], r[np.isfinite(r)]
    if len(c) == 0 or len(r) == 0 or abs(r.mean()) < 1e-12:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = np.array(
        [
            rng.choice(c, len(c), replace=True).mean()
            / max(rng.choice(r, len(r), replace=True).mean(), 1e-12)
            for _ in range(BOOT)
        ]
    )
    return float(c.mean() / r.mean()), *np.percentile(draws, [2.5, 97.5])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cells", help="rc1_cells.json")
    ap.add_argument("--out", default="rc1_scores.json")
    a = ap.parse_args()

    cells = json.load(open(a.cells, encoding="utf-8"))
    # (corpus, battery, n, k) -> {gate: [values across subsamples]}
    grouped: dict = defaultdict(lambda: defaultdict(list))
    for c in cells:
        key = (c["corpus"], c["battery"], c["n"], c["k"])
        for g in GATES:
            grouped[key][g].append(c[g])

    corpora = sorted({k[0] for k in grouped} - {"real"})
    batteries = sorted({k[1] for k in grouped})
    report: dict = {"candidates": {}, "gate_discrimination": {}}

    for cand in corpora:
        cells_pass, cells_total = 0, 0
        mandatory_fail: list[str] = []
        per_gate_pass: dict = defaultdict(lambda: [0, 0])
        detail = []
        for (corpus, battery, n, k), vals in sorted(grouped.items()):
            if corpus != cand:
                continue
            ref = grouped.get(("real", battery, n, k))
            if ref is None:
                continue
            cells_total += 1
            passed, results = 0, {}
            for g, (lo, hi, mandatory) in GATES.items():
                r, clo, chi = ratio_ci(vals[g], ref[g])
                ok = bool(np.isfinite(clo) and clo >= lo and chi <= hi)
                results[g] = {
                    "ratio": None if not np.isfinite(r) else round(r, 4),
                    "ci": [None, None]
                    if not np.isfinite(clo)
                    else [round(clo, 4), round(chi, 4)],
                    "pass": ok,
                }
                per_gate_pass[g][0] += int(ok)
                per_gate_pass[g][1] += 1
                if ok:
                    passed += 1
                elif mandatory:
                    mandatory_fail.append(f"{g}@{battery}/n={n}/k={k}")
            if passed >= len(GATES) - 2:
                cells_pass += 1
            detail.append(
                {"battery": battery, "n": n, "k": k, "gates_passed": passed,
                 "results": results}
            )
        # PREREG v2 §5: mandatory gates in EVERY cell, "all but two" in >=10/12
        admitted = (not mandatory_fail) and cells_pass >= max(
            1, int(round(cells_total * 10 / 12))
        )
        report["candidates"][cand] = {
            "admitted": admitted,
            "cells_meeting_count_rule": f"{cells_pass}/{cells_total}",
            "mandatory_gate_failures": len(mandatory_fail),
            "example_mandatory_failures": mandatory_fail[:5],
            "detail": detail,
        }
        print(
            f"{cand:16s} admitted={admitted!s:5s} "
            f"count-rule {cells_pass}/{cells_total} "
            f"mandatory-failures {len(mandatory_fail)}",
            flush=True,
        )

    # §8: which nulls does each gate separate?
    for g in GATES:
        sep = []
        for cand in corpora:
            d = report["candidates"][cand]["detail"]
            fails = sum(1 for c in d if not c["results"][g]["pass"])
            if fails > len(d) / 2:
                sep.append(cand)
        report["gate_discrimination"][g] = sep
        print(f"  {g:22s} separates: {sep or 'NONE'}", flush=True)

    any_null_admitted = any(v["admitted"] for v in report["candidates"].values())
    report["battery_sufficient"] = not any_null_admitted
    print(
        "\nregistered expectation (no frozen null admitted): "
        f"{'MET' if not any_null_admitted else 'VIOLATED'}",
        flush=True,
    )
    json.dump(report, open(a.out, "w", encoding="utf-8"), indent=2)
    print(f"wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
