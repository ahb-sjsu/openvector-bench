"""F2 transfer test: is the geometry profile a property of the DATA or of one model?

`NORMAL_FORMS.md` F2 is a registered falsification criterion the campaign has
never tested: "the selected descriptor predicts within known datasets but fails
on unseen embedding models or modalities — this would make it a benchmarking
heuristic rather than a general theory."

`R21B_SCALE_DEPENDENCE.md` characterised the target as a curve: real (Cohere
Embed-V3, 1024-d) has s(r) rising 15.7 -> 37.3 with beta strengthening +1.80 ->
+4.80 across the ladder, and six generator families have now failed to
reproduce it. Before designing a seventh, it is worth knowing whether that
profile is a property of embedding geometry in general or an artifact of one
model.

Design: the SAME passages through two encoders.

* Cohere Embed-V3 (1024-d) — read directly from the `emb` column of the source
  parquets, so it is the exact vector the corpus was built from.
* LaBSE (768-d) — a BERT dual-encoder trained with translation ranking, which
  is a genuinely different architecture, objective and dimension.

Exact pairing is the point: both encoders see identical text, so any difference
in profile is the encoder, not the sample.

Sampling: ~`PER_BLOB` rows from each of many parquet blobs rather than a head
slice. A 110k head slice of this corpus was measured earlier and gave G1 ~17
flat against the registered 26.64 -> 19.92 falling — Wikipedia arrives topically
ordered and a contiguous slice is not representative. Spreading across blobs
restores a broad sample.

Readings:
1. **Sign and shape.** Does LaBSE also produce a RISING s(r)? Ambient dimension
   differs (768 vs 1024) so absolute levels are not comparable, but the shape
   and the direction are.
2. **beta and its n-trend.** Real's discriminator against every synthetic family
   was beta rising with n (+1.41 per ln n). Does LaBSE show it too?
3. **G1 ladder.** Does intrinsic dimension fall with n for LaBSE as it does for
   Cohere?

If LaBSE reproduces the profile, it is a property of embedding geometry and an
encoder-based generator is a live route. If it does not, F2 fires: the
descriptor is model-specific and the whole target is narrower than assumed.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.geometry import id_twonn, knn, normalize  # noqa: E402

CACHE = (
    "/home/claude/.cache/huggingface/hub/"
    "datasets--CohereLabs--wikipedia-2023-11-embed-multilingual-v3/blobs"
)
OUT = os.environ.get("F2_OUT", "/home/claude/ovb_scale/f2_transfer.json")
NS = json.loads(os.environ.get("F2_NS", "[25000, 50000, 100000]"))
NQ = int(os.environ.get("F2_NQ", "10000"))
KMAX = int(os.environ.get("F2_KMAX", "500"))
PER_BLOB = int(os.environ.get("F2_PER_BLOB", "1000"))
NEED = max(NS) + NQ
BATCH = int(os.environ.get("F2_BATCH", "16"))

KGRID = sorted({int(round(v)) for v in np.geomspace(4, KMAX, 16)})


def load_paired(need: int):
    """(texts, cohere_emb) spread across blobs, not a head slice."""
    import pyarrow.parquet as pq

    files = [
        f
        for f in sorted(glob.glob(os.path.join(CACHE, "*")))
        if not f.endswith(".lock")
    ]
    texts: list[str] = []
    embs: list[np.ndarray] = []
    got = 0
    for f in files:
        try:
            pf = pq.ParquetFile(f)
        except Exception:
            continue
        try:
            b = next(pf.iter_batches(batch_size=PER_BLOB, columns=["text", "emb"]))
        except StopIteration:
            continue
        t = b.column("text").to_pylist()
        e = np.asarray(b.column("emb").to_pylist(), dtype=np.float32)
        texts.extend(t)
        embs.append(e)
        got += len(t)
        if got % 20000 < PER_BLOB:
            print(f"  loaded {got}", flush=True)
        if got >= need:
            break
    x = np.concatenate(embs)[:need]
    return texts[:need], x


def curve(base: np.ndarray, q: np.ndarray) -> dict:
    d, _ = knn(base, q, KMAX)
    r = np.array([float(np.median(d[:, k - 1])) for k in KGRID])
    s = np.gradient(np.log(np.array(KGRID, dtype=float)), np.log(r))
    return {
        "k": KGRID,
        "r": r.tolist(),
        "s": s.tolist(),
        "s_lo": float(s[0]),
        "s_hi": float(s[-1]),
        "g1": float(id_twonn(d)),
        "beta": float(np.log(s[-1] / max(s[0], 1e-9)) / np.log(r[-1] / r[0])),
    }


def profile(name: str, x: np.ndarray, out: dict) -> None:
    xn = normalize(x)
    q = xn[-NQ:]
    out[name] = {}
    for n in NS:
        c = curve(xn[:n], q)
        out[name][str(n)] = c
        print(
            f"{name:8s} n={n:6d} dim={x.shape[1]:4d}  G1={c['g1']:7.2f}  "
            f"s {c['s_lo']:6.1f} -> {c['s_hi']:6.1f}  beta={c['beta']:+6.2f}  "
            f"r {c['r'][0]:.3f}..{c['r'][-1]:.3f}",
            flush=True,
        )
    b = [out[name][str(n)]["beta"] for n in NS]
    g = [out[name][str(n)]["g1"] for n in NS]
    out[name]["beta_trend"] = float(np.polyfit(np.log(NS), b, 1)[0])
    out[name]["g1_exponent"] = float(np.polyfit(np.log(NS), np.log(g), 1)[0])
    print(
        f"  -> {name}: beta_trend {out[name]['beta_trend']:+.2f} per ln n, "
        f"G1 exponent {out[name]['g1_exponent']:+.3f}",
        flush=True,
    )


def main() -> int:
    t0 = time.time()
    print(f"loading {NEED} paired rows ({PER_BLOB}/blob)", flush=True)
    texts, cohere = load_paired(NEED)
    print(
        f"got {len(texts)} texts, cohere {cohere.shape} in {time.time()-t0:.0f}s",
        flush=True,
    )

    import torch

    torch.set_num_threads(4)  # 20 took Atlas to 99C; 4 holds 78C
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("sentence-transformers/LaBSE", device="cpu")
    # throughput probe before committing to the full pass
    t = time.time()
    model.encode(texts[:256], batch_size=BATCH, show_progress_bar=False)
    rate = 256 / (time.time() - t)
    print(
        f"LaBSE CPU throughput ~{rate:.0f} sent/s -> "
        f"{len(texts)/rate/60:.0f} min for {len(texts)}",
        flush=True,
    )

    t = time.time()
    labse = model.encode(
        texts, batch_size=BATCH, show_progress_bar=False, convert_to_numpy=True
    ).astype(np.float32)
    print(f"LaBSE {labse.shape} in {(time.time()-t)/60:.1f} min", flush=True)

    out: dict = {}
    profile("cohere", cohere, out)
    profile("labse", labse, out)

    print("\n=== F2 comparison ===", flush=True)
    for name in ("cohere", "labse"):
        print(
            f"  {name:8s} beta_trend {out[name]['beta_trend']:+.2f}  "
            f"G1 exponent {out[name]['g1_exponent']:+.3f}",
            flush=True,
        )
    print("  registered real anchors: G1 exponent -0.168, beta_trend +1.41", flush=True)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "ns": NS,
                    "nq": NQ,
                    "kmax": KMAX,
                    "kgrid": KGRID,
                    "per_blob": PER_BLOB,
                    "n_texts": len(texts),
                },
                "results": out,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("F2_TRANSFER_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
