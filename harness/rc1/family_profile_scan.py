"""Does ANY registered family have headroom on the profile? Scan before searching.

`spec/PROFILE.md` is registered and `make_evaluate_fn` can now price it. The
next step in `GENERATOR_SEARCH.md` §7 is to point a searcher at that fitness —
but a search is only worth its compute if some family can plausibly reach the
target. Six families are closed on mechanism, and `R25_ANISOTROPY_CONTROLS.md`
adds a stronger a-priori exclusion: the ramp is carried by structure beyond the
first two moments, so any family whose geometry is determined by its covariance
cannot express it however its knobs are set.

This scans every registered family at its **default** parameters and reports
where each sits relative to the registered band. It is a reconnaissance run,
not a search: defaults are not optimised, so a family scoring badly here is not
thereby refuted. What the scan can establish is the opposite and more useful
thing — whether every family sits so far outside the band, and in the same
direction, that a parameter search has nowhere to go.

Reading:

* **Some family within a few sd of +0.451** -> a search is justified; start
  there.
* **All families clustered near or below zero trend** -> the gap is
  mechanistic, not parametric, and searching the existing families would burn
  compute confirming what R21-R25 already established.

Deliberately small (dim 256, modest rungs) — this ranks families, it does not
measure them at registered scale. Run locally to keep Atlas free.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench import generator_search as G  # noqa: E402
from openvector_bench.geometry import knn, profile_ratio  # noqa: E402
from openvector_bench.geometry import PROFILE_KGRID  # noqa: E402

DIM = int(os.environ.get("FS_DIM", "256"))
NS = json.loads(os.environ.get("FS_NS", "[6000, 12000, 24000]"))
NQ = int(os.environ.get("FS_NQ", "2000"))
OUT = os.environ.get("FS_OUT", "family_profile_scan.json")
SEED = 7

FAMILIES = [
    ("round8_synth", G.PARAMS, G.synth_corpus),
    ("manifold", G.MANIFOLD_PARAMS, G.manifold_corpus),
    ("concentration", G.CONCENTRATION_PARAMS, G.concentration_corpus),
    ("stratified", G.STRATIFIED_PARAMS, G.stratified_corpus),
    ("hier_concentration", G.HIER_PARAMS, G.hier_concentration_corpus),
    ("hier_coloured", G.HIER_COLOURED_PARAMS, G.hier_coloured_corpus),
    ("hier_multiscale", G.HIER_MS_PARAMS, G.hier_multiscale_corpus),
    ("hier_query", G.HIER_QUERY_PARAMS, G.hier_query_corpus),
    ("hier_dupq", G.HIER_DUPQ_PARAMS, G.hier_dupq_corpus),
    ("hier_lc", G.HIER_LC_PARAMS, G.hier_lc_corpus),
]

TREND = G.PROFILE_TARGET["ratio_trend"]
TREND_SD = G.PROFILE_TARGET["ratio_trend_sd"]


def scan(name, spec, gen) -> dict:
    p = G.decode(np.array([]), spec)  # all defaults
    nmax = max(NS)
    t0 = time.time()
    full = gen(p, nmax + NQ, DIM, SEED)
    q = full[nmax:]
    ratios = []
    for n in NS:
        rng = np.random.default_rng(SEED + n)
        bi = rng.choice(nmax, size=n, replace=False)
        d, _ = knn(full[bi], q, max(PROFILE_KGRID))
        ratios.append(profile_ratio(d))
    trend = float(np.polyfit(np.log(NS), ratios, 1)[0])
    z = (trend - TREND) / TREND_SD
    return {"ratios": [round(r, 3) for r in ratios], "trend": trend,
            "z": float(z), "seconds": time.time() - t0}


def main() -> int:
    print(f"dim={DIM} rungs={NS} nq={NQ}", flush=True)
    print(f"registered target: trend {TREND:+.3f} +/- {TREND_SD:.3f} "
          f"(band [{TREND-2*TREND_SD:+.3f}, {TREND+2*TREND_SD:+.3f}])\n", flush=True)
    out = {}
    for name, spec, gen in FAMILIES:
        try:
            r = scan(name, spec, gen)
            out[name] = r
            print(f"{name:20s} ratios {str(r['ratios']):22s} trend {r['trend']:+.3f} "
                  f"z {r['z']:+7.2f}  ({r['seconds']:.0f}s)", flush=True)
        except Exception as e:
            out[name] = {"error": f"{type(e).__name__}: {e}"}
            print(f"{name:20s} FAILED {type(e).__name__}: {e}", flush=True)

    ok = {k: v for k, v in out.items() if "error" not in v}
    if ok:
        best = min(ok.items(), key=lambda kv: abs(kv[1]["z"]))
        print(f"\nclosest family: {best[0]} at z {best[1]['z']:+.2f}", flush=True)
        rising = [k for k, v in ok.items() if v["trend"] > 0.1]
        print(f"families with a meaningfully rising profile: {rising or 'NONE'}",
              flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"config": {"dim": DIM, "ns": NS, "nq": NQ, "seed": SEED,
                              "target_trend": TREND, "target_sd": TREND_SD},
                   "families": out}, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("FAMILY_SCAN_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
