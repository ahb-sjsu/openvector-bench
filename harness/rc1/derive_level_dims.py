"""Invert a measured s(r) into per-level dimensions — and show why it fails.

Blum, Hopcroft & Kannan §2.3 gives near-orthogonality of independent components
in high dimension, so squared distances add; §2.4.1 gives volume growing as
``r^d``. For the index cascade of `R32`, rows differing in levels 0..L sit at
radius ``R(L) = sqrt(2 * sum_{l<=L} w_l^2)`` and their difference spans the sum
of those levels' subspaces, which appears to give

    s(R(L)) = sum_{l<=L} d_l

and hence a per-level schedule by inversion — apparently decoupling the weights
(fixed by the autocorrelation) from the dimensions (fixed by s(r)).

**This is wrong, and `R33` measured it wrong.** The neighbour count is not free:
the rows within index gap ``2^L`` number exactly ``2^L``, so

    s = dlog k / dlog r = ln 2 / ln( R(L+1) / R(L) )

depends on the **weights alone**. Subspace dimension only sets spread within a
level. Four schedules spanning a 6x range in d_3 moved s(4) by 3 units and the
ratio not at all. The Gaussian Annulus Theorem is why: each level's distance
contribution is concentrated in a thin shell, so a level acts as a near-discrete
radius step rather than a d_l-dimensional volume to fill.

This script prints both quantities so the discrepancy is reproducible.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

from openvector_bench.twoscale_gen import CASCADE_WEIGHTS

SCURVES = os.environ.get("DLD_SCURVES", "results/scurves.json")
ARM = os.environ.get("DLD_ARM", "real_b100")


def main() -> int:
    w2 = np.asarray(CASCADE_WEIGHTS, dtype=float)
    radius = np.sqrt(2 * np.cumsum(w2))

    print("L   R(L)     s implied by WEIGHTS alone (ln2 / ln(R[L+1]/R[L]))")
    for level in range(len(radius) - 1):
        s = np.log(2) / np.log(radius[level + 1] / radius[level])
        print(f"{level}   {radius[level]:.4f}   {s:6.2f}")

    if not os.path.exists(SCURVES):
        print(f"\n{SCURVES} not found; skipping the inversion", file=sys.stderr)
        return 0
    d = json.load(open(SCURVES, encoding="utf-8"))[ARM]
    rr, ss = np.asarray(d["r"]), np.asarray(d["s"])
    cum = np.interp(radius, rr, ss)
    per = np.diff(np.concatenate([[0.0], cum]))
    print(f"\ninversion against {ARM} (r spans {rr[0]:.4f}..{rr[-1]:.4f})")
    print("  L  R(L)     in-range  cumulative D   per-level d_L")
    for level in range(len(radius)):
        inside = rr[0] <= radius[level] <= rr[-1]
        print(f"  {level}  {radius[level]:.4f}   {str(inside):5s}     "
              f"{cum[level]:7.2f}       {per[level]:7.2f}")
    print("\nMeasured cascade s(k) is ~17-20 for every schedule (R33), so the")
    print("inversion above does not predict the built geometry. The weight-only")
    print("column does.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
