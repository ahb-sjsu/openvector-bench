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


def _poisson_pmf(lam: float, c: int) -> float:
    if lam <= 0:
        return 1.0 if c == 0 else 0.0
    return math.exp(-lam + c * math.log(lam) - math.lgamma(c + 1))


def tail_share(counts: np.ndarray, frac: float = 0.01) -> float:
    """Share of all retrieval slots captured by the busiest ``frac`` of points.

    The robust replacement for ``count_max``. A maximum over ``n_base`` sparse
    counts is an extreme-value draw, so at low occupancy it is mostly noise —
    which is exactly the regime the registered ladder's top cells sit in. A
    tail mass sums thousands of points instead of taking one, so its
    signal survives where the maximum's does not.
    """
    c = np.sort(np.asarray(counts, dtype=np.float64))[::-1]
    m = max(1, int(round(len(c) * frac)))
    total = c.sum()
    return float(c[:m].sum() / max(total, 1e-12))


def poisson_tail_share(lam: float, n_base: int, frac: float = 0.01) -> float:
    """``tail_share`` for a structureless Poisson corpus, computed exactly.

    Walks the Poisson tail from the top until ``frac * n_base`` points are
    accounted for, taking a partial share of the boundary count so the
    result is continuous in ``frac`` rather than stepping. No simulation, so
    no seed and no sampling noise in the reference.
    """
    if lam <= 0 or n_base <= 0:
        return 1.0
    m = max(1.0, n_base * frac)
    c_hi = max(1, int(lam + 12 * math.sqrt(lam) + 12))
    taken = 0.0
    mass = 0.0
    for c in range(c_hi, -1, -1):
        cnt = n_base * _poisson_pmf(lam, c)
        if taken + cnt >= m:
            mass += (m - taken) * c
            taken = m
            break
        taken += cnt
        mass += cnt * c
    return float(mass / max(n_base * lam, 1e-12))


def tail_excess(counts: np.ndarray, n_base: int, frac: float = 0.01) -> float:
    """Observed tail mass over the structureless expectation.

    1.0 means the busiest ``frac`` of points capture no more than chance
    gives them. Use in place of ``hub_excess`` wherever occupancy is low.
    """
    c = np.asarray(counts, dtype=np.float64)
    null = poisson_tail_share(float(c.mean()), n_base, frac)
    return float(tail_share(c, frac) / max(null, 1e-12))


def attractiveness_skew(counts: np.ndarray) -> float:
    """Skewness of the per-point ATTRACTIVENESS, with sampling noise removed.

    The budget-invariant form of G6, and the one the ladder needs.

    Model: a point's retrieval count is Poisson(rho * w) where ``w`` is its
    attractiveness under the query measure (mean 1 by construction) and
    ``rho`` is the budget. Then

        Var(c)  = rho + rho^2 Var(w)
        mu3(c)  = rho + 3 rho^2 Var(w) + rho^3 mu3(w)

    so both moments of ``w`` are recoverable, and ``skew(w)`` is a property
    of the corpus and the query measure alone.

    Raw ``s_k`` is not. It interpolates between the Poisson floor
    ``1/sqrt(rho)`` at low budget and ``skew(w)`` at high budget, so up a
    fixed-budget ladder it mixes structure with occupancy. Verified against
    a fixed corpus measured at rho in {0.5, 1, 2, 4}: raw ``s_k`` moves
    2.46 -> 5.59 while this estimator holds 10.02 -> 9.84 against a true
    9.85.

    An earlier attempt at ``s_k * sqrt(rho)`` is not invariant either — it
    over-corrects, moving 1.74 -> 11.19 on the same data — and was removed
    rather than shipped.

    Returns NaN when the counts carry no resolvable structure (the
    deconvolved variance is at or below the Poisson floor), which is the
    honest answer at very low occupancy rather than a large unstable number.
    """
    c = np.asarray(counts, dtype=np.float64)
    rho = float(c.mean())
    if rho <= 0:
        return float("nan")
    var_w = (float(c.var()) - rho) / rho**2
    if var_w <= 1e-9:
        return float("nan")
    mu3_w = (float(((c - rho) ** 3).mean()) - rho - 3 * rho**2 * var_w) / rho**3
    return float(mu3_w / var_w**1.5)


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
        "attractiveness_skew": attractiveness_skew(c),
        "tail_share_1pct": tail_share(c, 0.01),
        "tail_excess_1pct": tail_excess(c, n_base, 0.01),
        "rho": rho(n_query, k, n_base),
    }
