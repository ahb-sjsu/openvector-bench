# openvector-bench
# MIT License

"""Pool runner for NRP batch work: independent tasks, no wave barrier.

The scheduling model that carried the turboquant-pro 1T fleet (2026-08-04),
generalized. A pool of items runs at most ``maxpar`` Jobs at once; each item
retries independently, so one stuck volume or slow node idles a single slot
instead of blocking a wave — measured on that run: a wave barrier let one
offline-node volume hold seven finished servers hostage for 5.5 h.

Submissions go through the ``burst.submit`` NATS flow (the resident
nats-bursting controller applies the politeness layer); job state is
read-only ``kubectl get``; recycling deletes the Job and resubmits. Both
side effects are injectable, so the state machine is unit-testable with no
cluster.

Failure handling, each clause paid for by a measured incident:

- ``NotFound`` is confirmed across two polls with the API reachable before
  a job is treated as vanished — one API blip once got a healthy wave of
  eight deleted.
- A job Active beyond ``wedge_s`` recycles: a worker sat wedged at its
  memory ceiling for 7 h making zero progress; content-addressed resume
  makes the recycle cost minutes.
- A job with no Running pod for ``pend_s`` recycles (transient attach
  hangs); after ``stuckvol_after`` consecutive such recycles the item is
  PARKED with a ``STUCKVOL`` line and the pool moves on — the volume-level
  fix (delete + reprovision + regenerate from seed) is deliberately left to
  a human because it destroys a volume.
- An unparsable/failed kubectl cycle changes NOTHING (``NOTE`` line only).

State (done/parked) checkpoints to a JSON file after every transition, so
the runner itself restarts cleanly and adopts still-running jobs.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Callable

DEFAULT_NS = "ssu-atlas-ai"


def _kubectl_json(ns: str, *args: str):
    r = subprocess.run(
        ["kubectl", "-n", ns, *args, "-o", "json"], capture_output=True, text=True
    )
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def nats_submitter(
    descriptor_factory: Callable[[object], object], ns: str = DEFAULT_NS
):
    """Return a ``submit(item)`` using the resident nats-bursting client.

    Imported lazily so the package (and CI) never needs the Atlas-local
    ``nats_bursting`` checkout; one short-lived connection per submit, since
    a pool run lasts days and a held-open transport dies on the first blip.
    """
    import sys

    sys.path.insert(0, "/home/claude/src/nats-bursting/python")
    from nats_bursting import Client

    def submit(item):
        with Client() as client:
            return client.submit(descriptor_factory(item))

    return submit


class PoolRunner:
    def __init__(
        self,
        items: list,
        *,
        job_name: Callable[[object], str],
        submit: Callable[[object], object],
        state_path: str,
        ns: str = DEFAULT_NS,
        maxpar: int = 8,
        maxtries: int = 1000,
        wedge_s: int = 28_800,  # 5h recycled healthy slow-node runs; measured 2026-08-05
        pend_s: int = 2_700,
        stuckvol_after: int = 3,
        poll_s: int = 60,
        kubectl=None,
        delete_job: Callable[[str], None] | None = None,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], None] | None = None,
    ):
        self.items = {job_name(i): i for i in items}
        self.pool = [job_name(i) for i in items]
        self.job_name = job_name
        self.submit = submit
        self.state_path = state_path
        self.ns = ns
        self.maxpar = maxpar
        self.maxtries = maxtries
        self.wedge_s = wedge_s
        self.pend_s = pend_s
        self.stuckvol_after = stuckvol_after
        self.poll_s = poll_s
        self.kubectl = kubectl or (lambda *a: _kubectl_json(self.ns, *a))
        self.delete_job = delete_job or self._delete_job_kubectl
        self.clock = clock
        self._log = log or (
            lambda m: print(
                f"=== {time.strftime('%H:%M', time.gmtime())} {m}", flush=True
            )
        )
        self.done: set[str] = set()
        self.parked: set[str] = set()
        self.active: dict[str, dict] = {}
        self._load()

    # -- persistence ------------------------------------------------------ #
    def _load(self) -> None:
        if os.path.exists(self.state_path):
            with open(self.state_path, encoding="utf-8") as f:
                st = json.load(f)
            self.done = set(st.get("done", []))
            self.parked = set(st.get("parked", []))
            self.pool = [n for n in self.pool if n not in self.done]
            self._log(f"STATE loaded: {len(self.done)} done, {len(self.parked)} parked")

    def _save(self) -> None:
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"done": sorted(self.done), "parked": sorted(self.parked)}, f)
        os.replace(tmp, self.state_path)

    # -- side effects ------------------------------------------------------ #
    def _delete_job_kubectl(self, name: str) -> None:
        subprocess.run(
            [
                "kubectl",
                "-n",
                self.ns,
                "delete",
                "job",
                name,
                "--ignore-not-found",
                "--wait=false",
            ],
            capture_output=True,
        )

    def _submit(self, name: str, tries: int) -> None:
        self.submit(self.items[name])
        prev = self.active.get(name, {})
        self.active[name] = {
            "t0": self.clock(),
            "tries": tries,
            "notfound": 0,
            "pendfails": prev.get("pendfails", 0),
        }
        self._log(f"SUBMIT {name} try {tries}/{self.maxtries}")

    def _recycle(self, name: str, why: str) -> None:
        st = self.active[name]
        if st["tries"] >= self.maxtries:
            self._log(f"GAVE UP {name} after {self.maxtries} tries")
            self.parked.add(name)
            del self.active[name]
            self._save()
            return
        self._log(f"RECYCLE {name}: {why}")
        self.delete_job(name)
        self._submit(name, st["tries"] + 1)

    # -- one poll cycle ---------------------------------------------------- #
    def poll(self) -> None:
        jobs = self.kubectl("get", "jobs")
        if jobs is None:
            self._log("NOTE kubectl unclear, skipping cycle")
            return
        by_name = {j["metadata"]["name"]: j for j in jobs.get("items", [])}

        for name in list(self.active):
            st = self.active[name]
            j = by_name.get(name)
            if j is None:
                st["notfound"] += 1
                if st["notfound"] >= 2:
                    self._recycle(name, "job vanished (confirmed)")
                continue
            st["notfound"] = 0
            status = j.get("status", {})
            if status.get("succeeded"):
                self._log(f"DONE {name}")
                self.done.add(name)
                del self.active[name]
                self._save()
                continue
            if status.get("failed"):
                self._recycle(name, "job failed")
                continue
            age = self.clock() - st["t0"]
            if age > self.wedge_s:
                self._recycle(name, f"active {int(age / 3600)}h > wedge bound")
                continue
            if age > self.pend_s:
                pods = self.kubectl("get", "pods", "-l", f"job-name={name}")
                running = any(
                    p["status"].get("phase") == "Running"
                    for p in (pods or {"items": []})["items"]
                )
                if not running:
                    st["pendfails"] = st.get("pendfails", 0) + 1
                    if st["pendfails"] >= self.stuckvol_after:
                        self._log(
                            f"STUCKVOL {name}: {st['pendfails']} consecutive "
                            "no-Running recycles — parked for human volume repair"
                        )
                        self.parked.add(name)
                        self.delete_job(name)
                        del self.active[name]
                        self._save()
                    else:
                        self._recycle(name, "no Running pod past pend bound")

        while len(self.active) < self.maxpar and self.pool:
            name = self.pool.pop(0)
            j = by_name.get(name)
            if j and j.get("status", {}).get("succeeded"):
                self._log(f"DONE {name} (pre-existing)")
                self.done.add(name)
                self._save()
                continue
            if j:
                self.active[name] = {"t0": self.clock(), "tries": 1, "notfound": 0}
                self._log(f"ADOPT {name} (job already exists)")
                continue
            self._submit(name, 1)

    def run(self) -> bool:
        """Poll until the pool drains. True iff nothing ended up parked."""
        self._log(f"POOL start: {len(self.pool)} to run, maxpar={self.maxpar}")
        while self.pool or self.active:
            self.poll()
            time.sleep(self.poll_s)
        self._log(f"POOL_DONE done={len(self.done)} parked={sorted(self.parked)}")
        return not self.parked
