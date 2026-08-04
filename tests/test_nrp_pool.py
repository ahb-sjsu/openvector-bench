"""PoolRunner state machine, exercised with fake cluster + submitter.

Every scenario here is a measured incident from the 1T fleet run the runner
was distilled from: API blips must change nothing, NotFound needs two-poll
confirmation, wedged jobs recycle on the age bound, attach-stuck items park
after three strikes instead of blocking the pool.
"""

from __future__ import annotations

from openvector_bench.nrp_pool import PoolRunner


class FakeCluster:
    """In-memory job store standing in for kubectl + burst.submit."""

    def __init__(self):
        self.jobs: dict[str, dict] = {}
        self.submits: list[str] = []
        self.deletes: list[str] = []
        self.pods: dict[str, str] = {}  # job name -> pod phase
        self.blip = False

    def kubectl(self, *args):
        if self.blip:
            return None
        if args[:2] == ("get", "jobs"):
            return {
                "items": [
                    {"metadata": {"name": n}, "status": s} for n, s in self.jobs.items()
                ]
            }
        if args[:2] == ("get", "pods"):
            name = args[3].split("=", 1)[1]
            ph = self.pods.get(name)
            return {"items": [{"status": {"phase": ph}}] if ph else []}
        raise AssertionError(f"unexpected kubectl {args}")

    def submit(self, item):
        name = f"job-{item}"
        self.jobs[name] = {"active": 1}
        self.submits.append(name)

    def delete(self, name):
        self.jobs.pop(name, None)
        self.deletes.append(name)


def make_runner(cluster, items, tmp_path, **kw):
    t = {"now": 0.0}
    kw.setdefault("maxpar", 2)
    runner = PoolRunner(
        items,
        job_name=lambda i: f"job-{i}",
        submit=cluster.submit,
        state_path=str(tmp_path / "state.json"),
        kubectl=cluster.kubectl,
        delete_job=cluster.delete,
        clock=lambda: t["now"],
        log=lambda m: None,
        **kw,
    )
    return runner, t


def test_pool_respects_maxpar_and_drains(tmp_path):
    c = FakeCluster()
    r, _ = make_runner(c, [1, 2, 3], tmp_path, maxpar=2)
    r.poll()
    assert len(c.submits) == 2  # slot cap, third waits
    c.jobs["job-1"] = {"succeeded": 1}
    r.poll()
    assert "job-1" in r.done and len(c.submits) == 3  # freed slot refills
    c.jobs["job-2"] = {"succeeded": 1}
    c.jobs["job-3"] = {"succeeded": 1}
    r.poll()
    assert r.done == {"job-1", "job-2", "job-3"} and not r.active and not r.pool


def test_api_blip_changes_nothing(tmp_path):
    c = FakeCluster()
    r, _ = make_runner(c, [1], tmp_path)
    r.poll()
    c.blip = True
    r.poll()
    r.poll()
    assert c.deletes == [] and len(c.submits) == 1  # nothing recycled on blips


def test_notfound_needs_two_polls(tmp_path):
    c = FakeCluster()
    r, _ = make_runner(c, [1], tmp_path)
    r.poll()
    del c.jobs["job-1"]  # swept
    r.poll()
    assert c.deletes == []  # first sighting: not yet
    r.poll()
    assert len(c.submits) == 2  # confirmed on the second: resubmitted


def test_failed_job_recycles_with_retry_count(tmp_path):
    c = FakeCluster()
    r, _ = make_runner(c, [1], tmp_path, maxtries=2)
    r.poll()
    c.jobs["job-1"] = {"failed": 1}
    r.poll()
    assert r.active["job-1"]["tries"] == 2
    c.jobs["job-1"] = {"failed": 1}
    r.poll()
    assert "job-1" in r.parked and not r.active  # budget exhausted -> parked


def test_wedge_bound_recycles_old_active_job(tmp_path):
    c = FakeCluster()
    r, t = make_runner(c, [1], tmp_path, wedge_s=100)
    r.poll()
    c.pods["job-1"] = "Running"
    t["now"] = 101
    r.poll()
    assert c.deletes == ["job-1"] and len(c.submits) == 2


def test_attach_stuck_parks_after_three_strikes(tmp_path):
    c = FakeCluster()
    r, t = make_runner(c, [1, 2], tmp_path, maxpar=1, pend_s=10, stuckvol_after=3)
    r.poll()
    for i in range(3):
        t["now"] += 20  # past pend bound, pod never Running
        r.poll()
    assert "job-1" in r.parked
    r.poll()
    assert "job-2" in c.jobs  # the pool moved on to the next item


def test_state_survives_restart_and_adopts_running(tmp_path):
    c = FakeCluster()
    r, _ = make_runner(c, [1, 2], tmp_path, maxpar=2)
    r.poll()
    c.jobs["job-1"] = {"succeeded": 1}
    r.poll()
    # New runner over the same state: done stays done, running is adopted.
    r2, _ = make_runner(c, [1, 2], tmp_path, maxpar=2)
    r2.poll()
    assert "job-1" in r2.done
    assert "job-2" in r2.active
    assert c.submits.count("job-2") == 1  # adopted, not duplicated
