# TurboQuant Pro: Open-source TurboQuant for LLM KV cache compression
# Copyright (c) 2026 Andrew H. Bond
# MIT License

"""The RC-1 admission battery (PREREG v2): geometry that governs ANN search.

Implements the registered design: the **angular** metric (§2), a grid over
sample size and neighbourhood scale (§3), **two batteries** — corpus-to-corpus
and held-out-query-to-corpus (§4) — and the eight gated diagnostics (§5).

Design notes that are load-bearing rather than incidental:

* **Exact k-NN, doubly blocked.** Distances are computed in query-blocks x
  base-blocks with a running top-k merge, so peak memory is
  ``qblock x bblock`` and is independent of corpus size. (A single
  ``queries x base`` matrix at the registered grid is 1.6 GB, and the naive
  broadcast form is ~1.7 TB; both are unusable.) Approximate neighbours would
  make an admission filter circular, so exactness is not negotiable.
* **One neighbour structure per (corpus, n, subsample).** Diagnostics at
  k=10/30/100 read prefixes of the same k=100 lists, so the three scales
  describe one graph rather than three samples.
* **Queries are disjoint from the searched base** in both batteries; the
  self-match is therefore absent and no ``[:, 1:]`` self-skip is applied.
* **All vectors are L2-normalized first** (§2). Norms are outside the
  measured geometry by construction and are emitted as descriptors only.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field

import numpy as np

from openvector_bench.hubness import attractiveness_skew

K_GRID = [int(x) for x in os.environ.get("RC_K_GRID", "10,30,100").split(",")]
N_GRID = [
    int(x) for x in os.environ.get("RC_N_GRID", "25000,50000,100000,200000").split(",")
]
N_QUERY = int(os.environ.get("RC_NQ", "10000"))
SUBSAMPLES = int(os.environ.get("RC_SUBSAMPLES", "5"))
PCA_DIM = int(os.environ.get("RC_PCA", "256"))
KMAX = max(K_GRID)

try:
    import torch

    _DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
except Exception:  # numpy fallback is exact, just slower
    torch = None
    _DEV = "cpu"


def normalize(x: np.ndarray) -> np.ndarray:
    """The registered metric: everything is measured on the unit sphere."""
    x = np.asarray(x, dtype=np.float32)
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


# --------------------------------------------------------------------------- #
# Exact k-NN, doubly blocked                                                   #
# --------------------------------------------------------------------------- #
def _blocks(n_base: int, dim: int) -> tuple[int, int]:
    """Block sizes from available device memory, capped for cache behaviour."""
    if torch is not None and _DEV.startswith("cuda"):
        free, _ = torch.cuda.mem_get_info()
        budget = int(free * 0.25) // 4  # float32 entries for the distance tile
    else:
        budget = 64_000_000
    qb = 1024
    bb = max(4096, min(n_base, budget // qb))
    return qb, bb


def knn(base: np.ndarray, queries: np.ndarray, k: int):
    """Exact top-k Euclidean neighbours of unit vectors (= cosine ranking).

    Returns ``(dists, idx)`` with no self-match assumption: callers pass query
    sets disjoint from ``base``.
    """
    n_base, dim = base.shape
    qb, bb = _blocks(n_base, dim)
    if torch is not None:
        dev = torch.device(_DEV)
        b_all = torch.as_tensor(base, dtype=torch.float32)
        D = np.empty((len(queries), k), dtype=np.float32)
        Ix = np.empty((len(queries), k), dtype=np.int64)
        for qs in range(0, len(queries), qb):
            q = torch.as_tensor(queries[qs : qs + qb], dtype=torch.float32).to(dev)
            best_d = torch.full((len(q), k), float("inf"), device=dev)
            best_i = torch.zeros((len(q), k), dtype=torch.long, device=dev)
            for bs in range(0, n_base, bb):
                blk = b_all[bs : bs + bb].to(dev, non_blocking=True)
                # ||q||^2 omitted: constant per row, does not affect ranking.
                d2 = (blk * blk).sum(1)[None, :] - 2.0 * (q @ blk.T)
                kk = min(k, d2.shape[1])
                dd, ii = torch.topk(d2, kk, dim=1, largest=False)
                cat_d = torch.cat([best_d, dd], 1)
                cat_i = torch.cat([best_i, ii + bs], 1)
                sel = torch.topk(cat_d, k, dim=1, largest=False)
                best_d = sel.values
                best_i = torch.gather(cat_i, 1, sel.indices)
            qn = (q * q).sum(1, keepdim=True)
            D[qs : qs + qb] = torch.sqrt(torch.clamp(best_d + qn, min=0)).cpu().numpy()
            Ix[qs : qs + qb] = best_i.cpu().numpy()
        return D, Ix
    D = np.empty((len(queries), k), dtype=np.float32)
    Ix = np.empty((len(queries), k), dtype=np.int64)
    bsq = (base * base).sum(1)
    for qs in range(0, len(queries), qb):
        q = queries[qs : qs + qb]
        best_d = np.full((len(q), k), np.inf, dtype=np.float32)
        best_i = np.zeros((len(q), k), dtype=np.int64)
        for bs in range(0, n_base, bb):
            blk = base[bs : bs + bb]
            d2 = bsq[bs : bs + bb][None, :] - 2.0 * (q @ blk.T)
            kk = min(k, d2.shape[1])
            ii = np.argpartition(d2, kk - 1, axis=1)[:, :kk]
            dd = np.take_along_axis(d2, ii, 1)
            cat_d = np.concatenate([best_d, dd], 1)
            cat_i = np.concatenate([best_i, ii + bs], 1)
            sel = np.argpartition(cat_d, k - 1, axis=1)[:, :k]
            best_d = np.take_along_axis(cat_d, sel, 1)
            best_i = np.take_along_axis(cat_i, sel, 1)
        order = np.argsort(best_d, 1)
        best_d = np.take_along_axis(best_d, order, 1)
        best_i = np.take_along_axis(best_i, order, 1)
        qn = (q * q).sum(1, keepdims=True)
        D[qs : qs + qb] = np.sqrt(np.maximum(best_d + qn, 0))
        Ix[qs : qs + qb] = best_i
    return D, Ix


# --------------------------------------------------------------------------- #
# Diagnostics (all on normalized vectors; no self-match to skip)               #
# --------------------------------------------------------------------------- #
def id_twonn(d: np.ndarray) -> float:
    """Facco two-NN MLE, trimmed at the 90th percentile of mu."""
    r1, r2 = d[:, 0], d[:, 1]
    mu = r2[r1 > 0] / np.maximum(r1[r1 > 0], 1e-12)
    mu = mu[mu > 1.0]
    if len(mu) < 100:
        return float("nan")
    mu = mu[mu <= np.quantile(mu, 0.9)]
    return float(len(mu) / np.sum(np.log(mu)))


def cascade_spectrum_gate(
    d: np.ndarray,
    *,
    ref_r1_median: float | None = None,
    min_octaves: float = 3.0,
    max_ks: float = 0.15,
    min_logmu_spread: float = 0.5,
) -> dict:
    """Mechanism-PRESENCE gate for the round-12 cascade (P-A' precondition).

    P-A' claims that *on a scale-free pair-distance distribution* the TwoNN
    mu-statistics are subsample-invariant, and its failure clause promotes a
    failure to primary capacity-conjecture evidence. That inference is only
    valid if the scale-free ladder was actually present when the prediction
    failed. This gate checks the realized structure has the property the claim
    names, so a P-A' failure means "mechanism present but insufficient" rather
    than being confounded with "mechanism absent" or "grid too narrow".

    It is a *precondition* check, not the registered prediction: P-A' is about
    G1 n-drift across the ladder, which this does not touch.

    ``d``: (n, k>=2) sorted neighbour distances EXCLUDING self.
    ``ref_r1_median``: median r1 of the cascade-OFF control, used as the
        sub-ambient cut. Pass it — using this sample's own median (the
        fallback) conflates the cascade with the ambient scale.

    Three readings, all on the sub-ambient rows the cascade is supposed to
    create: how many octaves the ladder spans, how close to log-uniform
    (scale-free) it is, and whether mu itself is broad rather than
    concentrated at 1 (high-dimensional concentration is precisely what makes
    TwoNN finite-sample-biased, so a mechanism that does not broaden mu cannot
    stabilize it).
    """
    r1 = d[:, 0].astype(np.float64)
    r2 = d[:, 1].astype(np.float64)
    ok = r1 > 0
    cut = (
        float(ref_r1_median) if ref_r1_median is not None else float(np.median(r1[ok]))
    )
    sub = r1[ok & (r1 < cut)]
    out: dict[str, float | bool | int | str] = {
        "n_sub_ambient": int(len(sub)),
        "cut": cut,
        "octaves_spanned": 0.0,
        "ks_uniform": 1.0,
        "logmu_spread": 0.0,
        "passed": False,
    }
    if len(sub) < 200:
        out["cause"] = "too_few_sub_ambient_rows"
        return out

    lg = np.sort(np.log2(sub))
    lo, hi = float(np.quantile(lg, 0.01)), float(np.quantile(lg, 0.99))
    out["octaves_spanned"] = hi - lo
    # KS distance of log2(r1) from Uniform(lo, hi): flat in log <=> scale-free.
    core = lg[(lg >= lo) & (lg <= hi)]
    if hi - lo > 1e-9 and len(core) > 1:
        ecdf = (np.arange(len(core)) + 0.5) / len(core)
        out["ks_uniform"] = float(np.max(np.abs(ecdf - (core - lo) / (hi - lo))))

    mu = r2[ok] / np.maximum(r1[ok], 1e-12)
    lmu = np.log2(mu[mu > 1.0])
    if len(lmu) >= 100:
        out["logmu_spread"] = float(lmu.std())

    out["passed"] = bool(
        out["octaves_spanned"] >= min_octaves
        and out["ks_uniform"] <= max_ks
        and out["logmu_spread"] >= min_logmu_spread
    )
    return out


def id_local(d: np.ndarray, k: int) -> np.ndarray:
    """Levina-Bickel per-point local ID at scale k."""
    tk = d[:, k - 1 : k]
    tj = d[:, : k - 1]
    good = (tj > 0).all(1) & (tk[:, 0] > 0)
    return 1.0 / np.maximum(np.log(tk[good] / tj[good]).mean(1), 1e-12)


def id_ball_growth(d: np.ndarray, k: int) -> float:
    lo, hi = np.quantile(d[:, k - 1], [0.1, 0.9])
    radii = np.geomspace(max(lo, 1e-9), max(hi, 1e-8), 12)
    counts = np.array([(d[:, :k] <= r).sum(1).mean() for r in radii])
    ok = counts > 1
    if ok.sum() < 4:
        return float("nan")
    return float(np.polyfit(np.log(radii[ok]), np.log(counts[ok]), 1)[0])


# --------------------------------------------------------------------------- #
# The scale-resolved growth profile (spec/PROFILE.md §1)                       #
# --------------------------------------------------------------------------- #
PROFILE_KGRID: tuple[int, ...] = tuple(
    sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})
)


def growth_slope(
    d: np.ndarray, kgrid: tuple[int, ...] = PROFILE_KGRID
) -> tuple[np.ndarray, np.ndarray]:
    """``(r, s)`` where ``s(r) = dlog k / dlog r`` — the registered profile.

    This is the pre-limit form of Local Intrinsic Dimensionality (Houle, SISAP
    2017), equivalently the local slope of the Grassberger-Procaccia correlation
    integral. It is *not* a new estimator; see ``spec/PROFILE.md`` §1.

    ``d`` is the sorted neighbour-distance matrix from :func:`knn` with at least
    ``max(kgrid)`` columns.
    """
    r = np.array([float(np.median(d[:, k - 1])) for k in kgrid])
    return r, np.gradient(np.log(np.array(kgrid, dtype=float)), np.log(r))


def profile_ratio(d: np.ndarray, kgrid: tuple[int, ...] = PROFILE_KGRID) -> float:
    """The registered k-matched ratio ``s(k_max)/s(k_min)`` (``PROFILE.md`` §1).

    Matched in k and dimensionless. Deliberately *not* ``beta = dlog s/dlog r``:
    beta divides by each corpus's own log-radius span, and corpora occupy
    disjoint bands with spans differing up to 6x, which makes it unsound across
    corpora (``PROFILE.md`` §1, ``results/R21B_SCALE_DEPENDENCE.md``).
    """
    _, s = growth_slope(d, kgrid)
    return float(s[-1] / max(s[0], 1e-9))


def reproducible_matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """``a @ b`` with a summation order that does not depend on the BLAS.

    A float32 ``@`` is **not** bit-reproducible across platforms. Measured on
    identical inputs, same OpenBLAS build, Windows vs Linux: the f32 product
    hashes differ (``f81d6818`` vs ``a04d9149``) because SIMD width and blocking
    change the order of the inner sum, and f32 has too little precision to
    absorb the reordering. The same product in f64 agrees, as does an explicit
    fixed-order accumulation.

    This matters beyond tidiness. `DISTRIBUTION.md` §3 makes regeneration a
    first-class source, and `R22`'s cross-toolchain result (16/16 shards
    byte-identical) holds only because ``philox_u8`` is pure integer arithmetic.
    Any float-heavy emitter forfeits that guarantee unless its reductions are
    ordered explicitly.

    Accumulating one rank-1 term at a time is the conservative choice: it uses
    no BLAS at all, so it does not rely on f64 having enough headroom for the
    reduction length. Cost is a Python loop over ``a.shape[1]``, which is the
    inner dimension and small in every use here.
    """
    a = np.asarray(a)
    b = np.asarray(b)
    out = np.zeros((a.shape[0], b.shape[1]), dtype=np.float32)
    for j in range(a.shape[1]):
        out += a[:, j : j + 1].astype(np.float32) * b[j : j + 1, :].astype(np.float32)
    return out


def exchangeable_split(
    support: np.ndarray, n_base: int, n_query: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Split an index ``support`` into base and query indices exchangeably.

    Base and queries **must** be drawn from the same region. Sampling queries
    from a different support -- a tail slice, a global holdout over a corpus
    whose base is a head slice or a clumped subset -- makes the split
    non-exchangeable and inflates every neighbour diagnostic. It moved measured
    G1 from 16.1 to 65.7 in `R23`, and has been reintroduced three separate
    times since (`R29`, `R30`, and the first clumpiness ladder in `R31`), each
    time producing smooth, plausible, monotone numbers.

    The failure is not self-announcing, so the split is constructed here once
    rather than per experiment: choose the support first, then partition it.

    Returns ``(base_idx, query_idx)``, both sorted, disjoint, and drawn from the
    same support.
    """
    support = np.asarray(support)
    need = n_base + n_query
    if len(support) < need:
        raise ValueError(
            f"support has {len(support)} rows, need {need} "
            f"(n_base={n_base} + n_query={n_query})"
        )
    rng = np.random.default_rng(seed)
    picked = rng.permutation(support)[:need]
    return np.sort(picked[:n_base]), np.sort(picked[n_base:])


def spectrum(x: np.ndarray) -> tuple[float, int]:
    xc = x - x.mean(0, keepdims=True)
    lam = np.linalg.svd(xc, compute_uv=False) ** 2 / max(len(xc) - 1, 1)
    lam = lam[lam > 0]
    frac = np.cumsum(lam) / lam.sum()
    return float(lam.sum() ** 2 / (lam**2).sum()), int(np.searchsorted(frac, 0.90) + 1)


def relative_contrast(d: np.ndarray, base: np.ndarray, q: np.ndarray, k: int) -> float:
    rng = np.random.default_rng(0)
    ref = base[rng.choice(len(base), size=min(4096, len(base)), replace=False)]
    qq = q[: min(512, len(q))]
    mean_d = float(np.sqrt(np.maximum(2.0 - 2.0 * (qq @ ref.T), 0)).mean())
    return mean_d / float(np.median(d[:, k - 1]))


def hubness(idx: np.ndarray, n_base: int, k: int) -> float:
    counts = np.bincount(idx[:, :k].ravel(), minlength=n_base).astype(np.float64)
    s = counts.std()
    return float(((counts - counts.mean()) ** 3).mean() / max(s**3, 1e-12))


def pca_retention(base: np.ndarray, q: np.ndarray, idx: np.ndarray, k: int) -> float:
    dim = min(PCA_DIM, base.shape[1] - 1)
    mu = base.mean(0, keepdims=True)
    rng = np.random.default_rng(2)
    fit = (base - mu)[rng.choice(len(base), min(20000, len(base)), replace=False)]
    _, _, vt = np.linalg.svd(fit, full_matrices=False)
    p = vt[:dim].T
    _, idx_p = knn(normalize((base - mu) @ p), normalize((q - mu) @ p), k)
    return float(
        np.mean(
            [
                len(set(a) & set(b)) / len(set(a) | set(b))
                for a, b in zip(idx[:, :k], idx_p[:, :k])
            ]
        )
    )


def norm_descriptors(raw: np.ndarray) -> dict:
    """Reported, never gated (PREREG v2 §2): norms are outside the metric."""
    n = np.linalg.norm(raw, axis=1)
    return {"norm_cv": float(n.std() / max(n.mean(), 1e-12))}


@dataclass
class Cell:
    corpus: str
    battery: str
    n: int
    k: int
    sub: int
    dim: int
    g1_id_twonn: float
    g2_id_ballgrowth: float
    g3_eff_rank: float
    g4_dims90: int
    g5_relative_contrast: float
    g6_hubness_skew: float
    # PREREG_RC1 amendment 2026-08-07: G6 is SCORED as the Poisson-deconvolved
    # attractiveness skew. The raw skew stays alongside it because the stored
    # real reference from 2026-07-20 carries only the raw form, so keeping both
    # is what lets the two be compared and the re-measurement be audited.
    g6_attractiveness_skew: float
    rho: float
    g7_local_id_iqr: float
    g8_pca_retention: float
    descriptors: dict = field(default_factory=dict)


def measure(
    corpus: str, battery: str, base_raw, query_raw, n: int, sub: int
) -> list[Cell]:
    """One neighbour structure -> the diagnostics at every k in the grid."""
    rng = np.random.default_rng(10_000 * sub + n)
    bi = rng.choice(len(base_raw), size=min(n, len(base_raw)), replace=False)
    base = normalize(base_raw[bi])
    qi = rng.choice(len(query_raw), size=min(N_QUERY, len(query_raw)), replace=False)
    q = normalize(query_raw[qi])
    d, idx = knn(base, q, KMAX)
    eff, d90 = spectrum(base[: min(50000, len(base))])
    desc = norm_descriptors(base_raw[bi])
    out = []
    for k in K_GRID:
        lid = id_local(d, k)
        out.append(
            Cell(
                corpus=corpus,
                battery=battery,
                n=int(len(base)),
                k=k,
                sub=sub,
                dim=int(base.shape[1]),
                g1_id_twonn=id_twonn(d),
                g2_id_ballgrowth=id_ball_growth(d, k),
                g3_eff_rank=eff,
                g4_dims90=d90,
                g5_relative_contrast=relative_contrast(d, base, q, k),
                g6_hubness_skew=hubness(idx, len(base), k),
                g6_attractiveness_skew=attractiveness_skew(
                    np.bincount(idx[:, :k].ravel(), minlength=len(base)).astype(
                        np.float64
                    )
                ),
                rho=float(len(q) * k / max(len(base), 1)),
                g7_local_id_iqr=float(np.subtract(*np.percentile(lid, [75, 25]))),
                g8_pca_retention=pca_retention(base, q, idx, k),
                descriptors=desc,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Corpora: target + frozen nulls (PREREG v2 §8)                                #
# --------------------------------------------------------------------------- #
def load_target(path: str, cap: int) -> tuple[np.ndarray, np.ndarray]:
    """(corpus rows, real held-out query rows) — Battery B needs both."""
    import glob

    parts = sorted(glob.glob(os.path.join(path, "part_*.npy")))
    out, got = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        take = min(len(a), cap - got)
        out.append(np.asarray(a[:take]))
        got += take
        if got >= cap:
            break
    corpus = np.concatenate(out)
    qpath = os.path.join(path, "queries.npy")
    queries = np.load(qpath) if os.path.exists(qpath) else None
    return corpus, queries


def null_gaussian(x, seed):
    rng = np.random.default_rng(1000 + seed)
    return (rng.standard_normal(x.shape) * float(x.std())).astype(np.float32)


def null_shuffle(x, seed):
    rng = np.random.default_rng(2000 + seed)
    y = np.array(x, copy=True)
    for j in range(y.shape[1]):
        rng.shuffle(y[:, j])
    return y


def null_lowrank(x, seed, rank):
    """The recipe behind the existing 1B/10B synthetic corpus."""
    rng = np.random.default_rng(3000 + seed)
    n, dim = x.shape
    basis = rng.standard_normal((rank, dim)).astype(np.float32)
    coeff = (rng.standard_normal((n, rank)) * np.linspace(1.0, 0.3, rank)).astype(
        np.float32
    )
    y = coeff @ basis
    y += 0.05 * float(x.std()) * rng.standard_normal(y.shape).astype(np.float32)
    return y


def main() -> None:
    target_path = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
    out_path = os.environ.get("RC_OUT", "/archive/tqp_real/rc1/rc1_cells.json")
    cap = int(os.environ.get("RC_CAP", str(max(N_GRID) * 3)))

    print(
        f"device={_DEV} n_grid={N_GRID} k_grid={K_GRID} subs={SUBSAMPLES} nq={N_QUERY}",
        flush=True,
    )
    corpus, real_q = load_target(target_path, cap)
    print(
        f"target {corpus.shape}, real queries {None if real_q is None else real_q.shape}",
        flush=True,
    )
    eff, _ = spectrum(normalize(corpus[:50000]))
    rank = max(2, int(round(eff)))
    print(f"target effective rank {eff:.1f} -> null_lowrank rank {rank}", flush=True)

    # Battery A holds out corpus points as queries, disjoint from the base.
    # Registered protocol fix (results/RC1_ROUND2_CANDIDATE.md, finding 3): the
    # holdout is sampled UNIFORMLY. Taking the first rows inherits the corpus's
    # topical row ordering (Wikipedia arrives ordered), which smuggles a
    # concentrated query marginal into the corpus-to-corpus battery; real
    # battery-A targets are re-measured under this protocol before the next
    # admission run.
    hold = min(N_QUERY * 2, len(corpus) // 10)
    hrng = np.random.default_rng(7)
    hidx = np.sort(hrng.choice(len(corpus), size=hold, replace=False))
    hmask = np.zeros(len(corpus), dtype=bool)
    hmask[hidx] = True
    corpus_q, corpus_base = corpus[hmask], corpus[~hmask]

    cells: list[dict] = []
    for sub in range(SUBSAMPLES):
        variants = {
            "real": (corpus_base, corpus_q, real_q),
            "null_gaussian": None,
            "null_shuffle": None,
            "null_lowrank": None,
        }
        for name in variants:
            if name == "real":
                base_x, qa, qb = variants[name]
            else:
                gen = {
                    "null_gaussian": lambda: null_gaussian(corpus_base, sub),
                    "null_shuffle": lambda: null_shuffle(corpus_base, sub),
                    "null_lowrank": lambda: null_lowrank(corpus_base, sub, rank),
                }[name]
                base_x = gen()
                # Analogous query sets from each corpus's own process (§4).
                qa = base_x[:hold]
                base_x = base_x[hold:]
                qb = None
            for n in N_GRID:
                if n > len(base_x):
                    continue
                for battery, qset in (("A_corpus", qa), ("B_query", qb)):
                    if qset is None:
                        continue
                    for c in measure(name, battery, base_x, qset, n, sub):
                        cells.append(asdict(c))
                        print(json.dumps(asdict(c)), flush=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(cells, f, indent=2)
    print(f"wrote {out_path}", flush=True)
    print("RC1_CELLS_DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
