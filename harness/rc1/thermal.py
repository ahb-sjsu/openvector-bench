"""Thermal-governed execution for Atlas probes — the standard wrapper.

The atlas skill requires `batch_probe.ThermalController` around **all** CPU/GPU-
heavy work. Several rounds in this arc instead ran fixed-thread jobs and reacted
to temperature after the fact, which is how `R54` reached 99 C — one degree
below critical — with another workload already on the box.

The controller is a Kalman-filtered PI loop over `[temp, temp_rate]`: it *reduces*
threads before overshoot using the predicted rate, and raises them during
cooldown using predicted headroom. Reacting after the reading is the failure mode
it exists to prevent.

Two pieces are needed to apply it to a numpy/BLAS workload:

* the controller supplies a thread budget (`get_threads()`), and
* `threadpoolctl.threadpool_limits` applies it to OpenBLAS/OMP **at runtime** —
  setting `OMP_NUM_THREADS` in the environment is read once at import and cannot
  be changed per work unit.

Usage::

    from thermal import governed

    for arm in arms:
        with governed(target_temp=80.0) as budget:
            run_one_arm(threads=budget())

or, for a sequence of units sharing one controller::

    with ThermalGovernor(target_temp=80.0) as gov:
        for arm in arms:
            with gov.limits():
                run_one_arm()

`target_temp` defaults to 80 rather than the skill's 82 because the Z840's two
packages track a few degrees apart and the *other* package is the one that has
run hot here.
"""

from __future__ import annotations

import contextlib

try:  # available on Atlas; absent locally, so the module stays importable
    from batch_probe import ThermalController
except Exception:  # pragma: no cover - depends on host
    ThermalController = None

try:
    from threadpoolctl import threadpool_limits
except Exception:  # pragma: no cover
    threadpool_limits = None


class ThermalGovernor:
    """Hold a workload at a temperature setpoint by varying its thread budget."""

    def __init__(
        self,
        target_temp: float = 80.0,
        max_threads: int = 20,
        min_threads: int = 2,
        verbose: bool = False,
    ):
        # max_threads 20 is the skill's cap: the Z840's coolers cannot sustain
        # more, and 40 threads took the CPUs to 99 C in an earlier incident.
        self.target_temp = target_temp
        self.max_threads = max_threads
        self.min_threads = min_threads
        self._ctrl = None
        if ThermalController is not None:
            self._ctrl = ThermalController(
                target_temp=target_temp,
                max_threads=max_threads,
                min_threads=min_threads,
                verbose=verbose,
            )

    def __enter__(self) -> "ThermalGovernor":
        if self._ctrl is not None:
            self._ctrl.start()
        return self

    def __exit__(self, *exc) -> None:
        if self._ctrl is not None:
            self._ctrl.stop()
        return None

    def budget(self) -> int:
        """Current thread allowance, from the controller if present."""
        if self._ctrl is None:
            return self.min_threads
        return max(self.min_threads, int(self._ctrl.get_threads()))

    @contextlib.contextmanager
    def limits(self):
        """Apply the current budget to BLAS/OMP for one work unit."""
        n = self.budget()
        if threadpool_limits is None:
            yield n
        else:
            with threadpool_limits(limits=n):
                yield n

    def summary(self):
        return self._ctrl.summary() if self._ctrl is not None else None


@contextlib.contextmanager
def governed(target_temp: float = 80.0, max_threads: int = 20):
    """One-shot governor for a single work unit."""
    with ThermalGovernor(target_temp=target_temp, max_threads=max_threads) as gov:
        with gov.limits() as n:
            yield lambda: n
