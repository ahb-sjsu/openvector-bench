"""F2 three-arm transfer test: is the dimension ramp a property of Cohere alone?

`NORMAL_FORMS.md` F2 is a registered falsification criterion never tested. Two
independent agent reviews converged on this as the cheapest experiment that can
kill — or validate — the encoder-generator route, and it is diagnostic for the
hand-designed family search either way.

## The question

Real (Cohere Embed-V3) has a local growth dimension that RISES with radius, and
whose rise STRENGTHENS with n. Six generator families have failed to reproduce
it. Before designing a seventh, establish whether the ramp is a property of
embedding geometry generally or of one model.

## Arms — all on IDENTICAL passages, so differences are the encoder

| arm | dim | isolates |
|---|---|---|
| cohere (from the parquet `emb` column) | 1024 | the reference, free |
| LaBSE | 768 | a different architecture, objective, training set |
| LeBSE (`ahbond/lebse`) | 768 | SAME arch + tokenizer as LaBSE, different training |
| BGE-M3 | 1024 | the REGISTERED dim, a different family (XLM-R, 24 layers) |

LaBSE vs LeBSE is the contrast a Cohere-vs-LaBSE comparison cannot give:
identical architecture and tokenizer, so it separates *training* from
*architecture*. Caveat to record: LeBSE is contrastively fine-tuned
(MultipleNegativesRankingLoss), which is itself known to reshape geometry — so
that arm confounds domain with objective.

## Statistics, and why not beta

`beta = dlog s / dlog r` divides by each corpus's own log-radius span, and the
corpora occupy DISJOINT bands (real 0.92-1.08, cascades 1.27-1.33, gaussian
1.32-1.36) with spans differing 6x. That inflates |beta| for narrow-band corpora
and makes cross-corpus comparison unsound — it is why a deep cascade appeared to
sit 7% from real on beta while sitting 2x away on a band-independent statistic.

So the headline here is the **k-matched ratio** s(k=500)/s(k=4) and its trend in
n, with beta reported alongside for continuity. Reference values measured on the
600k pool: real s_ratio 1.29 -> 2.37 with trend +0.511 per ln n; every control
flat near 1.2 or below with |trend| <= 0.13.

`||mean(X)||` is reported per arm because anisotropy (the "narrow cone") is the
first alternative explanation a reviewer raises, and the achieved radius band
tells us whether an arm is even comparable to real's.

## Registered reading, before the run

If NO arm produces a rising s(r) whose ratio strengthens with n, the ramp is
specific to Cohere Embed-V3 — the encoder route dies, and the family search
learns it has been chasing a property of one model rather than of text.

Env: F3_N, F3_NQ, F3_NS, F3_KMAX, F3_OUT, F3_CACHE_DIR, F3_THREADS.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

THREADS = os.environ.get("F3_THREADS", "6")
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, THREADS)

from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

BLOBS = ("/home/claude/.cache/huggingface/hub/"
         "datasets--CohereLabs--wikipedia-2023-11-embed-multilingual-v3/blobs")
OUT = os.environ.get("F3_OUT", "/home/claude/ovb_scale/f2_three_arm.json")
EMB_DIR = os.environ.get("F3_CACHE_DIR", "/archive/experiments/f2_arms")
NEED = int(os.environ.get("F3_N", "60000"))
NQ = int(os.environ.get("F3_NQ", "10000"))
NS = json.loads(os.environ.get("F3_NS", "[12500, 25000, 50000]"))
KMAX = int(os.environ.get("F3_KMAX", "500"))
PER_BLOB = 600

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})
ARMS = [("labse", "sentence-transformers/LaBSE"),
        ("lebse", "ahbond/lebse"),
        ("bge_m3", "BAAI/bge-m3")]


def load_paired(need: int):
    import pyarrow.parquet as pq

    files = [f for f in sorted(glob.glob(os.path.join(BLOBS, "*")))
             if not f.endswith(".lock")]
    texts, embs, got = [], [], 0
    for f in files:
        try:
            pf = pq.ParquetFile(f)
            b = next(pf.iter_batches(batch_size=PER_BLOB, columns=["text", "emb"]))
        except Exception:
            continue
        texts.extend(b.column("text").to_pylist())
        embs.append(np.asarray(b.column("emb").to_pylist(), dtype=np.float32))
        got = len(texts)
        if got >= need:
            break
    return texts[:need], np.concatenate(embs)[:need]


def profile(name: str, x: np.ndarray) -> dict:
    xn = normalize(x)
    q = xn[-NQ:]
    per_n, ratios, g1s, betas = {}, [], [], []
    for n in NS:
        d, _ = knn(xn[:n], q, KMAX)
        r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
        s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
        ratio = float(s[-1] / max(s[0], 1e-9))
        beta = float(np.log(max(s[-1], 1e-9) / max(s[0], 1e-9)) / np.log(r[-1] / r[0]))
        g1 = float(id_twonn(d))
        per_n[str(n)] = {"g1": g1, "s_lo": float(s[0]), "s_hi": float(s[-1]),
                         "s_ratio": ratio, "beta": beta,
                         "r_lo": float(r[0]), "r_hi": float(r[-1]),
                         "r": r.tolist(), "s": s.tolist()}
        ratios.append(ratio)
        g1s.append(g1)
        betas.append(beta)
        print(f"    {name:8s} n={n:6d} dim={x.shape[1]:4d} G1={g1:7.2f} "
              f"s {s[0]:6.1f}->{s[-1]:6.1f} ratio {ratio:.2f} beta {beta:+6.2f} "
              f"r [{r[0]:.3f},{r[-1]:.3f}]", flush=True)
    ln = np.log(NS)
    out = {"dim": int(x.shape[1]), "per_n": per_n,
           "s_ratio_trend": float(np.polyfit(ln, ratios, 1)[0]),
           "beta_trend": float(np.polyfit(ln, betas, 1)[0]),
           "g1_exponent": float(np.polyfit(ln, np.log(g1s), 1)[0]),
           "mean_norm": float(np.linalg.norm(xn.mean(0)))}
    print(f"  -> {name}: s_ratio trend {out['s_ratio_trend']:+.3f}/ln n, "
          f"G1 exp {out['g1_exponent']:+.3f}, ||mean|| {out['mean_norm']:.3f}",
          flush=True)
    return out


def encode(model_id: str, tag: str, texts: list[str]) -> np.ndarray:
    """Encode with progress, caching to disk so a crash costs nothing."""
    os.makedirs(EMB_DIR, exist_ok=True)
    path = os.path.join(EMB_DIR, f"{tag}_{len(texts)}.npy")
    if os.path.exists(path):
        print(f"  {tag}: cached {path}", flush=True)
        return np.load(path)
    from sentence_transformers import SentenceTransformer

    m = SentenceTransformer(model_id, device="cpu")
    chunks, t0, done = [], time.time(), 0
    STEP = 5000
    for i in range(0, len(texts), STEP):
        chunks.append(m.encode(texts[i:i + STEP], batch_size=16,
                               show_progress_bar=False,
                               convert_to_numpy=True).astype(np.float32))
        done += len(texts[i:i + STEP])
        el = time.time() - t0
        print(f"  {tag}: {done}/{len(texts)}  {done/el:.1f} sent/s  "
              f"eta {(len(texts)-done)/max(done/el,1e-9)/60:.0f} min", flush=True)
    x = np.concatenate(chunks)
    np.save(path, x)
    del m
    return x


def main() -> int:
    print(f"threads={THREADS} need={NEED} ns={NS} nq={NQ}", flush=True)
    texts, cohere = load_paired(NEED)
    # CRITICAL: rows arrive blob-by-blob and each parquet blob is a contiguous,
    # topically-clustered slice of Wikipedia. Taking the query set as the LAST
    # NQ rows would draw base and queries from disjoint blobs -> non-exchangeable
    # splits and badly distorted neighbour geometry. (Measured: that bug put
    # Cohere G1 at 65.7 against 26.0 on a properly-drawn pool.) Permute once,
    # with a fixed seed, so base and queries are i.i.d. from one distribution.
    perm = np.random.default_rng(20260808).permutation(len(texts))
    texts = [texts[i] for i in perm]
    cohere = cohere[perm]
    print(f"loaded {len(texts)} paired rows, cohere {cohere.shape}; "
          f"permuted for exchangeable base/query split", flush=True)

    results: dict = {}

    def save():
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"config": {"n": NEED, "ns": NS, "nq": NQ, "kmax": KMAX,
                                  "kgrid": KGRID, "arms": ARMS},
                       "results": results}, f, indent=2)

    print("\n[cohere reference]", flush=True)
    results["cohere"] = profile("cohere", cohere)
    save()

    for tag, model_id in ARMS:
        print(f"\n[{tag}] {model_id}", flush=True)
        try:
            x = encode(model_id, tag, texts)
            results[tag] = profile(tag, x)
            del x
        except Exception as e:
            print(f"  {tag} FAILED: {type(e).__name__}: {e}", flush=True)
            results[tag] = {"error": f"{type(e).__name__}: {e}"}
        save()

    print("\n=== F2 THREE-ARM SUMMARY ===", flush=True)
    print(f"{'arm':10s} {'dim':>5s} {'ratio@max_n':>12s} {'ratio trend':>12s} "
          f"{'G1 exp':>8s} {'||mean||':>9s}", flush=True)
    for k, v in results.items():
        if "error" in v:
            print(f"{k:10s} FAILED", flush=True)
            continue
        print(f"{k:10s} {v['dim']:5d} {v['per_n'][str(NS[-1])]['s_ratio']:12.2f} "
              f"{v['s_ratio_trend']:+12.3f} {v['g1_exponent']:+8.3f} "
              f"{v['mean_norm']:9.3f}", flush=True)
    print("\nreference (600k pool, real): ratio 2.37 @200k, trend +0.511, "
          "G1 exp -0.168; controls flat near 1.2 with |trend| <= 0.13", flush=True)
    save()
    print(f"wrote {OUT}", flush=True)
    print("F2_THREE_ARM_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
