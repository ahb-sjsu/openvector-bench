"""Is the rising s(r) just anisotropy? Two independent tests, plus diagnostics.

## The objection

Real embeddings are famously anisotropic — they occupy a narrow cone rather
than the sphere (Mimno & Thompson EMNLP 2017; Gao et al. ICLR 2019
"representation degeneration"; Ethayarajh EMNLP 2019). Our corpus shows it:
||mean(X)|| ~ 0.48 on unit vectors, effective rank ~190 of 1024 ambient, and
the whole measurement band sits at r in [0.86, 1.13] where the chordal maximum
is sqrt(2) ~ 1.414, i.e. neighbour cosines of 0.37-0.63.

A reviewer's first move is therefore: *the rising growth dimension is a
restatement of known anisotropy.* That objection has to be answered with
measurements, not argument, because the anisotropy literature is entirely
GLOBAL (average cosine, IsoScore, spectral decay) and has never been
scale-resolved — so there is nothing to cite either way.

## Two tests, in opposite directions

**A. Synthesize the anisotropy alone.** A Gaussian with the corpus's EXACT
empirical mean and covariance, unit-normalised. It has real's first and second
moments — its cone, its spectrum, its effective rank — and nothing else. If
anisotropy produced the ramp, this must reproduce it.

This is a much sharper null than `null_lowrank`, which uses a linear
singular-value taper 1.0 -> 0.3 at rank 190 and is not real's spectrum.

**B. Strip the anisotropy from real.** Whiten and re-measure. If the ramp
survives, it is not anisotropy. Two variants, because whitening is not unique:

* `whitened_topk` — PCA-whiten within the top-K subspace capturing 99% of
  variance, then renormalise. Restricting to top-K keeps the inverse
  well-conditioned; full Sigma^-1/2 would amplify near-null directions into
  noise and test nothing.
* `abtt` — "all-but-the-top" (Mu & Viswanath, ICLR 2018): subtract the mean and
  project out the top 8 principal directions. A lighter, standard,
  well-conditioned de-anisotropisation.

Reporting BOTH matters: if they disagree, the answer depends on how much
structure whitening removes along with the anisotropy, and that itself is the
finding.

## Diagnostics — proving the manipulation worked

Every arm reports ||mean|| and effective rank (participation ratio of the
covariance spectrum). A whitening that leaves ||mean|| at 0.4 has not whitened
anything, and a claim resting on it would be void. These are printed so the
manipulation is auditable rather than asserted.

## Registered reading, before the run

* Gaussian-exact-cov FLAT or FALLING, and whitened real STILL RISING ->
  anisotropy is not the cause; the objection is closed.
* Gaussian-exact-cov RISING -> anisotropy alone suffices; the finding is a
  restatement of known geometry and must be withdrawn.
* Whitened real FLAT -> the ramp is carried by the anisotropic component;
  report as such, which is a substantially weaker claim than currently made.

Protocol is the registered one, on the registered head pool, so every number is
directly comparable to the anchors (G1 exponent -0.168, s_ratio trend +0.511).

Env: AC_CAP, AC_NS, AC_NQ, AC_KMAX, AC_OUT, AC_TARGET, AC_ABTT_D, AC_VAR.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, os.environ.get("AC_THREADS", "4"))

from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

TARGET = os.environ.get("AC_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("AC_OUT", "/home/claude/ovb_scale/anisotropy_controls.json")
CAP = int(os.environ.get("AC_CAP", "600000"))
NS = json.loads(os.environ.get("AC_NS", "[25000, 50000, 100000, 200000]"))
NQ = int(os.environ.get("AC_NQ", "10000"))
KMAX = int(os.environ.get("AC_KMAX", "500"))
ABTT_D = int(os.environ.get("AC_ABTT_D", "8"))
VAR_KEEP = float(os.environ.get("AC_VAR", "0.99"))
SEED = 11
FIT_N = 200_000  # rows used for the mean/covariance fit

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})


def load_head(path: str, cap: int) -> np.ndarray:
    parts = sorted(glob.glob(os.path.join(path, "part_*.npy")))
    out, got = [], 0
    for p in parts:
        a = np.load(p, mmap_mode="r")
        take = min(len(a), cap - got)
        out.append(np.asarray(a[:take]))
        got += take
        if got >= cap:
            break
    return np.concatenate(out)


def spectrum_stats(xn: np.ndarray) -> tuple[float, float]:
    """(||mean||, effective rank) — the manipulation's audit trail."""
    sub = xn[: min(50_000, len(xn))]
    c = sub - sub.mean(0, keepdims=True)
    lam = np.linalg.svd(c, compute_uv=False) ** 2 / max(len(c) - 1, 1)
    lam = lam[lam > 0]
    eff = float(lam.sum() ** 2 / (lam**2).sum())
    return float(np.linalg.norm(xn.mean(0))), eff


def eig_fit(x: np.ndarray):
    """Mean and eigendecomposition of the empirical covariance."""
    fit = x[: min(FIT_N, len(x))].astype(np.float32)
    mu = fit.mean(0, keepdims=True)
    c = fit - mu
    # covariance eigenpairs via SVD of the centred matrix (no 1024x1024 inverse)
    _, s, vt = np.linalg.svd(c, full_matrices=False)
    lam = (s.astype(np.float64) ** 2) / max(len(c) - 1, 1)
    return mu, lam, vt.astype(np.float32)


def make_gaussian_exact(x: np.ndarray) -> np.ndarray:
    """N(mu, Sigma) with the corpus's exact first and second moments."""
    mu, lam, vt = eig_fit(x)
    rng = np.random.default_rng(4242)
    out = np.empty_like(x)
    scale = np.sqrt(np.maximum(lam, 0)).astype(np.float32)
    step = 50_000
    for i in range(0, len(x), step):
        z = rng.standard_normal((min(step, len(x) - i), len(scale))).astype(np.float32)
        out[i:i + step] = mu + (z * scale) @ vt
    return out


def make_whitened_topk(x: np.ndarray) -> np.ndarray:
    """PCA-whiten inside the top-K subspace holding VAR_KEEP of the variance."""
    mu, lam, vt = eig_fit(x)
    frac = np.cumsum(lam) / lam.sum()
    k = int(np.searchsorted(frac, VAR_KEEP) + 1)
    w = (vt[:k].T / np.sqrt(lam[:k]).astype(np.float32))  # (dim, k)
    print(f"  whitened_topk: K={k} of {len(lam)} for {VAR_KEEP:.0%} variance",
          flush=True)
    out = np.empty((len(x), k), dtype=np.float32)
    step = 50_000
    for i in range(0, len(x), step):
        out[i:i + step] = (x[i:i + step] - mu) @ w
    return out


def make_abtt(x: np.ndarray, d: int) -> np.ndarray:
    """All-but-the-top (Mu & Viswanath, ICLR 2018): centre, drop top-d PCs."""
    mu, _, vt = eig_fit(x)
    top = vt[:d]  # (d, dim)
    out = np.empty_like(x)
    step = 50_000
    for i in range(0, len(x), step):
        c = x[i:i + step] - mu
        out[i:i + step] = c - (c @ top.T) @ top
    return out


def ladder(name: str, x: np.ndarray, results: dict) -> None:
    xn = normalize(x)
    mnorm, eff = spectrum_stats(xn)
    hrng = np.random.default_rng(7)
    hidx = hrng.choice(len(xn), size=NQ, replace=False)
    hmask = np.zeros(len(xn), dtype=bool)
    hmask[hidx] = True
    q = xn[hmask]
    base_pool = xn[~hmask]
    per_n, g1s, ratios = {}, [], []
    for n in NS:
        rng = np.random.default_rng(10_000 + n)
        bi = rng.choice(len(base_pool), size=min(n, len(base_pool)), replace=False)
        d, _ = knn(base_pool[bi], q, KMAX)
        r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
        s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
        g1 = float(id_twonn(d))
        ratio = float(s[-1] / max(s[0], 1e-9))
        per_n[str(n)] = {"g1": g1, "s_lo": float(s[0]), "s_hi": float(s[-1]),
                         "s_ratio": ratio, "r_lo": float(r[0]), "r_hi": float(r[-1])}
        g1s.append(g1)
        ratios.append(ratio)
        print(f"    n={n:6d} G1={g1:7.2f} s {s[0]:6.1f}->{s[-1]:6.1f} "
              f"ratio {ratio:.2f} r [{r[0]:.3f},{r[-1]:.3f}]", flush=True)
    ln = np.log(NS)
    results[name] = {"dim": int(x.shape[1]), "mean_norm": mnorm, "eff_rank": eff,
                     "per_n": per_n,
                     "g1_exponent": float(np.polyfit(ln, np.log(g1s), 1)[0]),
                     "s_ratio_trend": float(np.polyfit(ln, ratios, 1)[0])}
    print(f"  -> {name}: G1 exp {results[name]['g1_exponent']:+.3f}, "
          f"ratio trend {results[name]['s_ratio_trend']:+.3f}, "
          f"||mean|| {mnorm:.3f}, eff_rank {eff:.0f}", flush=True)


def main() -> int:
    real = load_head(TARGET, CAP)
    print(f"registered head pool {real.shape}", flush=True)
    results: dict = {}

    print("\n[real] reference", flush=True)
    ladder("real", real, results)

    print("\n[gaussian_exact_cov] real's exact mean + covariance, nothing else",
          flush=True)
    ladder("gaussian_exact_cov", make_gaussian_exact(real), results)

    print(f"\n[whitened_topk] PCA-whitened, {VAR_KEEP:.0%} variance", flush=True)
    ladder("whitened_topk", make_whitened_topk(real), results)

    print(f"\n[abtt_{ABTT_D}] all-but-the-top, {ABTT_D} PCs removed", flush=True)
    ladder(f"abtt_{ABTT_D}", make_abtt(real, ABTT_D), results)

    print("\n=== anisotropy controls ===", flush=True)
    print(f"{'arm':20s} {'dim':>5s} {'G1 exp':>8s} {'ratio trend':>12s} "
          f"{'||mean||':>9s} {'eff_rank':>9s}", flush=True)
    for k, v in results.items():
        print(f"{k:20s} {v['dim']:5d} {v['g1_exponent']:+8.3f} "
              f"{v['s_ratio_trend']:+12.3f} {v['mean_norm']:9.3f} "
              f"{v['eff_rank']:9.0f}", flush=True)

    g = results["gaussian_exact_cov"]["s_ratio_trend"]
    w = results["whitened_topk"]["s_ratio_trend"]
    a = results[f"abtt_{ABTT_D}"]["s_ratio_trend"]
    verdict = ("ANISOTROPY SUFFICES — withdraw the claim" if g > 0.25 else
               "ANISOTROPY NOT THE CAUSE" if (w > 0.25 and a > 0.25) else
               "MIXED — ramp partly carried by the anisotropic component")
    print(f"\nVERDICT: {verdict}", flush=True)
    print("(reference: real +0.511; synthetic controls |trend| <= 0.13)",
          flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"config": {"cap": CAP, "ns": NS, "nq": NQ, "kmax": KMAX,
                              "abtt_d": ABTT_D, "var_keep": VAR_KEEP,
                              "fit_n": FIT_N, "kgrid": KGRID},
                   "results": results, "verdict": verdict}, f, indent=2)
    print(f"wrote {OUT}", flush=True)
    print("ANISOTROPY_CONTROLS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
