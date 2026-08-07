"""Budget-invariant hubness statistics.

The properties asserted here are the ones the campaign's count targets
turned out to lack: invariance to query budget, and separation of hub
structure from the null ceiling.
"""

from __future__ import annotations

import numpy as np

from openvector_bench.hubness import (
    count_stats,
    hub_excess,
    hub_share,
    poisson_null_max,
    rho,
)


def test_share_is_invariant_to_query_budget():
    # Same corpus concentration, twice the queries: raw maxima double, share
    # does not. This is the property raw count_max lacks.
    assert hub_share(40, 1000, 10) == hub_share(80, 2000, 10)
    assert rho(1000, 10, 25000) == rho(2000, 10, 50000)


def test_null_max_rises_with_corpus_and_occupancy():
    # More points, more chances for a big count.
    assert poisson_null_max(1.0, 1_000_000) > poisson_null_max(1.0, 1_000)
    # More slots per point, higher ceiling.
    assert poisson_null_max(4.0, 25_000) > poisson_null_max(0.5, 25_000)


def test_null_max_falls_up_a_fixed_budget_ladder():
    # The ladder's own confound: with a fixed query budget, occupancy falls
    # as 1/n and the ceiling falls with it despite n growing. Any raw-count
    # slope read across such a ladder inherits this.
    nq, k = 10_000, 10
    ceilings = [poisson_null_max(nq * k / n, n) for n in (25_000, 200_000)]
    assert ceilings[0] > ceilings[1]


def test_excess_is_one_for_structureless_counts():
    # A Poisson corpus has no hubs: its busiest point should sit at the
    # ceiling, not above it.
    rng = np.random.default_rng(0)
    n, lam = 50_000, 2.0
    c = rng.poisson(lam, size=n)
    e = hub_excess(c.max(), c.mean(), n)
    assert 0.7 <= e <= 1.4, e


def test_excess_detects_planted_hubs_that_share_can_miss():
    rng = np.random.default_rng(1)
    n, lam = 50_000, 2.0
    c = rng.poisson(lam, size=n)
    c[0] = int(c.max() * 4)  # one genuine hub
    assert hub_excess(c[0], c.mean(), n) > 3.0


def test_count_stats_reports_every_form(tmp_path):
    # idx: 500 queries x k=10 drawn over 2000 points, one point over-picked.
    rng = np.random.default_rng(2)
    idx = rng.integers(0, 2000, size=(500, 10))
    idx[:100, 0] = 7  # point 7 is a hub
    st = count_stats(idx, 2000, 10, 500)
    for key in (
        "count_max",
        "count_mean",
        "s_k",
        "zero_frac",
        "hub_share",
        "null_max",
        "hub_excess",
        "rho",
    ):
        assert key in st
    assert st["rho"] == 500 * 10 / 2000
    assert st["hub_excess"] > 1.5  # the planted hub is visible above chance
    assert abs(st["count_mean"] - 500 * 10 / 2000) < 1e-9
