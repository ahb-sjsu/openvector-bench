"""Generator-search fitness — the shared ``evaluate_fn`` for procedural-corpus
discovery, reusing the RC-1 geometry battery. Tests are self-consistent (no real
embeddings needed): a synthetic corpus at known knobs is the "target", and the
fitness must reward a candidate that reproduces those knobs.
"""

from __future__ import annotations

import numpy as np

from openvector_bench.generator_search import (
    GATES,
    decode,
    make_evaluate_fn,
    measure_corpus,
    synth_corpus,
)

DIM = 64
N, NQ, KS = 1500, 400, (10,)
P_STAR = np.array([4.0, 1.2, 1.0, 0.30, 0.05])  # PARAMS order


def _target(p, seed=0):
    # Same-instance split, matching make_evaluate_fn: queries are held out from
    # the SAME generated instance (results/QUERY_COUPLING_ARTIFACT.md) — an
    # independent seed is a different manifold realization.
    full = synth_corpus(decode(p), N + NQ, DIM, seed)
    base, q = full[:N], full[N:]
    return measure_corpus(base, q, ks=KS, batteries=("A", "B"), n_query=NQ, seed=seed)


def test_decode_inactive_restores_defaults():
    on = decode(P_STAR)
    off = decode(np.full(len(P_STAR), 1e6))
    assert off["log2_clusters"] == 6.0 and off["size_tail"] == 1.1  # defaults
    assert on["size_tail"] == 1.2  # active value passes through


def test_synth_corpus_shape_and_unit_norm():
    x = synth_corpus(decode(P_STAR), 800, DIM, 3)
    assert x.shape == (800, DIM)
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)


def test_evaluate_fn_contract_and_rewards_match():
    target = _target(P_STAR, seed=0)
    ev = make_evaluate_fn(target, dim=DIM, n=N, n_query=NQ, ks=KS, seed=0)

    near, err = ev(P_STAR)  # the candidate IS the target (same knobs + seed)
    far, _ = ev(np.array([0.0, 0.0, 3.0, 1.0, 0.4]))  # very different knobs

    # structural-fuzzing contract: (scalar score, dict of signed per-target errors)
    assert isinstance(near, float) and isinstance(err, dict) and err
    assert all("@" in key for key in err)
    assert {key.split("@")[0] for key in err} <= set(GATES)

    assert np.isfinite([near, far]).all()
    assert near < 1e-6  # exact reproduction -> ~zero mismatch
    assert far > near  # matching the target's geometry fits it better


def test_manifold_corpus_shape_norm_and_hyperbolic_branch():
    from openvector_bench.generator_search import MANIFOLD_PARAMS, manifold_corpus

    p = {name: dflt for name, _, _, dflt in MANIFOLD_PARAMS}
    x = manifold_corpus(p, 600, DIM, 5)
    assert x.shape == (600, DIM)
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)
    # the hyperbolic (Poincare exp_0) latent branch runs and stays finite
    xh = manifold_corpus({**p, "curvature": 2.0}, 600, DIM, 5)
    assert xh.shape == (600, DIM) and np.isfinite(xh).all()


def test_local_centers_off_is_byte_identical_to_round10():
    from openvector_bench.generator_search import (
        HIER_LC_PARAMS,
        hier_dupq_corpus,
        hier_lc_corpus,
    )

    p = {name: dflt for name, _, _, dflt in HIER_LC_PARAMS}
    assert p["lc_shells"] == 0.0  # the primitive's default is OFF
    x_lc = hier_lc_corpus(p, 900, DIM, 7)
    x_r10 = hier_dupq_corpus(p, 900, DIM, 7)
    assert np.array_equal(x_lc, x_r10)


def test_local_centers_count_response_is_a_dial():
    """PREREG_ROUND11 mechanism claim at unit-test scale: every shell member's
    nearest neighbours are its planted rows, so a planted row's k-occurrence
    count ~ its shell's membership — constructed, not emergent."""
    from openvector_bench.generator_search import local_centers
    from openvector_bench.geometry import knn, normalize

    n, m, p, n_shell = 2400, 4, 3, 80
    base = normalize(np.random.default_rng(0).standard_normal((n, DIM)))
    x, planted = local_centers(
        base,
        n_base=n,
        m=m,
        n_planted=p,
        n_shell=n_shell,
        radius=0.1,
        center_jit=0.05,
        rng=np.random.default_rng(1),
        return_rows=True,
    )
    assert x.shape == base.shape and len(planted) == m * p
    assert np.allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-4)
    _, idx = knn(x, x, p + 1)  # self lands in column 0; count columns 1..p
    counts = np.bincount(idx[:, 1:].ravel(), minlength=n).astype(np.float64)
    pmask = np.zeros(n, dtype=bool)
    pmask[planted] = True
    # Near-deterministic response: planted rows capture ~all member slots ...
    assert counts[pmask].sum() >= 0.9 * m * n_shell * p
    assert counts[pmask].min() >= 0.7 * n_shell
    # ... and no unplanted row comes close (the tail is constructed).
    assert counts[~pmask].max() <= 0.25 * n_shell


def test_r12_mechanisms_off_is_byte_identical_to_round10():
    from openvector_bench.generator_search import (
        HIER_R12_PARAMS,
        hier_dupq_corpus,
        hier_r12_corpus,
    )

    p = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    # Every round-12 mechanism defaults OFF.
    assert p["grad_decay"] == 0.0 and p["grad_span"] == 1.0
    assert p["occ_mix"] == 0.0 and p["dens_span"] == 0.0
    x_r12 = hier_r12_corpus(p, 900, DIM, 7)
    x_r10 = hier_dupq_corpus(p, 900, DIM, 7)
    assert np.array_equal(x_r12, x_r10)


def test_r12_gradient_moves_twonn_and_stays_count_quiet():
    """PREREG_ROUND12 P-A at unit-test scale: the gradient field lowers the
    TwoNN reading (anisotropy dials local effective dimension) while leaving
    the count tail within noise of the mechanism-off control."""
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import id_twonn, knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}  # architecture off
    pg = p0 | {"grad_decay": 0.8, "grad_span": 8.0}
    n, nq, k = 3000, 300, 10

    def _measure(p, seed=11):
        x = hier_r12_corpus(p, n + nq, DIM, seed)
        base, q = x[:n], x[n:]
        d, idx = knn(base, q, k)
        counts = np.bincount(idx[:, :k].ravel(), minlength=n).astype(np.float64)
        sk = ((counts - counts.mean()) ** 3).mean() / max(counts.std() ** 3, 1e-12)
        return id_twonn(d), sk

    id0, sk0 = _measure(p0)
    idg, skg = _measure(pg)
    assert idg < 0.8 * id0  # the gradient mechanism moves G1 down
    assert abs(skg - sk0) < 0.5 * max(abs(sk0), 1.0)  # and is count-quiet


def test_r12_renewal_moves_count_tail():
    """PREREG_ROUND12 P-B mechanism direction at unit-test scale: renewal
    occupancy + density contrast raise the count tail. NOTE: strict
    ID-quietness is the registered stage-2 DECOUPLING CHECK at ladder scale,
    not a toy-scale property — at n=3000/DIM=64 the occupancy re-weighting
    measurably lowers the pooled TwoNN reading (~0.77x control; more
    within-patch neighbour pairs), which is exactly what the r12_stage1
    sweeps exist to quantify. Here we assert the dial works and the ID
    reading stays sane, not silent."""
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import id_twonn, knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}
    po = p0 | {"occ_mix": 1.0, "occ_tail": 1.2, "dens_span": 0.9}
    n, nq, k = 3000, 300, 10

    def _measure(p, seed=13):
        x = hier_r12_corpus(p, n + nq, DIM, seed)
        base, q = x[:n], x[n:]
        d, idx = knn(base, q, k)
        counts = np.bincount(idx[:, :k].ravel(), minlength=n).astype(np.float64)
        sk = ((counts - counts.mean()) ** 3).mean() / max(counts.std() ** 3, 1e-12)
        return id_twonn(d), sk

    id0, sk0 = _measure(p0)
    ido, sko = _measure(po)
    assert sko > 1.5 * max(sk0, 0.1)  # the renewal law moves the count tail up
    assert ido > 0.5 * id0  # sanity: no collapse (quietness: stage-2, at scale)


def test_r12_cascade_builds_the_graded_ladder():
    """Round-12 v2 P-A' mechanism signature at unit-test scale: the cascade
    puts base->base NN distances at graded fractional scales (real's
    diagnostic: r1 1%-quantile 0.375 vs median 0.86, diag_target.json), so
    the 1%-quantile/median ratio must drop sharply vs cascade-off — while
    the count tail stays within noise (uniform parents, no owners).
    n-FLATNESS itself is the registered ladder-scale question, not a toy
    property."""
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}
    pc = p0 | {"cascade_frac": 0.5}
    n, k = 3000, 10

    def _measure(p, seed=19):
        x = hier_r12_corpus(p, n, DIM, seed)
        base = x[: n - int(round(n / 9))]
        d, idx = knn(base, base, 2)  # col 0 = self, col 1 = true NN
        r1 = d[:, 1]
        ladder = float(np.quantile(r1, 0.01) / max(np.median(r1), 1e-12))
        d10, i10 = knn(base, base, k + 1)
        counts = np.bincount(i10[:, 1:].ravel(), minlength=len(base)).astype(np.float64)
        sk = ((counts - counts.mean()) ** 3).mean() / max(counts.std() ** 3, 1e-12)
        return ladder, sk

    lad0, sk0 = _measure(p0)
    ladc, skc = _measure(pc)
    # Measured at these settings: ratio 0.637 (off) -> 0.443 (frac 0.5) —
    # the cascade grades the WHOLE r1 distribution (median 0.49 -> 0.13),
    # and the shape ratio lands at real's 0.375/0.86 = 0.44. The threshold
    # asserts the direction, not the coincidence of the toy-scale match.
    assert ladc < 0.75 * lad0  # graded short-range mass appears
    assert abs(skc - sk0) < 0.75 * max(abs(sk0), 1.0)  # and no count tail


def test_r12_cascade_passes_its_mechanism_presence_gate():
    """The P-A' PRECONDITION gate (R12_PREFREEZE_AUDIT.md item 5).

    ``test_r12_cascade_builds_the_graded_ladder`` shows the cascade *changes*
    the ladder; it does not show the ladder is *scale-free*, which is the
    property P-A's mechanism claim actually names. Since P-A's failure clause
    promotes a failure to primary capacity-conjecture evidence, that inference
    needs the mechanism demonstrably present first.

    Checked at the freeze-CANDIDATE setting the audit derives, not at the
    convenience setting: cascade_frac 0.85 (>= the ~0.79 the mixture
    arithmetic requires), cascade_smin 0.05 (>= 4.3 octaves, satisfying the
    >= 3-octave precondition), cascade_alpha 1.0 (the only value at which the
    offset law is log-uniform, hence scale-free).

    Thresholds are fixed a priori from the prereg text, NOT tuned to pass: if
    the cascade fails its own presence gate here, that is a finding about the
    mechanism and belongs in the record.
    """
    from openvector_bench.generator_search import HIER_R12_PARAMS, hier_r12_corpus
    from openvector_bench.geometry import cascade_spectrum_gate, knn

    p0 = {name: dflt for name, _, _, dflt in HIER_R12_PARAMS}
    p0 |= {"cloud_mass": 0.0, "dup_mass": 0.0, "q_anchor": 0.0}
    pc = p0 | {"cascade_frac": 0.85, "cascade_smin": 0.05, "cascade_alpha": 1.0}
    n = 3000

    def _dists(p, seed=19):
        x = hier_r12_corpus(p, n, DIM, seed)
        base = x[: n - int(round(n / 9))]
        d, _ = knn(base, base, 4)
        return d[:, 1:]  # drop the self column

    d_off = _dists(p0)
    ref = float(np.median(d_off[:, 0]))
    gate = lambda over: cascade_spectrum_gate(  # noqa: E731
        _dists(p0 | over), ref_r1_median=ref
    )
    g_off = cascade_spectrum_gate(d_off, ref_r1_median=ref)

    # (1) The gate must DISCRIMINATE, or it is vacuous: cascade-off has no
    #     sub-ambient scale-free ladder to find. Measured off: 0.74 octaves,
    #     ks 0.46, mu spread 0.18.
    assert not g_off["passed"], f"gate is vacuous — passes with cascade off: {g_off}"

    # (2) The mechanism IS demonstrably present somewhere in the family:
    #     frac 0.5 / smin 0.05 / alpha 1 measures 3.02 octaves, ks 0.134,
    #     mu spread 0.91.
    g_half = gate({"cascade_frac": 0.5, "cascade_smin": 0.05, "cascade_alpha": 1.0})
    assert g_half["passed"], f"cascade absent even at frac 0.5: {g_half}"
    assert g_half["octaves_spanned"] >= 3.0  # P-A's own precondition
    assert g_half["logmu_spread"] > g_off["logmu_spread"]  # mu broadened

    # (3) smin at its declared maximum cannot satisfy the >= 3-octave
    #     precondition (measured 2.18) — the grid restriction in
    #     R12_PREFREEZE_AUDIT.md item 3a, pinned as a regression guard.
    assert not gate({"cascade_frac": 0.85, "cascade_smin": 0.3})["passed"]

    # (4) CHARACTERIZATION — the open finding, deliberately asserted so it
    #     cannot be lost. At the frac P-A' actually needs (>= ~0.79 by the
    #     audit's mixture arithmetic) the realized spectrum stops being
    #     log-uniform: frac 0.85 measures ks 0.219 against the 0.15 bound,
    #     because deep attachment makes pair distances SUMS of offsets along
    #     the tree path rather than single log-uniform draws. If this
    #     assertion ever starts failing, the tension is resolved — update
    #     R12_PREFREEZE_AUDIT.md and delete this guard.
    g_cand = gate(pc)
    assert not g_cand["passed"], (
        "frac 0.85 now passes the presence gate — the frac tension recorded in "
        f"R12_PREFREEZE_AUDIT.md is resolved; update the audit. {g_cand}"
    )
    assert g_cand["ks_uniform"] > g_half["ks_uniform"]  # flatness degrades with frac


def test_make_evaluate_fn_accepts_the_manifold_family():
    from openvector_bench.generator_search import (
        MANIFOLD_PARAMS,
        manifold_corpus,
        measure_corpus,
    )

    p_star = np.array([d for _, _, _, d in MANIFOLD_PARAMS])
    # Same-instance split, matching make_evaluate_fn (see _target above).
    full = manifold_corpus({n: d for n, _, _, d in MANIFOLD_PARAMS}, N + NQ, DIM, 0)
    base, q = full[:N], full[N:]
    target = measure_corpus(base, q, ks=KS, batteries=("B",), n_query=NQ, seed=0)
    ev = make_evaluate_fn(
        target,
        dim=DIM,
        n=N,
        n_query=NQ,
        ks=KS,
        batteries=("B",),
        seed=0,
        generator=manifold_corpus,
        params_spec=MANIFOLD_PARAMS,
    )
    near, err = ev(p_star)
    assert isinstance(near, float) and err and near < 1e-6  # candidate == target


def test_dirichlet_codebook_knobs_move_what_they_claim():
    """The family's whole claim is three near-separable knobs.

    Asserted at smoke scale only — this is a wiring check that each knob
    moves its own target in the right direction, not the registered
    separation measurement (harness/rc1/r15_codebook_gate.py, P-15B/C).
    """
    import numpy as np

    from openvector_bench.generator_search import dirichlet_codebook_corpus
    from openvector_bench.geometry import spectrum

    base = {"log2_atoms": 6.0, "concentration": 0.3, "atom_tail": 0.0, "noise": 0.02}
    x0 = dirichlet_codebook_corpus(base, 3000, 128, 0)
    assert x0.shape == (3000, 128)
    assert np.isfinite(x0).all()
    # rows are unit norm
    assert np.allclose(np.linalg.norm(x0, axis=1), 1.0, atol=1e-4)

    # More atoms -> higher effective rank.
    eff0, _ = spectrum(x0)
    eff1, _ = spectrum(
        dirichlet_codebook_corpus(dict(base, log2_atoms=7.0), 3000, 128, 0)
    )
    assert eff1 > eff0

    # An asymmetric popularity law must actually concentrate mass on atoms:
    # with a strong tail the corpus should be less spread than without.
    eff_tail, _ = spectrum(
        dirichlet_codebook_corpus(dict(base, atom_tail=1.5), 3000, 128, 0)
    )
    assert eff_tail < eff0


def test_dirichlet_codebook_is_reproducible_by_seed():
    from openvector_bench.generator_search import dirichlet_codebook_corpus

    p = {"log2_atoms": 6.0, "concentration": 0.3, "atom_tail": 0.5, "noise": 0.02}
    a = dirichlet_codebook_corpus(p, 500, 64, 7)
    b = dirichlet_codebook_corpus(p, 500, 64, 7)
    assert (a == b).all()  # byte-reproducible, as the benchmark family requires
