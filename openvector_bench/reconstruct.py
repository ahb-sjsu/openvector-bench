"""Reconstruction with graceful degradation (spec/DISTRIBUTION.md §3).

For each shard, in order, stopping at the first source that **verifies**:
regenerate from the generator spec, then fetch from each manifest source in
declared order. Acceptance is by hash alone — a regenerated shard that does
not match its root is not an error but a *cache miss*, recorded and fallen
through, so determinism is an optimization and correctness never depends on
it.

Every attempt is recorded as an event (``method``, ``source``, ``ok``,
``bytes_moved``, ``seconds``): regeneration-success rate, per-source latency,
and total bytes moved are the reportable measurements of spec §6, so the
event log is the primary output, not debug garnish.

Credentials are ambient, never arguments: ``https://`` and ``file://`` need
none; ``s3://`` uses boto3's standard resolution (env / ``~/.aws``) plus an
optional non-AWS endpoint (NRP Ceph, MinIO) from ``OVB_S3_ENDPOINT``. Nothing
here reads, stores, or prints a secret.
"""

from __future__ import annotations

import os
import time
import urllib.request

from .generators import GENERATORS
from .manifest import shard_filename, verify_shard_bytes


def default_fetch(url: str) -> bytes:
    """Fetch one shard's bytes. file:// and http(s):// via urllib; s3:// via
    boto3 with ambient credentials and an optional custom endpoint."""
    if url.startswith("s3://"):
        import boto3  # optional dependency, imported only on the s3 path

        bucket, key = url[5:].split("/", 1)
        client = boto3.client("s3", endpoint_url=os.environ.get("OVB_S3_ENDPOINT"))
        return client.get_object(Bucket=bucket, Key=key)["Body"].read()
    with urllib.request.urlopen(url) as r:  # noqa: S310 — manifest-declared URL
        return r.read()


def _attempt(events: list[dict], method: str, source: str, fn) -> bytes | None:
    t0 = time.time()
    data, err = None, None
    try:
        data = fn()
    except Exception as e:  # a dead mirror is degradation, not failure
        err = f"{type(e).__name__}: {e}"
    ev = {
        "method": method,
        "source": source,
        "ok": data is not None,
        "bytes_moved": len(data) if (data is not None and method == "fetch") else 0,
        "seconds": round(time.time() - t0, 3),
    }
    if err:
        ev["error"] = err
    events.append(ev)
    return data


def reconstruct_shard(
    man: dict,
    i: int,
    dest_dir: str,
    *,
    generators: dict | None = None,
    fetch=default_fetch,
    skip_sources: frozenset[str] = frozenset(),
    events: list[dict] | None = None,
) -> list[dict]:
    """Materialize shard *i* into ``dest_dir`` from the first verifying source.

    ``skip_sources`` (by ``kind``) deliberately disables sources so the §6
    experiment can force a mixture of regeneration, cache, and mirror.
    ``generators`` overrides the registry (or pass ``{}`` to disable
    regeneration entirely). Raises ``LookupError`` when every source is
    exhausted — the manifest names the mirrors that exist, so exhaustion is a
    statement about the world, not about this function.
    """
    evs = events if events is not None else []
    registry = GENERATORS if generators is None else generators

    candidates: list[tuple[str, str, object]] = []
    gen = man.get("generator")
    if gen and gen.get("impl") in registry:
        impl = registry[gen["impl"]]
        candidates.append(("regenerate", gen["impl"], lambda: impl(i, gen["params"])))
    for src in man.get("sources", []):
        if src.get("kind") in skip_sources:
            continue
        url = src["url"].rstrip("/") + "/" + shard_filename(man, i)
        candidates.append(("fetch", url, lambda u=url: fetch(u)))

    for method, source, fn in candidates:
        data = _attempt(evs, method, source, fn)
        if data is None:
            continue
        if not verify_shard_bytes(man, i, data):
            evs[-1]["ok"] = False
            evs[-1]["error"] = "hash mismatch (recorded as cache miss)"
            continue
        path = os.path.join(dest_dir, shard_filename(man, i))
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
        evs[-1]["shard"] = i
        return evs
    raise LookupError(f"shard {i}: no source verified ({len(evs)} attempts)")


def reconstruct(man: dict, dest_dir: str, **kw) -> list[dict]:
    """All shards; returns the full event log for reporting."""
    os.makedirs(dest_dir, exist_ok=True)
    events: list[dict] = []
    for s in man["shards"]:
        reconstruct_shard(man, s["i"], dest_dir, events=events, **kw)
    return events


def summarize(events: list[dict]) -> dict:
    """The spec-§6 reportables, computed from the event log."""
    regen = [e for e in events if e["method"] == "regenerate"]
    fetch = [e for e in events if e["method"] == "fetch"]
    return {
        "regen_attempts": len(regen),
        "regen_hits": sum(e["ok"] for e in regen),
        "fetch_attempts": len(fetch),
        "fetch_hits": sum(e["ok"] for e in fetch),
        "bytes_moved": sum(e["bytes_moved"] for e in events),
        "seconds_by_source": {
            src: round(sum(e["seconds"] for e in events if e["source"] == src), 3)
            for src in {e["source"] for e in events}
        },
    }
