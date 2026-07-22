# Generator search — round 0 (exploratory): the loop moves, the substrate is too weak

**Run:** 2026-07-22, on the real target (Cohere Wikipedia Embed-V3, en, 1024-d)
at `/archive/tqp_real/wiki1024`. Driver:
[`harness/generator/explore_search.py`](../harness/generator/explore_search.py).

This is **not** RC-1: it is a *fitting* signal — a plain 50-eval random search
over the five `synth_corpus` knobs, battery B (query→corpus), n=15 000, k=10 —
run to answer one question before wiring the real engines: **does the fitness
loop move the mandatory gates (G1 intrinsic dimension, G6 hubness) at all?**

**Train/validation only.** The sealed 25% (PREREG_RC1 §7, hash of row index) is
never loaded; nothing here touches the seal, and no admission is claimed.

## Result: yes — it halves the gap and moves both mandatory gates

| candidate | G1 id_twonn | G6 hubness_skew | mismatch score |
|---|---:|---:|---:|
| **real target** | 52.6 | 3.78 | — |
| default knobs | 297.1 (5.64×) | 15.12 (4.00×) | 1.095 |
| low-rank-like point | 283.7 (5.39×) | 23.93 (6.33×) | 1.232 |
| **best of 50-eval search** | **127.6 (2.42×)** | **7.91 (2.09×)** | **0.558** |

Best knobs: `log2_clusters≈8.4` (~345 clusters), `size_tail≈2.36` (heavy),
`spectrum_decay≈0.47`, `cluster_spread≈0.87`, `noise≈0.03`.

Two readings:

- **The machinery works.** Random search over five knobs, in ~4 minutes, cut the
  weighted mismatch roughly in half (1.10 → 0.56) and pulled *both* mandatory
  gates from ~5–6× off toward real — G1 5.6× → 2.4×, G6 6.3× → 2.1×. The fitness
  is smooth enough to optimise, and hubness (the property `null_lowrank` cannot
  produce) is reachable: many clusters + a heavy size tail generate it.
- **The substrate is too weak.** Even the best point sits at 2.4× the real
  **intrinsic dimension** — the mixture-of-anisotropic-Gaussians family fills too
  many dimensions to reach real embeddings' ~52-dim manifold in 1024-d. The wall
  is G1, and no amount of the current five knobs closes it.

## What it implies for the next round

The block is now concrete: **reach real's low intrinsic dimension while keeping
the hubness the cluster/tail structure already supplies.** That is a *structural*
change to the generator family, not a re-tune of five scalars — exactly the job
for the two engines the scaffold was built for:

- **Theory Radar** — search over *family structure* (e.g. an explicit
  low-dimensional manifold with calibrated off-manifold noise), not just the
  knobs, minimising the same `evaluate_fn`.
- **structural-fuzzing** — hammer each surviving candidate's G1/G6 (and their
  N-scaling) to reject generators that match the level but not the mechanism.

Round 0 is a green light on the loop and a sharp diagnosis, **not** a generator:
nothing here passes RC-1, and the sealed test is untouched.
