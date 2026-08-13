"""RC-2 real-side: held-out target measurement (PROFILE.md P1 falsifier).

Four contiguous 600k-row blocks of the real corpus at offsets NEVER used by
any prior round (consumed: 0, 1067268, 7228966, 34414820): 5M, 15M, 25M,
39M. The measurement protocol â€” splits, seeds, rung construction, g8 â€”
matches the registered generator-side protocol byte for byte, so the
held-out bands (mean +- 2 sd across blocks) are directly comparable to the
frozen generator's single evaluation.

Runs on Atlas GPU 1 (CUDA_VISIBLE_DEVICES=1), thermal-guarded: pauses
between heavy stages while CPU Package > 80 C or GPU > 80 C.
"""

import json
import subprocess
import time

import numpy as np
import torch  # noqa: E402  (after generation: fork-clean CUDA)

DEV = "cuda"
assert torch.cuda.is_available()

DIM, POOL = 1024, 600000
OFFSETS = [8_000_000, 13_000_000, 23_000_000, 37_000_000]
PARTS = "/archive/tqp_real/wiki1024/part_%03d.npy"
OUT = "/home/claude/ovb_scale/rc3_heldout.json"
KG = sorted({int(round(v)) for v in np.geomspace(4, 500, 16)})


def temps():
    try:
        g = int(
            subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu",
                    "--format=csv,noheader",
                    "-i",
                    "1",
                ]
            ).split()[0]
        )
    except Exception:
        g = 0
    try:
        s = subprocess.check_output(["sensors"]).decode()
        c = max(
            float(ln.split("+")[1].split("\xb0")[0])
            for ln in s.splitlines()
            if "Package id" in ln
        )
    except Exception:
        c = 0.0
    return c, g


def guard():
    while True:
        c, g = temps()
        if c <= 80.0 and g <= 80:
            return
        print("thermal pause: cpu %.0f gpu %d" % (c, g), flush=True)
        time.sleep(30)


def load_block(off):
    part, rem = divmod(off, 1_000_000)
    a = np.load(PARTS % part, mmap_mode="r")
    if rem + POOL <= len(a):
        x = np.asarray(a[rem : rem + POOL], dtype=np.float32)
    else:
        b = np.load(PARTS % (part + 1), mmap_mode="r")
        x = np.concatenate(
            [
                np.asarray(a[rem:], dtype=np.float32),
                np.asarray(b[: rem + POOL - len(a)], dtype=np.float32),
            ]
        )
    x = torch.from_numpy(x).to(DEV)
    return x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)


def normalize_t(x):
    return x / x.norm(dim=1, keepdim=True).clamp_min(1e-12)


def knn_t(base, q, k, bs=4096):
    od, oi = [], []
    for s in range(0, q.shape[0], bs):
        sim = q[s : s + bs] @ base.T
        dv, iv = torch.topk(sim, k, dim=1)
        od.append((2.0 - 2.0 * dv).clamp_min(0).sqrt())
        oi.append(iv)
    return torch.cat(od), torch.cat(oi)


def exch(sup, nb, nq, seed=31):
    p = np.random.default_rng(seed).permutation(np.asarray(sup))[: nb + nq]
    return np.sort(p[:nb]), np.sort(p[nb:])


def id_twonn(d):
    r1, r2 = d[:, 0], d[:, 1]
    m = r1 > 0
    mu = r2[m] / np.maximum(r1[m], 1e-12)
    mu = mu[mu > 1.0]
    if len(mu) < 100:
        return float("nan")
    mu = mu[mu <= np.quantile(mu, 0.9)]
    return float(len(mu) / np.sum(np.log(mu)))


def sk_curve(dn):
    r = np.array([float(np.median(dn[:, k - 1])) for k in KG])
    s = np.gradient(np.log(np.array(KG, float)), np.log(r))
    return r, s


def profile_ratio(dn):
    _, s = sk_curve(dn)
    return float(s[-1] / max(s[0], 1e-9))


def spectrum_t(base_t):
    xc = base_t - base_t.mean(0, keepdim=True)
    lam = torch.linalg.svdvals(xc) ** 2 / max(xc.shape[0] - 1, 1)
    lam = lam[lam > 0].double()
    frac = torch.cumsum(lam, 0) / lam.sum()
    eff = float(lam.sum() ** 2 / (lam**2).sum())
    d90 = int(
        torch.searchsorted(
            frac, torch.tensor(0.90, dtype=frac.dtype, device=frac.device)
        ).item()
        + 1
    )
    return eff, d90


def g8_pca(x, bi, qi, nnn10):
    bt = x[torch.from_numpy(bi).to(DEV)]
    qt = x[torch.from_numpy(qi).to(DEV)]
    mu = bt.mean(0, keepdim=True)
    rng = np.random.default_rng(2)
    sel = rng.choice(len(bi), min(20000, len(bi)), replace=False)
    fit = bt[torch.from_numpy(sel).to(DEV)] - mu
    _, _, Vh = torch.linalg.svd(fit, full_matrices=False)
    p = Vh[:256].T
    bp = normalize_t((bt - mu) @ p)
    qp = normalize_t((qt - mu) @ p)
    _, idxp = knn_t(bp, qp, 10)
    idxp = idxp.cpu().numpy()
    jac = [len(set(a) & set(b)) / len(set(a) | set(b)) for a, b in zip(nnn10, idxp)]
    del bt, qt, bp, qp
    return float(np.mean(jac))


results = {}
for off in OFFSETS:
    guard()
    t0 = time.time()
    x = load_block(off)
    rec = {"offset": off}

    # half A: gates + section 3 four-rung ladder
    bi, qi = exch(np.arange(210000), 200000, 10000, seed=31)
    d, nn = knn_t(x[torch.from_numpy(bi).to(DEV)], x[torch.from_numpy(qi).to(DEV)], 500)
    dn, nnn = d.cpu().numpy(), nn.cpu().numpy()
    del d, nn
    rec["g1"] = id_twonn(dn)
    cnt = np.bincount(nnn[:, :10].ravel(), minlength=len(bi)).astype(np.float64)
    rec["g6"] = float(((cnt - cnt.mean()) ** 3).mean() / max(cnt.std() ** 3, 1e-12))
    bt = x[torch.from_numpy(bi).to(DEV)]
    rr = torch.randperm(bt.shape[0], device=DEV)[:4096]
    mean_d = float(
        (2.0 - 2.0 * (x[torch.from_numpy(qi[:512]).to(DEV)] @ bt[rr].T))
        .clamp_min(0)
        .sqrt()
        .mean()
    )
    rec["g5"] = mean_d / float(np.median(dn[:, 9]))
    rec["g3"], rec["g4"] = spectrum_t(bt[:50000])
    del bt
    guard()
    rec["g8"] = g8_pca(x, bi, qi, nnn[:, :10])
    b6, q6 = exch(np.arange(POOL), POOL - 10000, 10000, seed=61)
    ratios, g1s = [], []
    for n_r in (25000, 50000, 100000, 200000):
        rr2 = np.random.default_rng(10000 + n_r)
        sub = b6[rr2.choice(len(b6), n_r, replace=False)]
        d5, _ = knn_t(
            x[torch.from_numpy(np.sort(sub)).to(DEV)],
            x[torch.from_numpy(q6).to(DEV)],
            500,
        )
        d5n = d5.cpu().numpy()
        ratios.append(profile_ratio(d5n))
        g1s.append(id_twonn(d5n))
        del d5
    ln_n = np.log([25000, 50000, 100000, 200000])
    rec["s3_rung_ratios"] = ratios
    rec["s3_rung_g1"] = g1s
    rec["s3_trend"] = float(np.polyfit(ln_n, ratios, 1)[0])
    rec["s3_g1exp"] = float(np.polyfit(ln_n, np.log(g1s), 1)[0])
    guard()

    # half B: section 3b five-pool ladder + s(k) curve
    vals = {}
    for Pn in (50000, 100000, 200000, 400000, 600000):
        rg = np.random.default_rng(700 + Pn // 1000)
        sup = rg.choice(Pn, 35000, replace=False)
        b3, q3 = exch(sup, 25000, 10000, seed=31)
        d3, _ = knn_t(
            x[torch.from_numpy(b3).to(DEV)], x[torch.from_numpy(q3).to(DEV)], 500
        )
        d3n = d3.cpu().numpy()
        vals[Pn] = {"ratio": profile_ratio(d3n), "g1": id_twonn(d3n)}
        del d3
    rec["s3b"] = {str(k): v for k, v in vals.items()}
    rec["rspan"] = vals[50000]["ratio"] - vals[600000]["ratio"]
    rec["gspan"] = float(np.log(vals[50000]["g1"] / vals[600000]["g1"]))
    _, s = sk_curve(dn)
    rec["s_uniform"] = [float(v) for v in s]

    results[str(off)] = rec
    print(
        "off %8d | g1 %5.2f g3 %5.1f g4 %4d g5 %5.3f g6 %5.3f g8 %5.3f | "
        "trend %+.3f g1exp %+.3f | rspan %+6.3f gspan %+6.3f  (%.0fs)"
        % (
            off,
            rec["g1"],
            rec["g3"],
            rec["g4"],
            rec["g5"],
            rec["g6"],
            rec["g8"],
            rec["s3_trend"],
            rec["s3_g1exp"],
            rec["rspan"],
            rec["gspan"],
            time.time() - t0,
        ),
        flush=True,
    )
    del x
    torch.cuda.empty_cache()
    json.dump(results, open(OUT, "w"), indent=1)

# held-out bands: mean +- 2 sd across the four blocks, mirroring how the
# registered bands were derived from block variance
bands = {}
for stat in (
    "g1",
    "g3",
    "g4",
    "g5",
    "g6",
    "g8",
    "s3_trend",
    "s3_g1exp",
    "rspan",
    "gspan",
):
    v = np.array([results[str(o)][stat] for o in OFFSETS], dtype=float)
    bands[stat] = {
        "mean": float(v.mean()),
        "sd": float(v.std(ddof=1)),
        "lo": float(v.mean() - 2 * v.std(ddof=1)),
        "hi": float(v.mean() + 2 * v.std(ddof=1)),
    }
for i, n_r in enumerate((25000, 50000, 100000, 200000)):
    v = np.array([results[str(o)]["s3_rung_ratios"][i] for o in OFFSETS])
    bands["rung_ratio_%d" % n_r] = {
        "lo": float(v.mean() - 2 * v.std(ddof=1)),
        "hi": float(v.mean() + 2 * v.std(ddof=1)),
    }
for Pn in (50000, 100000, 200000, 400000, 600000):
    for f in ("ratio", "g1"):
        v = np.array([results[str(o)]["s3b"][str(Pn)][f] for o in OFFSETS])
        bands["s3b_%s_%d" % (f, Pn)] = {
            "lo": float(v.mean() - 2 * v.std(ddof=1)),
            "hi": float(v.mean() + 2 * v.std(ddof=1)),
        }
results["heldout_bands"] = bands
json.dump(results, open(OUT, "w"), indent=1)
print("RC3_REAL_DONE", flush=True)
