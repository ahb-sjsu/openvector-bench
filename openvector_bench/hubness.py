# openvector-bench
# MIT License

"""Query-budget-invariant hubness statistics.

Retrieval counts depend on three things at once: how concentrated the corpus
is, how many queries were spent, and how many points those queries were
spread over. Raw counts and raw count maxima mix all three, so a target
stated in them is meaningless without its measurement convention attached,
and two runs that differ only in query budget will disagree.

Measured on the real Cohere corpus 2026-08-07
(`results/R13_PROTOCOL_CHECK.md`): the raw count-maximum slope across the
ladder reverses sign between a fixed query budget and a budget scaled with
n, purely because the budget term moves. Worse, at the top of the registered
ladder the raw maximum is close to what pure chance produces — real's
`count_max` at k = 10, n = 200,000 is only 1.57x the Poisson null.

Two reductions fix this, and both are cheap:

``share``   count_max / (nq * k) — invariant to how many queries were spent,
            so it can be compared across budgets. Still contains the null
            ceiling.
``excess``  count_max / null_max — how far above pure chance the top hub
            sits. This is the only form that isolates hub STRUCTURE, because
            the null ceiling itself falls as the corpus grows at fixed
            occupancy, and that fall is otherwise attributed to the corpus.

For the round-11 real reference the decomposition at k = 10 is: raw slope
-0.73/decade, of which -0.41 is the null ceiling and -0.32 is genuine hub
structure. Roughly half of the apparent thinning was the null moving.
"""

from __future__ import annotations

import math

import numpy as np


def rho(n_query: int, k: int, n_base: int) -> float:
    """Retrieval slots per point. The measurement's budget parameter.

    Any statistic compared across a varying ``n_base`` must either hold this
    constant or be expressed in a rho-invariant form.
    """
    return n_query * k / max(n_base, 1)


def hub_share(count_max: float, n_query: int, k: int) -> float:
    """Fraction of all retrieval slots captured by the single busiest point."""
    return float(count_max) / max(n_query * k, 1)


def _poisson_sf(lam: float, x: int) -> float:
    """P(X >= x) for Poisson(lam), summed in log space for small lam."""
    if x <= 0:
        return 1.0
    s = 0.0
    for i in range(x):
        s += math.exp(-lam + i * math.log(lam + 1e-300) - math.lgamma(i + 1))
    return max(0.0, 1.0 - s)


def poisson_null_max(lam: float, n_base: int, cap: int = 100_000) -> int:
    """Count the busiest point would reach with NO hub structure at all.

    The largest ``c`` such that at least one of ``n_base`` independent
    Poisson(``lam``) points is expected to reach it. This is a ceiling that
    moves on its own as the ladder changes: at fixed occupancy a bigger
    corpus gives chance more chances, but falling occupancy lowers it
    faster, so it declines up the ladder and drags raw maxima with it.
    """
    if lam <= 0 or n_base <= 0:
        return 0
    c = 1
    while c < cap and n_base * _poisson_sf(lam, c) >= 1.0:
        c += 1
    return c - 1


def hub_excess(count_max: float, count_mean: float, n_base: int) -> float:
    """Ratio of the observed busiest count to the no-structure ceiling.

    1.0 means the busiest point is no busier than chance would make it;
    values above 1 are hub structure. Use this, not ``hub_share``, whenever
    the claim is about the corpus rather than about a workload.
    """
    nm = poisson_null_max(count_mean, n_base)
    return float(count_max) / max(nm, 1)


def count_stats(idx: np.ndarray, n_base: int, k: int, n_query: int) -> dict:
    """All four forms for one measured cell, so callers cannot pick one by
    accident: raw for continuity, share for budget invariance, excess for
    structure, plus the budget itself so any number can be re-derived."""
    c = np.bincount(idx[:, :k].ravel(), minlength=n_base).astype(np.float64)
    s = c.std()
    cmax, cmean = float(c.max()), float(c.mean())
    return {
        "count_max": cmax,
        "count_mean": cmean,
        "s_k": float(((c - c.mean()) ** 3).mean() / max(s**3, 1e-12)),
        "zero_frac": float((c == 0).mean()),
        "hub_share": hub_share(cmax, n_query, k),
        "null_max": poisson_null_max(cmean, n_base),
        "hub_excess": hub_excess(cmax, cmean, n_base),
        "rho": rho(n_query, k, n_base),
    }
