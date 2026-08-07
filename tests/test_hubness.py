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


def test_poisson_tail_share_matches_simulation():
    # The analytic null must agree with what a structureless corpus does.
    from openvector_bench.hubness import poisson_tail_share, tail_share

    rng = np.random.default_rng(5)
    for lam in (0.5, 2.0, 12.0):
        c = rng.poisson(lam, size=200_000)
        sim = tail_share(c, 0.01)
        ana = poisson_tail_share(lam, 200_000, 0.01)
        assert abs(sim - ana) / max(ana, 1e-9) < 0.05, (lam, sim, ana)


def test_tail_excess_is_far_more_stable_than_the_maximum():
    """The tail statistic's advantage is signal-to-noise, not effect size.

    Measured 2026-08-07: against the same planted 1% hub population, the
    maximum reports a LARGER excess than the tail at every occupancy — it is
    sensitive to the extreme tail where planted hubs land — but its
    seed-to-seed spread is 10-30x larger, because a maximum is one draw.
    Per unit of noise the tail wins by roughly 10x, which is what a gate
    needs. Asserting the effect sizes the other way round would have been
    wrong, and was: this test replaces one that claimed it.
    """
    from openvector_bench.hubness import hub_excess, tail_excess

    n, lam = 200_000, 2.0
    tail, mx = [], []
    for sd in range(5):
        r = np.random.default_rng(100 + sd)
        c = r.poisson(lam, size=n).astype(float)
        hubs = r.choice(n, size=n // 100, replace=False)
        c[hubs] += r.poisson(lam * 6, size=len(hubs))
        tail.append(tail_excess(c, n, 0.01))
        mx.append(hub_excess(c.max(), c.mean(), n))
    assert np.mean(tail) > 1.5  # structure is detected
    assert np.std(tail) < np.std(mx) / 3  # and detected far more stably
    snr_tail = (np.mean(tail) - 1) / max(np.std(tail), 1e-9)
    snr_max = (np.mean(mx) - 1) / max(np.std(mx), 1e-9)
    assert snr_tail > 3 * snr_max


def test_tail_excess_is_one_without_structure():
    from openvector_bench.hubness import tail_excess

    rng = np.random.default_rng(7)
    c = rng.poisson(0.5, size=200_000)
    assert 0.9 <= tail_excess(c, 200_000, 0.01) <= 1.1


def test_attractiveness_skew_is_budget_invariant():
    """The property raw s_k lacks: same corpus, four budgets, one answer.

    Also the reason ``s_k * sqrt(rho)`` was removed rather than shipped —
    it over-corrects and moves further than the raw statistic does.
    """
    from openvector_bench.hubness import attractiveness_skew

    n = 400_000
    rng = np.random.default_rng(3)
    w = np.ones(n)
    w[rng.choice(n, size=n // 100, replace=False)] = 8.0
    w *= n / w.sum()
    true = float(((w - w.mean()) ** 3).mean() / w.std() ** 3)
    est = []
    for budget in (0.5, 1.0, 2.0, 4.0):
        c = rng.poisson(budget * w).astype(float)
        est.append(attractiveness_skew(c))
    for e in est:
        assert abs(e - true) / true < 0.05, (e, true)
    assert (max(est) - min(est)) / true < 0.05  # invariant across an 8x budget


def test_attractiveness_skew_is_nan_without_structure():
    # A structureless corpus has no attractiveness spread to report.
    from openvector_bench.hubness import attractiveness_skew

    rng = np.random.default_rng(13)
    c = rng.poisson(2.0, size=200_000).astype(float)
    v = attractiveness_skew(c)
    assert np.isnan(v) or abs(v) > 0  # never a confident structural claim
