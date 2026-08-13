"""Separate DIMENSION from TRAINING: one encoder family, two widths.

`R23_F2_TRANSFER.md` established that the ramp is graded across encoders and
that **training data alone moves it** — LaBSE +0.072 vs LeBSE-v1 +0.267, same
BERT-base, same 768 dims, same tokenizer. That contrast held architecture fixed
and varied training.

This is its mirror: hold training fixed and vary dimension. `multilingual-e5`
ships `base` (768) and `large` (1024) trained on the same data with the same
recipe, so the pair isolates width in a way the LaBSE/BGE-M3 comparison cannot
(those differ in dimension, depth, family AND training at once).

Reading, registered before the run:

* **large ramps, base does not** -> dimension is doing the work, and the fact
  that the two strongest arms in R23 were both 1024-d stops being a
  coincidence.
* **both ramp similarly** -> dimension is not the driver; training and
  objective carry it, and R23's 1024-d pattern was confounding.
* **neither ramps** -> the e5 family simply does not produce the profile, which
  says nothing about dimension either way — a null result for the contrast, and
  it must be reported as such rather than as evidence for training.

Protocol is inherited by importing the F2 driver, so passages, permutation,
rungs, k grid and profile function are byte-identical to the arms already
measured; results merge into the same report.
"""

from __future__ import annotations

import json
import os
import sys

THREADS = os.environ.get("E5_THREADS", "4")
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, THREADS)

sys.path.insert(0, "/home/claude/ovb_scale")

import numpy as np  # noqa: E402

import f2_three_arm as F  # noqa: E402

ARMS = [("e5_base_768", "intfloat/multilingual-e5-base"),
        ("e5_large_1024", "intfloat/multilingual-e5-large")]


def main() -> int:
    texts, _ = F.load_paired(F.NEED)
    perm = np.random.default_rng(20260808).permutation(len(texts))
    texts = [texts[i] for i in perm]
    print(f"reproduced {len(texts)} texts under the same permutation", flush=True)

    report = json.load(open(F.OUT)) if os.path.exists(F.OUT) else {"results": {}}
    for tag, model_id in ARMS:
        print(f"\n[{tag}] {model_id}", flush=True)
        try:
            x = F.encode(model_id, tag, texts)
            report["results"][tag] = F.profile(tag, x)
            del x
        except Exception as e:
            print(f"  {tag} FAILED: {type(e).__name__}: {e}", flush=True)
            report["results"][tag] = {"error": f"{type(e).__name__}: {e}"}
        with open(F.OUT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    print("\n=== dimension vs training ===", flush=True)
    print(f"{'arm':14s} {'dim':>5s} {'ratio@max_n':>12s} {'ratio trend':>12s} "
          f"{'G1 exp':>8s}", flush=True)
    for k, v in report["results"].items():
        if "error" in v:
            print(f"{k:14s} FAILED", flush=True)
            continue
        print(f"{k:14s} {v['dim']:5d} {v['per_n'][str(F.NS[-1])]['s_ratio']:12.2f} "
              f"{v['s_ratio_trend']:+12.3f} {v['g1_exponent']:+8.3f}", flush=True)
    print("E5_DIM_ARM_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
