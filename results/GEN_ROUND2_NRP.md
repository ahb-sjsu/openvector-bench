# Generator search — round 2: the `amp` decoupling is falsified; the adversary says why

**Run:** 2026-07-21, on an **NRP Nautilus swarm CPU pod** (cpu=1, mem=2Gi;
[`harness/generator/nrp_opt.py`](../harness/generator/nrp_opt.py) +
[`nrp_r2_job.yaml`](../harness/generator/nrp_r2_job.yaml)). Real-target profile
precomputed on Atlas and staged via ConfigMap; the pod generated its own synthetic
corpora — no corpus data, no GPU, no thermal budget. Bounded Nelder-Mead
(`maxfev=60`) from the round-1 corner, then the real **structural-fuzzing**
adversary. n=8000, battery B, k=10. Train/val only; seal untouched.

Round 2 split the manifold immersion into a linear part (meant to pin intrinsic
dimension to `latent_dim`) plus an `amp`-weighted high-frequency part (meant to
own effective rank), on the hypothesis that `amp` would **decouple** G1 from G3 —
letting the search reach low intrinsic dimension *and* high effective rank at
once. The directed search + adversary tested that hypothesis directly.

## Result: one real gain, one clean falsification

Real (n=8000): `G1 id=57.7, G3 eff-rank=187.9, G6 hubness=6.83, G8 pca-ret=0.62`.
Best point after 60 evals (score 0.870, barely below the corner's 0.896):

| gate | best | ratio |
|---|---:|---:|
| **G1 intrinsic dim** | 305 | **5.30×** |
| G3 effective rank | 151 | 0.80× |
| G6 hubness | 5.97 | 0.87× |
| G8 PCA retention | 0.076 | 0.12× |

Best knobs: `amp=0.64` (**unchanged from the corner's 0.6**), `curvature=3.0`
(max), `freq_scale=4.03`, `latent_dim=52.8`.

**The real gain (carried from round 1):** the decoupled family holds **effective
rank 0.80× and hubness 0.87× *together*** — round 1 could only get one at a time.
That co-existence is genuine and stays.

**The falsification:** `amp` does **not** decouple intrinsic dimension. The
directed search, free to lower `amp`, **left it at 0.64** and G1 stuck at 5.30×,
improving the score by almost nothing (0.896 → 0.870). The design intent — "small
`amp` ⇒ the linear part sets local dimension ⇒ ID → 52" — is false in practice.

## Why — the adversary localizes it exactly

`find_adversarial_threshold` nudged each knob until a gate broke, and named the
gate. The pattern is the whole story:

| knob nudged | first gate to break |
|---|---|
| `amp` (↑3.5× / ↓0.53×) | **G3 effective rank** |
| `freq_scale` (↑1.9× / ↓0.53×) | **G3 effective rank** |
| `curvature` (↓0.53×) | **G3 effective rank** |
| `latent_dim` (↑1.9× / ↓0.53×) | **G6 hubness** |

**No knob breaks G1.** `amp`, `freq_scale`, `curvature` are all *effective-rank*
controllers; `latent_dim` is a *hubness* controller. **Nothing in the family is an
intrinsic-dimension controller** — G1 sits at ~305 regardless. The reason the
split failed: the high-frequency term's *local* gradient scales as `amp ·
freq_scale`, and that same quantity sets both the local two-NN dimension **and**
the effective rank. The additive linear part never wins the local neighbourhood
unless `amp → 0`, which (the adversary confirms) collapses G3 first. The round-1
ID/eff-rank coupling was **relocated, not broken.** The best point is also a
**fragile ridge** — nudges as small as 0.53× topple a gate — exactly the
Goodhart spike the adversary exists to expose.

## Round 3 direction — the EC experiment already pointed the way

The elliptic-curve falsification ([`EC_FALSIFICATION.md`](EC_FALSIFICATION.md))
found that a flat 52-torus reads ID ≈ 345, not 52: **real embeddings hit ID ≈ 57
because they are *concentrated* (clustered, hierarchical → locally low-dimensional
neighbourhoods), not because of low nominal dimension.** A smooth random-Fourier
manifold is globally smooth but *locally wiggly* (high `freq_scale` folds it), so
the two-NN estimator reads a high local dimension no matter how low `latent_dim`
is. The fix is not a smoother manifold or another lift knob — it is
**concentration**: strong local linear structure (each cluster genuinely ~57-dim
in its own neighbourhood) whose clusters collectively span the effective rank.
That is round 3, and it is a *structural* change to the family, not a re-tune —
which is exactly the regime the searcher × adversary loop is built to drive.

Nothing here passes RC-1; the seal is untouched. Numbers:
[`results/gen_round2_nrp.json`](gen_round2_nrp.json).
