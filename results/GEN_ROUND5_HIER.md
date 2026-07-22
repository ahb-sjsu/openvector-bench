# Generator search — round 5: hubness is solved, and P1 is falsified — G6 and G3 are a genuine trade-off

**Run:** 2026-07-22, NRP Nautilus, 12-shard swarm (indexed Job, cpu=1 each; 480
random-search evals + anchored defaults). n=8000, battery B, k=10, train/val only,
seal untouched. Family: `hier_concentration_corpus`. Pre-registration (smoke
disclosed): [`HIER_PREDICTION.md`](HIER_PREDICTION.md).

## Result against the registered predictions

Real (n=8k): `G1 id=57.7, G3 eff-rank=187.9, G6 hubness=6.83, G7 local-ID IQR=20.8,
G8 pca-ret=0.62`. All 12 shards, best point each (full table in
[`gen_round5_hier.json`](gen_round5_hier.json)):

**The wall fell.** G6 hubness — 0.13–0.23× across *every* shard of *every* prior
cluster family — now reads **0.67–2.55× on 11 of 12 shards**. The round-4 diagnosis
was right: hubness is angular density variation, and heavy-tailed hierarchical
*centre placement* manufactures it directly. The mechanism overshoots on demand
(shard 9: 2.55×), so the knob has range in both directions.

**P1 — FALSIFIED, by its registered falsifier.** No shard found the joint point:
every shard with G6 ≥ 0.5× has **G3 ≤ 0.05×**, and the single G3-matching shard
(shard 1: G3 = 1.13×) sits back on the hubness wall at **G6 = 0.24×**. The search
mapped a clean two-ended Pareto frontier with nothing in the middle. Full battery
at the two endpoints:

| gate | shard 4 ("hub end") | shard 1 ("rank end") | real |
|---|---:|---:|---:|
| G1 intrinsic dim | 68.1 (**1.18×**) | 33.2 (0.58×) | 57.7 |
| G2 ball-growth id | 10.7 (0.71×) | 0.3 (0.02×) | 15.1 |
| G3 effective rank | 1.9 (**0.01×**) | 211.6 (**1.13×**) | 187.9 |
| G4 dims90 | 57 (0.16×) | 517 (1.46×) | 355 |
| G5 relative contrast | 2.17 (1.83×) | 1.06 (0.89×) | 1.18 |
| G6 hubness | 6.27 (**0.92×**) | 1.61 (**0.24×**) | 6.83 |
| G7 local-ID IQR | 22.0 (**1.06×**) | 25.9 (1.24×) | 20.8 |
| G8 PCA retention | 0.43 (0.69×) | 0.52 (0.84×) | 0.62 |

**P2 — supported at the edge of its band.** At the hub end the local-patch gates
survive the hierarchy: G1 = 1.18× ✓, G7 = 1.06× ✓, G8 = 0.69× — **one point below
the registered [0.7, 1.3] floor**, reported as the marginal miss it is. The
"flat patch in a random subspace" story holds; it is the *global* spectrum that
the hierarchy destroys, not the local structure.

**P3 — the honest risk fired, and it is the round's finding.** The same knobs
(`n_levels`, `level_decay`, `branch_tail`) drive hubness and rank with opposite
signs, exactly as registered: deep/heavy-tailed hierarchy concentrates the corpus
onto a few codebook directions (Zipf mass ⇒ a handful of dominant angular modes ⇒
rank collapse), while flattening the hierarchy to recover rank erases the density
gradient. **Codebook geometry alone cannot decouple the hub directions from the
spectrum directions.** The registered conclusion applies: hubness and rank need
*separate mechanisms*.

## The scoreboard after five rounds

Every mandatory gate has now been individually solved, each by a named mechanism:

| gate | solved by | round |
|---|---|---|
| G1 intrinsic dim | flat local patches (concentration) | 3 |
| G3 effective rank | many independent subspaces / Mahalanobis colouring | 3 / probe |
| G6 hubness | heavy-tailed hierarchical centre placement | **5** |
| G7 local-ID spread | Whitney-flag dimension spectrum | 4 |
| G8 PCA retention | Grassmannian subspace diversity | 3 |

What no family has done is hold them **all at once** — and round 5 sharpened where
the remaining tension lives: it is exactly one axis, **G6 × G3**.

## Round 6 direction (registered in P3): separate the mechanisms

Compose the two knobs that each own one end of the frontier: hierarchical
Zipf centre *placement* (this round's G6 mechanism) applied **inside** a
high-rank designed (Mahalanobis) colouring (the codebook probe's confirmed G3
knob, `spectrum_decay`) — i.e. make the hubs by *where* the centres sit, then
restore the spectrum by *colouring* the ambient space, so the density gradient
and the covariance spectrum are set by different parts of the construction. The
codebook probe already showed the colouring moves G3 385 → 4 independently of
cluster structure; the open question for round 6 is whether it preserves the
angular hubs while doing so.

Nothing here passes RC-1; the seal is untouched. Numbers:
[`results/gen_round5_hier.json`](gen_round5_hier.json).
