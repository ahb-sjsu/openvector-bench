# R80: the ANN-behaviour characterization — geometry admission does not predict index behaviour

**Open characterization, not the sealed test.** Measured 2026-08-13 on
Atlas GPU 1. Identical IVF-flat pipelines (k-means K=1024, 20 iters, seed
7; 590k base / 10k exchangeable queries; exact GT) over three consumed
real blocks (3M/13M/23M — the sealed set untouched) and the frozen RC-3
generator at seeds 2027 and 41. Driver `harness/rc1/rc6_ann.py`; record
`results/rc6_ann.json`.

## The result

| statistic | real (3 blocks) | generator (2 seeds) | verdict |
|---|---|---|---|
| recall@10 at nprobe 1 | 0.533–0.536 | **0.914–0.917** | 1.7× apart |
| recall@10 at nprobe 8 | 0.823–0.828 | 0.981–0.982 | — |
| **nprobe for 95% recall** | **47–50** | **2** | **25× apart** |
| occupancy CV | 0.38–0.40 | 0.31 | close |
| occupancy skew | 0.61–0.88 | 0.44 | close-ish |
| max / top-10 cell share | 0.003 / 0.023–0.026 | 0.002 / 0.019 | close |
| median margin (r2−r1)/r1 | 0.051–0.052 | 0.054 | match |
| median margin (r10−r1)/r1 | 0.213–0.219 | 0.212–0.214 | match |

Both sides are internally tight (real block spread and generator seed
spread are each ~1% on every statistic), so the 25× gap is structural.

## The diagnosis

The generator's neighbours are **partition-friendly**: its coarse
structure *is* generative clusters (nested arrangement, segment centres),
k-means recovers them, and 92% of a query's true top-10 sit in the
query's own cell. Real is **partition-hostile**: roughly a third of its
true top-10 are cross-article, scattered across cells that no 1024-way
partition co-locates — its nprobe-1 recall (0.53) matches the same-
article share of the k=10 neighbourhood (`nn_index_gap`, paper §5), and
the remaining recall must be bought cell by cell. The property that
governs IVF difficulty is the **alignment between neighbour structure and
any recoverable partition** — and none of the ten registered geometric
criteria, nor the s(k) curve, nor the §3/§3b ladders, measures it.
Margins and occupancy — the statistics folklore associates with ANN
difficulty — nearly match while probe depth diverges 25×.

## The consequences

1. **The pre-registration's Goodhart concern is now measured, not
   hypothetical.** Geometric admission — even 8/10 held-out with the
   mandatory trio — would not have certified ANN behaviour. The sealed
   ANN-prediction gate (`GENERATOR_SEARCH.md` §5, the original RC-2
   sense) is *necessary*, and keeping it sealed until geometry passed was
   the correct order.
2. **The frozen generator must not ship as a benchmark tier**, even under
   a relaxed geometric gate: it would make IVF-family benchmarks
   trivially easy (95% recall at nprobe 2) and mis-rank systems that
   trade partition quality against other resources.
3. **The admission battery for any successor family needs a
   partition-scatter criterion** — e.g. same-cell neighbour fraction
   under a fixed k-means protocol, or nprobe@95 itself — registered
   alongside the geometric gates. This is the first known statistic on
   which the family fails *catastrophically* rather than marginally,
   which also makes it the most informative fitness signal a successor
   search could have.
4. For the paper's thesis, the finding extends cleanly: ANN difficulty,
   like the dimension profile, is a property of **corpus assembly
   relative to the index's partition** — the generator reproduces the
   assembly's local geometry but organizes its global cloud into exactly
   the structure a partitioner recovers.

## Budget

5 index builds; no sealed data touched; no held-out geometric blocks
consumed.
