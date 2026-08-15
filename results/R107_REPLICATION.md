# R107: cross-corpus replication — the profile's shape replicates; battery B's signal is corpus-structural

**Status: measured, 2026-08-15.** Three new corpora under the exact
r101 protocol (uniform_holdout seed 7, N ∈ {25k, 50k, 100k, 200k},
k ∈ {10, 30, 100}, 3 subsamples, batteries A and B):

* **msmarco1024** — CohereLabs/msmarco-v2-embed-english-v3, 10M rows
  banked, 1024-d Embed-V3. *Same encoder as wiki1024, different text.*
* **dbpedia1536** — DBpedia entity abstracts, OpenAI ada-002 (1536-d),
  990k rows. *Different encoder family.*
* **dbpedia3072** — same entities, OpenAI text-embedding-3-large
  (1536-d; directory name is a misnomer). *Current-generation encoder.*

Battery-B queries are, as for wiki1024, held-out rows banked past each
download cap. Raw cells `results/r107_cells.json`; ANN difficulty
panels `results/r107_panels.json`. Wiki real cells reused from r101.

## Battery A: the profile vs density (k=10, medians over subs)

| gate | n | real wiki | msmarco | dbpedia-ada | dbpedia-3L |
|---|---|---|---|---|---|
| g1 two-NN ID | 25k→200k | 26.9→18.3 | 18.7→14.9 | 33.2→26.4 | 34.9→26.5 |
| g3 eff-rank | 25k→200k | 180 (flat) | 190 (flat) | 170 (flat) | 227 (flat) |
| g4 dims90 | 25k→200k | 362 (flat) | 396 (flat) | 457 (flat) | 610 (flat) |
| g5 rel-contrast | 25k→200k | 1.23→1.32 | 1.25→1.38 | 1.27→1.37 | 1.22→1.31 |
| g8 pca-retention | 25k→200k | .66→.68 ↑ | .66→.71 ↑ | .67→.66 ↓ | .66→.64 ↓ |

**Replicates:** the density response (local ID falling as density
rises) appears in all four corpora and all three encoders; rank
saturation (g3/g4 flat in n) and the contrast rise (g5 up with n)
replicate everywhere. **Diverges:** g8's direction flips on the entity
corpora — retention *falls* with density on DBpedia under both OpenAI
encoders. The profile's *shape* is universal in these four; its
*levels* are jointly encoder- and corpus-determined (same text under
ada-002 vs 3-large: g4 457 vs 610; same encoder on wiki vs msmarco:
g4 362 vs 396) — confirming §7: cross-corpus dimension comparisons
require matched protocol, and a dimension number without its corpus
and encoder is not a statistic.

## Battery B: the placement signal (B/A ratio, n=100k, k=10)

| gate | real wiki | msmarco | dbpedia-ada | dbpedia-3L |
|---|---|---|---|---|
| g1 two-NN ID | **3.01** | **3.46** | 1.29 | 0.97 |
| g8 pca-retention | 0.86 | 0.83 | 0.96 | 0.99 |
| g3 / g4 | 1.00 | 1.00 | 1.00 | 1.00 |

The battery-B phenomenon — query rows experiencing ~3× the local ID of
exchangeable holdout rows — **replicates at full strength on MSMARCO**
(×3.46) and *vanishes on DBpedia* (×1.29, ×0.97). The explanation is
structural: wiki and msmarco battery-B rows come from far past the
10M-row cap of a topically-ordered stream — a genuinely different
corpus region — while the 1M-row DBpedia sets have no "far"; their
past-cap rows are near-exchangeable with the base. Battery B therefore
measures **corpus-region non-exchangeability**: large ordered corpora
carry region-to-region placement drift that any exchangeable model
(including our generator, and including the corpus's own uniform
holdout) fails to reproduce. This sharpens, and is fully consistent
with, §15's conclusion — the information battery B detects is carried
by the data's arrangement at scales beyond any single region, which is
exactly what a compressed artifact cannot supply per-row.

## ANN difficulty spread (R80 protocol, np@95)

real wiki 47–50 · **dbpedia-3L 51** · dbpedia-ada 25 · **msmarco 18** ·
S1 candidate 10–11 · RC-3 generator 2.

Real corpora spread ~3× on IVF difficulty; wiki1024 sits at the hard
end, and the S1 family (np@95 10–11, R106) is within 2× of a real
web-passage corpus. R80's "25× easier" is a statement about wiki1024
specifically; the corpus-relative caveat belongs in §13.
