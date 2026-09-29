# openvector-bench
# MIT License

"""Real tiers below the seam: membership, placement, L1 ground truth, strata.

Implements `spec/FAMILY.md` §1-§3 for a real source (the tiers are T6, T7 and,
where the source is large enough, T8):

**Eligibility.** The source's sealed 25% (`spec/PREREG_RC1.md` §7:
``blake2b(str(row_id), digest_size=1)[0] % 4 == 3``) is excluded before
anything else is computed, so no tier, query, ground truth or stratum ever
depends on a sealed row. The rule is the one every RC-1 script uses, and a test
pins it against them.

**Membership.** ``rank(row) = H(salt ‖ row_id)`` with ``H`` the integer-exact
keyed hash of :mod:`openvector_bench.hashrng` (``mix_keys(salt, row_id)``), so
the permutation is identical on any platform and regenerable from the salt and
the row ids alone. Eligible rows are sorted by rank; ``T_k`` is the first
``10**k`` of that order, so ``T_k ⊂ T_{k+1}`` exactly, and every tier's rows are
stored **in permutation order**, so a smaller tier's files are a prefix of a
larger tier's.

**Queries.** The last ``nq`` eligible rows of the same order. They are drawn by
the same hash as the tiers (exchangeable with them, `spec/PROFILE.md` §2) and
lie outside every tier smaller than ``n_eligible - nq`` rows.

**Ground truth** is exact top-``k`` under the angular metric (cosine on
L2-normalised rows), per tier (not nested), in tier positions.

**Strata** (`FAMILY.md` §3), per query, per tier, from L1 alone:

- ``lid``: Levina-Bickel local intrinsic dimension at k = 10 over the query's
  true-neighbour distances (angular distance ``1 - cos``);
- ``margin``: ``d_{11} / d_1``, the (k+1)-th true distance over the first; a
  tight margin (near 1) is where quantization flips ranks;
- ``hub_exposure``: the mean, over the query's true top-10, of how many queries'
  true top-100 contain that row, over its expectation ``nq * 100 / n``;
- ``dispersion``: the mean pairwise angular distance among the true top-10 over
  their mean distance to the query (one cluster below 1, spread above).

Each is cut at its tertiles into ``low`` / ``med`` / ``high``. ``L1/L2
agreement`` is **not computed**: no L2 labels exist yet (`FAMILY.md` §6 step 3).
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from .hashrng import mix_keys

TIER_SALT = 0x4F56425F54494552  # "OVB_TIER" in ASCII; published in every manifest
GT_K = 100
STRATA_K = 10
STRATA = ("lid", "margin", "hub_exposure", "dispersion")
NOT_COMPUTED = {
    "l1_l2_agreement": "no L2 labels exist yet (FAMILY.md section 6, step 3)"
}


def sealed(row_id: int) -> bool:
    """PREREG_RC1 §7: True for the untouchable 25%. The same expression as every
    RC-1 script (``harness/rc1/*``, ``harness/generator/*``)."""
    return (
        hashlib.blake2b(str(int(row_id)).encode(), digest_size=1).digest()[0] % 4 == 3
    )


def eligible_ids(n_source: int) -> np.ndarray:
    """Row ids ``0..n_source-1`` that are not sealed, ascending."""
    return np.fromiter(
        (i for i in range(n_source) if not sealed(i)), dtype=np.int64, count=-1
    )


def order(ids: np.ndarray, salt: int = TIER_SALT) -> np.ndarray:
    """The eligible ids in tier order: sorted by ``mix_keys(salt, row_id)``."""
    rank = mix_keys(salt, np.asarray(ids, dtype=np.int64))
    return np.asarray(ids)[np.argsort(rank, kind="stable")]


def plan(n_source: int, tiers: tuple[int, ...], nq: int, salt: int = TIER_SALT) -> dict:
    """Which source row lands where: the largest tier's rows in order, and the
    queries. Refuses tiers the eligible rows cannot fill beside the queries."""
    ordered = order(eligible_ids(n_source), salt)
    top = 10 ** max(tiers)
    if top + nq > len(ordered):
        raise ValueError(
            f"T{max(tiers)} needs {top:,} rows plus {nq:,} queries; the source has "
            f"{len(ordered):,} eligible rows"
        )
    return dict(
        salt=salt,
        n_source=n_source,
        n_eligible=int(len(ordered)),
        tiers=sorted(tiers),
        rows=ordered[:top],
        queries=ordered[-nq:],
    )


def ids_sha256(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a, dtype="<i8").tobytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Ground truth and strata                                                     #
# --------------------------------------------------------------------------- #


def normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


def exact_topk(blocks, queries: np.ndarray, k: int = GT_K):
    """Exact top-``k`` cosine over normalised rows streamed as ``(start, block)``.
    Returns ``(ids, sims)``, best first, ids in tier positions."""
    q = normalize(queries)
    best_s = np.full((len(q), k), -np.inf, np.float32)
    best_i = np.full((len(q), k), -1, np.int64)
    for start, blk in blocks:
        s = q @ normalize(blk).T
        kk = min(k, s.shape[1])
        part = np.argpartition(-s, kk - 1, axis=1)[:, :kk]
        cs = np.concatenate([best_s, np.take_along_axis(s, part, axis=1)], axis=1)
        ci = np.concatenate([best_i, part + start], axis=1)
        sel = np.argpartition(-cs, k - 1, axis=1)[:, :k]
        best_s = np.take_along_axis(cs, sel, axis=1)
        best_i = np.take_along_axis(ci, sel, axis=1)
    o = np.argsort(-best_s, axis=1, kind="stable")
    return np.take_along_axis(best_i, o, axis=1), np.take_along_axis(best_s, o, axis=1)


def _lid(d: np.ndarray, k: int) -> np.ndarray:
    """Levina-Bickel at scale k per row (NaN where a distance is zero), the
    estimator of ``geometry.id_local`` without dropping rows."""
    tk, tj = d[:, k - 1 : k], d[:, : k - 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        m = np.log(tk / tj).mean(1)
        out = 1.0 / np.maximum(m, 1e-12)
    out[~((tj > 0).all(1) & (tk[:, 0] > 0))] = np.nan
    return out


def measures(gt_ids, gt_sims, neighbour_rows, n_tier: int) -> dict:
    """Per-query stratum measures from the ground truth.

    ``neighbour_rows`` is ``(nq, STRATA_K, dim)``: each query's true top-10 rows
    (any scale; they are normalised here)."""
    k = STRATA_K
    d = np.clip(1.0 - gt_sims.astype(np.float64), 0.0, 2.0)  # angular distance
    counts = np.bincount(gt_ids.ravel(), minlength=n_tier)
    expect = gt_ids.size / n_tier
    hub = counts[gt_ids[:, :k]].mean(1) / expect
    v = normalize(neighbour_rows.reshape(-1, neighbour_rows.shape[-1])).reshape(
        neighbour_rows.shape
    )
    pair = 1.0 - np.einsum("qid,qjd->qij", v, v)
    iu = np.triu_indices(k, 1)
    spread = pair[:, iu[0], iu[1]].mean(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        margin = d[:, k] / d[:, 0]
        disp = spread / d[:, :k].mean(1)
    return dict(lid=_lid(d, k), margin=margin, hub_exposure=hub, dispersion=disp)


def strata(meas: dict) -> dict:
    """Tertile cuts per measure; NaN (undefined) queries are left out of every
    bin of that measure and counted."""
    out, cuts, undefined = {}, {}, {}
    for name in STRATA:
        x = np.asarray(meas[name], np.float64)
        ok = np.isfinite(x)
        undefined[name] = int((~ok).sum())
        lo, hi = np.quantile(x[ok], [1 / 3, 2 / 3])
        cuts[name] = [float(lo), float(hi)]
        idx = np.arange(len(x))
        out[f"{name}:low"] = idx[ok & (x <= lo)].tolist()
        out[f"{name}:med"] = idx[ok & (x > lo) & (x <= hi)].tolist()
        out[f"{name}:high"] = idx[ok & (x > hi)].tolist()
    return dict(strata=out, cuts=cuts, undefined=undefined, not_computed=NOT_COMPUTED)


def manifest_record(p: dict, source: dict, tier: int, files: dict) -> dict:
    """What a tier is: its source, the seal and the permutation it came from,
    and the identity of every file. Canonical JSON, so it hashes stably."""
    n = 10**tier
    return dict(
        schema="openvector-bench/real-tier",
        schema_version=1,
        tier=f"T{tier}",
        rows=n,
        source=source,
        seal="PREREG_RC1 section 7: blake2b(str(row_id), digest_size=1)[0] % 4 == 3 excluded",
        salt=f"0x{p['salt']:016X}",
        hash="openvector_bench.hashrng.mix_keys(salt, row_id)",
        n_source=p["n_source"],
        n_eligible=p["n_eligible"],
        row_ids_sha256=ids_sha256(p["rows"][:n]),
        query_ids_sha256=ids_sha256(p["queries"]),
        n_queries=int(len(p["queries"])),
        files=files,
    )


def dumps(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
