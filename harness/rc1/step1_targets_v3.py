"""Round-9 protocol step 1 (ROUND9_PREDICTION.md): re-measure the real + null
targets under the REGISTERED uniform battery-A protocol.

Differences from ``geometry.main()``, both registered:
  * sealed rows (blake2b(i) % 4 == 3) are excluded from the pool — the v2
    runner assumed a pre-filtered pool; here the filter is explicit;
  * the battery-A holdout is a UNIFORM sample for every corpus (real AND
    nulls), per RC1_ROUND2_CANDIDATE.md finding 3 — first-rows holdout
    inherits the corpus's topical row ordering.

Output: RC_OUT (default /home/claude/r9/rc1_targets_v3.json), one cell per
(corpus, battery, n, k, subsample) — the v3 target set that all round-9
candidate scoring reads. Published before any candidate number is read.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict

import numpy as np

from openvector_bench import geometry as G

TARGET = os.environ.get("RC_TARGET", "/archive/tqp_real/wiki1024")
OUT = os.environ.get("RC_OUT", "/home/claude/r9/rc1_targets_v3.json")

_T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - _T0:7.0f}s] {msg}", flush=True)


def sealed(i: int) -> bool:
    return hashlib.blake2b(str(i).encode(), digest_size=1).digest()[0] % 4 == 3


def uniform_holdout(x: np.ndarray, hold: int, seed: int):
    rng = np.random.default_rng(seed)
    hidx = np.sort(rng.choice(len(x), size=hold, replace=False))
    mask = np.zeros(len(x), dtype=bool)
    mask[hidx] = True
    return x[mask], x[~mask]  # (queries, base)


def main() -> None:
    log(f"device={G._DEV} n_grid={G.N_GRID} k_grid={G.K_GRID} "
        f"subs={G.SUBSAMPLES} nq={G.N_QUERY}")
    corpus, real_q = G.load_target(
        TARGET, cap=int(os.environ.get("RC_CAP", str(max(G.N_GRID) * 3)))
    )
    keep = np.fromiter(
        (i for i in range(len(corpus)) if not sealed(i)), dtype=np.int64
    )
    corpus = np.asarray(corpus[keep])
    log(f"non-sealed pool {corpus.shape}; real queries "
        f"{None if real_q is None else real_q.shape}")
    eff, _ = G.spectrum(G.normalize(corpus[:50000]))
    rank = max(2, int(round(eff)))
    log(f"target effective rank {eff:.1f} -> null_lowrank rank {rank}")

    hold = min(G.N_QUERY * 2, len(corpus) // 10)
    corpus_q, corpus_base = uniform_holdout(corpus, hold, seed=7)

    cells: list[dict] = []
    for sub in range(G.SUBSAMPLES):
        for name in ("real", "null_gaussian", "null_shuffle", "null_lowrank"):
            if name == "real":
                base_x, qa, qb = corpus_base, corpus_q, real_q
            else:
                gen = {
                    "null_gaussian": lambda: G.null_gaussian(corpus_base, sub),
                    "null_shuffle": lambda: G.null_shuffle(corpus_base, sub),
                    "null_lowrank": lambda: G.null_lowrank(corpus_base, sub, rank),
                }[name]
                bx = gen()
                qa, base_x = uniform_holdout(bx, hold, seed=70 + sub)
                qb = None
            for n in G.N_GRID:
                if n > len(base_x):
                    continue
                for battery, qset in (("A_corpus", qa), ("B_query", qb)):
                    if qset is None:
                        continue
                    for c in G.measure(name, battery, base_x, qset, n, sub):
                        cells.append(asdict(c))
                    log(f"sub {sub} {name:13s} n={n:6d} {battery}  "
                        f"({len(cells)} cells)")
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(cells, f, indent=1)
    log(f"wrote {OUT}")
    print("STEP1_TARGETS_DONE", flush=True)


if __name__ == "__main__":
    main()
