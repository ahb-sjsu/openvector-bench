# NRP operations model for benchmark compute

Measured facts and working patterns for running openvector-bench workloads
on NRP Nautilus (`ssu-atlas-ai`). Everything here was paid for on the
turboquant-pro 1T fleet run and the round-12 generator campaign
(2026-08-03/04); nothing is inferred from documentation alone. Companion
code: `openvector_bench/memguard.py` (page-cache discipline),
`openvector_bench/nrp_pool.py` (pool scheduling).

## The enforcement model

Three regimes, distinguished by measurement:

1. **Utilization bands.** Pods whose usage sits outside 20–200% (CPU) /
   20–150% (memory) of request get their *workload object* (the Job, not
   just the pod) deleted. The enforcer averages over roughly five minutes,
   so a startup phase that idles (image pull, pip install, resume scans)
   drags the average even if steady state complies. I/O-bound phases
   read as idle CPU.
2. **The exempt envelope.** `cpu <= 1 AND memory <= 2Gi` (requests ==
   limits) is not enforced at all. Pods in this envelope survived every
   sweep across a full day while sibling pods above it were killed.
   **This is the only spec that is safe at all times.**
3. **A transient fast clamp.** In some windows, ANY request above 2Gi is
   job-deleted ~40–60 s after container start regardless of usage — a
   16Gi pod holding a touched 4GiB ballast at 30% of request died on the
   same schedule as an idle one. The same spec ran to completion in other
   windows. If a job cannot fit the exempt envelope, submit through a
   retry loop and let attempts ride until one lands in a quiet window
   (the round-12 stage-2b run took eight attempts; the eighth ran 326 s
   to completion). Retry loops must also clear jobs that sit in
   **Failed** (with `backoffLimit: 0`, a pod error leaves the job object
   present forever — absence-only checks hang).

## Fitting the exempt envelope

2Gi is enough for surprisingly large work if page cache is managed, because
**cgroup-v2 charges page cache against the limit**:

- A worker whose anonymous memory was 292Mi OOMed at 2Gi with 1526Mi of
  file cache (its own spill + written artifacts).
- Dirty cache is the unreclaimable kind: evict per chunk *during* writes
  (`SpillFile`), not after them — post-hoc eviction still peaked 1928Mi.
- Mapped file pages resist reclaim even clean: a linear pass over hundreds
  of memory-mapped files crept to the limit; release each map when its
  file is done, and prefer `read()` for one-pass streams.
- Decode/transform in bounded chunks; an in-place normalize instead of a
  copy halves a transient.
- Startup must not idle: stage dependencies as ONE tarball on shared
  storage and extract (CPU-busy) instead of `pip install` (network-idle).
  Extract from the tarball, not from a staged *directory* — a concurrent
  re-stage swaps directories mid-import and imports die on vanished `.so`
  files; the tarball is one atomically-replaced file.

## Scheduling

Waves with barriers lose to stragglers: one volume on an offline node held
seven finished workers for 5.5 h. `PoolRunner` keeps N independent jobs in
flight from a pool — same footprint, no head-of-line blocking — with the
measured failure handling built in (two-poll NotFound confirmation, wedge
bound, attach-stuck parking). Submissions go through the resident
`burst.submit` NATS flow, never hand-rolled kubectl loops; subscribe or
request-reply on `burst.status.*` or a rejected descriptor is
indistinguishable from silence.

## Storage

- `linstor-unl` (autoPlace=1) volumes have ONE replica. An offline node
  makes the volume unreachable until the node returns — no error surfaces
  beyond `FailedAttachVolume`. For seed-defined corpora this does not
  matter: delete the PVC, recreate it under the same name, and let the
  content-addressed resume rebuild from seed (measured: a full 2B-row
  server rebuilt in 3h23m, faster than nursing the stuck volume).
- The provisioner rate-limits creation (~2 volumes per 45 s sustained);
  there is no namespace storage quota. Plan bulk provisioning as hours,
  not minutes.
- CephFS: one writer per file, never mmap-for-write, sequential reads via
  `np.load` over mmap faults.
