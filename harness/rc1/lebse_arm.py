"""Repair and run the LeBSE arm of the F2 three-arm test.

The arm failed with `ModuleNotFoundError: No module named
'sentence_transformers.base'`. Cause: `ahbond/lebse` (and the local
`lebse-v2`) were saved with sentence-transformers **5.6.0**, whose
`modules.json` names classes under `sentence_transformers.base.modules.*` and
`sentence_transformers.sentence_transformer.modules.*`. Atlas has **5.3.0**,
where the same four classes live at `sentence_transformers.models.*`. The
weights are fine; only the module *paths* are unreadable.

(The HF cache entry on Atlas holds metadata only — no weights — so this uses
the full local copies under /archive/courtlistener/.)

Fix: copy the model to a writable directory and rewrite the four `type` fields.
v1 already uses the 5.3-compatible paths and is the fallback if v2 will not
load.

Protocol is inherited by importing the original driver, so the texts, the
permutation, the rungs, the k grid and the profile function are byte-identical
to the arms already measured. Results are merged into the existing report.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

THREADS = os.environ.get("LB_THREADS", "4")
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, THREADS)

sys.path.insert(0, "/home/claude/ovb_scale")

import numpy as np  # noqa: E402

import f2_three_arm as F  # noqa: E402  — inherit the exact protocol

SRC_V2 = "/archive/courtlistener/lebse-v2"
SRC_V1 = "/archive/courtlistener/lebse"
WORK = "/archive/experiments/lebse_fixed"

REMAP = {
    "sentence_transformers.base.modules.transformer.Transformer": "sentence_transformers.models.Transformer",
    "sentence_transformers.sentence_transformer.modules.pooling.Pooling": "sentence_transformers.models.Pooling",
    "sentence_transformers.base.modules.dense.Dense": "sentence_transformers.models.Dense",
    "sentence_transformers.sentence_transformer.modules.normalize.Normalize": "sentence_transformers.models.Normalize",
}


def prepare(src: str, dest: str) -> str:
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    mpath = os.path.join(dest, "modules.json")
    mods = json.load(open(mpath))
    changed = 0
    for m in mods:
        if m["type"] in REMAP:
            m["type"] = REMAP[m["type"]]
            changed += 1
    json.dump(mods, open(mpath, "w"), indent=2)
    print(f"  patched {changed}/{len(mods)} module paths in {dest}", flush=True)
    return dest


def main() -> int:
    texts, cohere = F.load_paired(F.NEED)
    perm = np.random.default_rng(20260808).permutation(len(texts))
    texts = [texts[i] for i in perm]
    print(f"reproduced {len(texts)} texts under the same permutation", flush=True)

    model_dir, tag = None, "lebse"
    for src, label in ((SRC_V2, "v2"), (SRC_V1, "v1")):
        if not os.path.isdir(src):
            continue
        try:
            d = prepare(src, WORK)
            from sentence_transformers import SentenceTransformer

            SentenceTransformer(d, device="cpu")  # load probe only
            model_dir = d
            tag = f"lebse_{label}"
            print(f"  {label} loads OK -> using it", flush=True)
            break
        except Exception as e:
            print(f"  {label} failed to load: {type(e).__name__}: {e}", flush=True)
    if model_dir is None:
        print("LEBSE_ARM_FAILED: no loadable LeBSE", flush=True)
        return 1

    x = F.encode(model_dir, tag, texts)
    res = F.profile(tag, x)

    report = json.load(open(F.OUT)) if os.path.exists(F.OUT) else {"results": {}}
    report["results"].pop("lebse", None)  # drop the failed placeholder
    report["results"][tag] = res
    with open(F.OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=== updated summary ===", flush=True)
    print(
        f"{'arm':12s} {'dim':>5s} {'ratio@max_n':>12s} {'ratio trend':>12s} "
        f"{'G1 exp':>8s} {'||mean||':>9s}",
        flush=True,
    )
    for k, v in report["results"].items():
        if "error" in v:
            continue
        print(
            f"{k:12s} {v['dim']:5d} "
            f"{v['per_n'][str(F.NS[-1])]['s_ratio']:12.2f} "
            f"{v['s_ratio_trend']:+12.3f} {v['g1_exponent']:+8.3f} "
            f"{v['mean_norm']:9.3f}",
            flush=True,
        )
    print(f"wrote {F.OUT}", flush=True)
    print("LEBSE_ARM_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
