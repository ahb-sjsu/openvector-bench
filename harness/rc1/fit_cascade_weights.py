"""Fit `twoscale_gen.CASCADE_WEIGHTS` to `R30`'s measured index autocorrelation.

The corpus model is a trajectory whose components change at doubling rates::

    x(i) = sum_s w_s * v(s, i >> s) + w_glob * m

Two rows share the level-``s`` component iff ``i >> s == j >> s``, which happens
with probability ``max(0, 1 - gap / 2**s)``. So the cosine between rows at index
gap ``g`` is a non-negative combination of triangular kernels plus a constant,
and the level variances follow by NNLS.

**The fit is exact and that is not evidence.** Sixteen free non-negative
parameters against eight measured gaps interpolates by construction. Its purpose is to make the
autocorrelation real's *by design* so that G1, the ratio and the `PROFILE.md`
§3b spans become out-of-sample tests (`R32`).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import nnls

# R30, results/density_ordering.json: mean cosine by row gap, 600k rows.
GAPS = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=float)
RHO = np.array([0.5983, 0.5302, 0.4488, 0.3667, 0.3043, 0.2671, 0.2464, 0.2355])
RANDOM_BASELINE = 0.2279
N_LEVELS = 15


def fit(gaps=GAPS, rho=RHO, n_levels=N_LEVELS):
    """Return ``(level_variances, global_variance, fitted_rho)``."""
    lev = 2.0 ** np.arange(n_levels)
    kern = np.maximum(0.0, 1.0 - gaps[:, None] / lev[None, :])
    design = np.hstack([kern, np.ones((len(gaps), 1))])
    # Weight the sum-to-one constraint heavily so rho is a correlation.
    a, _ = nnls(np.vstack([design, np.full(n_levels + 1, 50.0)]), np.append(rho, 50.0))
    a = a / a.sum()
    return a[:-1], float(a[-1]), design @ a


def main() -> int:
    lev_var, glob_var, pred = fit()
    print("level variances (s -> component changes every 2**s rows):")
    for s, v in enumerate(lev_var):
        if v > 1e-4:
            print(f"  s={s:2d}  span {2 ** s:6d} rows   var {v:.4f}")
    print(
        f"  global                       var {glob_var:.4f}"
        f"   (random-pair baseline {RANDOM_BASELINE})"
    )
    print("\ngap   measured   fitted")
    for g, r, p in zip(GAPS, RHO, pred):
        print(f"{int(g):4d}   {r:.4f}     {p:.4f}")
    print(
        f"\nrms {np.sqrt(((RHO - pred) ** 2).mean()):.6f}  "
        f"(exact by construction: {len(lev_var) + 1} params, {len(GAPS)} gaps)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
