"""Per-tier ANN difficulty audit for fleet-scale synthetic corpora.

R80 (``results/R80_ANN.md``) established that a corpus can match real
embedding geometry on the admission panel and still be an order of
magnitude *easier* for an IVF index: real Wikipedia-1024 needs
nprobe 47-50 of 1024 cells for 95% recall@10, while the matched
generator needs 2. Any fleet run that stresses ANN systems with
synthetic data must therefore report where each tier sits on that
scale, or its difficulty claims are unfounded.

This module packages the R80 measurement panel as a reusable audit:

* cell-occupancy shape under IVF k-means (CV, skew, max share,
  top-10 share),
* query margins (median (r2-r1)/r1 and (r10-r1)/r1),
* recall@10 vs nprobe and expected scan fraction,
* ``nprobe_at_r95`` -- the single-number difficulty score,

plus the frozen real-Wikipedia reference band, so a report can flag a
tier as "real-hard", "intermediate", or "self-similar-easy" without
re-measuring the target corpus.

The measurement protocol is byte-for-byte the R80 one (K=1024 cells,
20 k-means iterations, seed 7, 10k exchangeable queries at seed 31,
exact top-10 ground truth) so numbers are comparable across reports.
Requires torch; runs on CUDA when available, CPU otherwise (slow).

CLI::

    python -m openvector_bench.difficulty_audit tier0.npy tier1.npy \
        --out report.json

or, for generated tiers, pass ``--gen seed:nrows`` to audit the frozen
package generator directly.
"""

from __future__ import annotations

import json
import time

import numpy as np

try:
    import torch
except ImportError:  # pragma: no cover - audit requires torch
    torch = None

K_CELLS = 1024
KM_ITERS = 20
KM_SEED = 7
QUERY_SEED = 31
N_QUERIES = 10_000
TOP_K = 10
NPROBES = (1, 2, 4, 8, 16, 32, 64)

# Frozen R80 panel (results/rc6_ann.json): real Wikipedia-1024 blocks
# 3M/13M/23M and the frozen RC-3 generator at seeds 2027/41, all at the
# protocol constants above with a 590k base. min/max across blocks.
R80_REFERENCE = {
    "real": {
        "nprobe_at_r95": (47, 50),
        "occ_cv": (0.384, 0.402),
        "occ_top10_share": (0.023, 0.026),
        "margin_nn": (0.0508, 0.0524),
        "margin_10": (0.2131, 0.2186),
        "recall_at_1": (0.533, 0.536),
    },
    "gen_rc3": {
        "nprobe_at_r95": (2, 2),
        "occ_cv": (0.313, 0.318),
        "occ_top10_share": (0.019, 0.019),
        "margin_nn": (0.0536, 0.0545),
        "margin_10": (0.2121, 0.2140),
        "recall_at_1": (0.914, 0.917),
    },
}


def _dev(device=None):
    if torch is None:
        raise RuntimeError("difficulty_audit requires torch")
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _normalize_t(t):
    return t / t.norm(dim=1, keepdim=True).clamp_min(1e-12)


def _knn(base, q, k, bs=4096):
    od, oi = [], []
    for s in range(0, q.shape[0], bs):
        sim = q[s : s + bs] @ base.T
        dv, iv = torch.topk(sim, k, dim=1)
        od.append((2.0 - 2.0 * dv).clamp_min(0).sqrt())
        oi.append(iv)
    return torch.cat(od), torch.cat(oi)


def _kmeans(bt, k, iters, seed, dev):
    rng = np.random.default_rng(seed)
    cent = bt[torch.from_numpy(rng.choice(bt.shape[0], k, replace=False)).to(dev)]
    cent = cent.clone()
    assign = None
    for _ in range(iters):
        sims = []
        for s in range(0, bt.shape[0], 65536):
            sims.append((bt[s : s + 65536] @ cent.T).argmax(1))
        assign = torch.cat(sims)
        cent.zero_()
        cent.index_add_(0, assign, bt)
        cnt = torch.bincount(assign, minlength=k).clamp_min(1)
        cent = _normalize_t(cent / cnt.unsqueeze(1))
    return cent, assign


def audit_corpus(x, name="corpus", device=None, verbose=True):
    """R80 difficulty panel for one corpus.

    ``x``: float32 array (n, dim), n > N_QUERIES. Rows are split into an
    exchangeable base/query pair at QUERY_SEED, exactly as in R80.
    Returns the panel dict (JSON-serializable).
    """
    dev = _dev(device)
    t0 = time.time()
    n = x.shape[0]
    if n <= N_QUERIES + K_CELLS:
        raise ValueError("corpus too small to audit: %d rows" % n)
    xt = _normalize_t(torch.from_numpy(np.ascontiguousarray(x)).to(dev))
    perm = np.random.default_rng(QUERY_SEED).permutation(n)[:n]
    bi = np.sort(perm[: n - N_QUERIES])
    qi = np.sort(perm[n - N_QUERIES :])
    bt = xt[torch.from_numpy(bi).to(dev)]
    qt = xt[torch.from_numpy(qi).to(dev)]

    d, gt = _knn(bt, qt, TOP_K)
    dn = d.cpu().numpy()
    rec = {
        "name": name,
        "n": int(n),
        "dim": int(x.shape[1]),
        "margin_nn": float(
            np.median((dn[:, 1] - dn[:, 0]) / np.maximum(dn[:, 0], 1e-9))
        ),
        "margin_10": float(
            np.median((dn[:, 9] - dn[:, 0]) / np.maximum(dn[:, 0], 1e-9))
        ),
    }

    cent, assign = _kmeans(bt, K_CELLS, KM_ITERS, KM_SEED, dev)
    cnt = torch.bincount(assign, minlength=K_CELLS).cpu().numpy().astype(float)
    frac = cnt / cnt.sum()
    rec["occ_cv"] = float(cnt.std() / cnt.mean())
    rec["occ_skew"] = float(
        ((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12)
    )
    rec["occ_max_share"] = float(frac.max())
    rec["occ_top10_share"] = float(np.sort(frac)[-10:].sum())

    qcell_sim = qt @ cent.T
    gt_cells = assign[gt]
    probe_rank = qcell_sim.argsort(dim=1, descending=True)
    cell_rank = torch.empty_like(probe_rank)
    cell_rank.scatter_(
        1, probe_rank, torch.arange(K_CELLS, device=dev).expand_as(probe_rank)
    )
    gt_cell_rank = torch.gather(cell_rank, 1, gt_cells)
    frac_t = torch.from_numpy(frac).to(dev).float()
    cum_mass = frac_t[probe_rank].cumsum(1)
    rec["recall"] = {}
    rec["scan_frac"] = {}
    for npb in NPROBES:
        rec["recall"][str(npb)] = float((gt_cell_rank < npb).float().mean())
        rec["scan_frac"][str(npb)] = float(cum_mass[:, npb - 1].mean())
    rec["nprobe_at_r95"] = None
    for npb in range(1, K_CELLS + 1):
        if float((gt_cell_rank < npb).float().mean()) >= 0.95:
            rec["nprobe_at_r95"] = npb
            break

    rec["difficulty"] = classify(rec)
    rec["seconds"] = round(time.time() - t0, 1)
    if verbose:
        print(format_row(rec), flush=True)
    del xt, bt, qt, cent
    if dev.type == "cuda":
        torch.cuda.empty_cache()
    return rec


def classify(rec):
    """Place a panel on the R80 real/self-similar scale by np@95."""
    np95 = rec["nprobe_at_r95"]
    real_lo = R80_REFERENCE["real"]["nprobe_at_r95"][0]
    easy_hi = R80_REFERENCE["gen_rc3"]["nprobe_at_r95"][1]
    if np95 is None or np95 >= real_lo:
        return "real-hard"
    if np95 <= 2 * easy_hi:
        return "self-similar-easy"
    return "intermediate"


def format_row(rec):
    return (
        "%-14s n=%-9d | occ cv %5.3f skew %5.2f top10 %.3f | "
        "m1 %.4f m10 %.4f | r@p1 %.3f | np@95 %-4s -> %s  (%.0fs)"
        % (
            rec["name"],
            rec["n"],
            rec["occ_cv"],
            rec["occ_skew"],
            rec["occ_top10_share"],
            rec["margin_nn"],
            rec["margin_10"],
            rec["recall"]["1"],
            rec["nprobe_at_r95"],
            rec["difficulty"],
            rec.get("seconds", 0),
        )
    )


def report(panels):
    """Text report over a list of audit_corpus panels, with the R80 band."""
    lines = [
        "ANN difficulty audit (R80 protocol: K=%d cells, %d queries, recall@%d)"
        % (K_CELLS, N_QUERIES, TOP_K),
        "reference  real wiki-1024   np@95 %d-%d   occ cv %.3f-%.3f   r@p1 %.3f-%.3f"
        % (
            *R80_REFERENCE["real"]["nprobe_at_r95"],
            *R80_REFERENCE["real"]["occ_cv"],
            *R80_REFERENCE["real"]["recall_at_1"],
        ),
        "reference  matched gen      np@95 %d-%d    occ cv %.3f-%.3f   r@p1 %.3f-%.3f"
        % (
            *R80_REFERENCE["gen_rc3"]["nprobe_at_r95"],
            *R80_REFERENCE["gen_rc3"]["occ_cv"],
            *R80_REFERENCE["gen_rc3"]["recall_at_1"],
        ),
        "-" * 100,
    ]
    lines += [format_row(r) for r in panels]
    return "\n".join(lines)


def _main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("npy", nargs="*", help=".npy corpora to audit (float32, n x dim)")
    ap.add_argument(
        "--gen",
        action="append",
        default=[],
        metavar="SEED:NROWS",
        help="audit the frozen package generator at this seed and size",
    )
    ap.add_argument(
        "--cap",
        type=int,
        default=600_000,
        help="rows per corpus (R80: 590k base + 10k queries)",
    )
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", default=None, help="write panels JSON here")
    args = ap.parse_args(argv)

    panels = []
    for path in args.npy:
        x = np.load(path, mmap_mode="r")
        x = np.array(x[: args.cap], dtype=np.float32)
        panels.append(audit_corpus(x, name=path.rsplit("/", 1)[-1], device=args.device))
    for spec in args.gen:
        seed, nrows = (int(v) for v in spec.split(":"))
        from openvector_bench.segment_gen import SEGMENT_PARAMS, segment_corpus

        p = {k: d for k, _, _, d in SEGMENT_PARAMS}
        nrows = min(nrows, args.cap)
        x = segment_corpus(p, nrows, 1024, seed)
        panels.append(audit_corpus(x, name="gen_s%d" % seed, device=args.device))
    print()
    print(report(panels))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(panels, f, indent=1)
        print("\nwrote %s" % args.out)


if __name__ == "__main__":
    _main()
