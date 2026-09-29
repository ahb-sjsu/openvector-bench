"""Real tiers (FAMILY.md §1-§3): the seal is excluded, tiers nest exactly,
queries lie outside the tiers, the build is the plan, and the strata are
defined from L1 alone."""

from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import pytest

from harness.tiers import build_real_tiers as B
from harness.tiers import gt_strata as G
from openvector_bench import tiers as T


def _rc1_sealed(i: int) -> bool:  # verbatim from harness/rc1/r11_calibration.py
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def test_the_seal_is_the_rc1_seal_and_is_excluded():
    assert all(T.sealed(i) == _rc1_sealed(i) for i in range(5000))
    ids = T.eligible_ids(5000)
    assert not any(_rc1_sealed(int(i)) for i in ids)
    assert 0.70 < len(ids) / 5000 < 0.80


def test_tiers_nest_and_queries_are_outside_them():
    p = T.plan(40_000, (3, 4), nq=500)
    rows, q = p["rows"], p["queries"]
    assert len(rows) == 10_000 and len(set(rows)) == len(rows)
    assert not set(q) & set(rows)
    assert not any(T.sealed(int(i)) for i in np.concatenate([rows, q]))
    # T3 is the first 10^3 of T4's order, and the order is regenerable
    again = T.plan(40_000, (3,), nq=500)
    np.testing.assert_array_equal(again["rows"], rows[:1000])
    # not a prefix of the source: the permutation mixes the whole range
    assert rows[:1000].max() > 30_000


def test_a_tier_the_source_cannot_fill_is_refused():
    with pytest.raises(ValueError, match="eligible rows"):
        T.plan(10_000, (4,), nq=100)


@pytest.fixture
def source(tmp_path):
    rng = np.random.default_rng(0)
    d = tmp_path / "src"
    d.mkdir()
    x = (rng.standard_normal((12_000, 16)) * np.geomspace(2, 0.3, 16)).astype(
        np.float32
    )
    for k in range(3):
        np.save(d / f"part_{k:03d}.npy", x[k * 4000 : (k + 1) * 4000])
    return tmp_path, x


def test_the_build_writes_every_row_to_its_planned_slot(source, monkeypatch):
    root, x = source
    monkeypatch.setattr(B, "PART", 1000)
    B.build(f"npy:{root / 'src'}", 12_000, str(root / "ovb"), "toy", [3], nq=200)
    p = T.plan(12_000, (3,), 200)
    t = root / "ovb" / "toy-t3"
    got = np.load(t / "part_000.npy")
    np.testing.assert_array_equal(got, x[p["rows"]])
    np.testing.assert_array_equal(np.load(t / "queries.npy"), x[p["queries"]])
    man = json.loads((t / "manifest.json").read_text())
    assert man["row_ids_sha256"] == T.ids_sha256(p["rows"])
    assert man["salt"] == f"0x{T.TIER_SALT:016X}" and "excluded" in man["seal"]


def test_smaller_tiers_are_hard_links_to_the_larger_tiers_prefix(source, monkeypatch):
    root, x = source
    monkeypatch.setattr(B, "PART", 100)
    B.build(f"npy:{root / 'src'}", 12_000, str(root / "ovb"), "toy", [2, 3], nq=200)
    small, big = root / "ovb" / "toy-t2", root / "ovb" / "toy-t3"
    assert os.path.samefile(small / "queries.npy", big / "queries.npy")
    assert os.path.samefile(small / "part_000.npy", big / "part_000.npy")
    assert len(np.load(big / "part_009.npy")) == 100


def test_a_tier_smaller_than_a_part_gets_its_own_truncated_copy(source, monkeypatch):
    root, x = source
    monkeypatch.setattr(B, "PART", 1000)
    B.build(f"npy:{root / 'src'}", 12_000, str(root / "ovb"), "toy", [2, 3], nq=200)
    small = np.load(root / "ovb" / "toy-t2" / "part_000.npy")
    big = np.load(root / "ovb" / "toy-t3" / "part_000.npy")
    assert len(small) == 100
    np.testing.assert_array_equal(small, big[:100])


def test_gt_and_strata_from_the_tier(source, monkeypatch, tmp_path):
    root, x = source
    monkeypatch.setattr(B, "PART", 1000)
    B.build(f"npy:{root / 'src'}", 12_000, str(root / "ovb"), "toy", [3], nq=200)
    t = root / "ovb" / "toy-t3"
    G.run(str(t), str(root), "toy-t3")
    ids = np.load(t / "gt_top100.npy")
    rows = np.load(t / "part_000.npy")
    q = np.load(t / "queries.npy")
    s = T.normalize(q[:5]) @ T.normalize(rows).T
    np.testing.assert_array_equal(ids[:5, :10], np.argsort(-s, axis=1)[:, :10])
    st = json.loads((t / "strata.json").read_text())
    assert set(st["strata"]) == {
        f"{m}:{b}" for m in T.STRATA for b in ("low", "med", "high")
    }
    lid = [set(st["strata"][f"lid:{b}"]) for b in ("low", "med", "high")]
    assert not (lid[0] & lid[1]) and sum(map(len, lid)) + st["undefined"]["lid"] == 200
    assert "l1_l2_agreement" in st["not_computed"]
    assert (root / "gt" / "toy-t3.npy").exists() and (
        root / "strata" / "toy-t3.json"
    ).exists()
