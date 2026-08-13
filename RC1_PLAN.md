# RC-1 generator: full re-evaluation and completion plan

**Written 2026-08-13, after R21–R61 (50 commits this campaign).** This document
re-states the problem, scores every completion criterion against the best
measured configuration, gives root-cause analyses for each open failure, and
lays out a phased plan with predictions and kill-criteria per phase.

---

## 1. The problem, restated

RC-1 requires a **deterministic, byte-reproducible, random-access generator**
whose geometry matches Cohere Embed-V3 over dense Wikipedia (1024-d), admitted
against criteria registered *before* any candidate was seen:

1. **Eight geometric gates** (`PREREG_RC1` §5), g1/g5/g6 mandatory.
2. **The scale-resolved profile** (`spec/PROFILE.md` §3): four-rung ladder,
   ratio trend +0.4512 ± 0.0988, G1 exponent −0.1696 ± 0.0287, per-rung ratios
   within ±2 sd.
3. **The density ladder** (`spec/PROFILE.md` §3b): ratio span +2.397 ± 0.085
   **and** log G1 span −0.494 ± 0.054, both in band.
4. **Distribution requirements** (`spec/DISTRIBUTION.md`): bit-exact,
   random-access, cross-toolchain, emission ≥ ~10 MB/s/core so regeneration
   beats fetching.

The verdict protocol is RC-2: freeze and hash the generator, evaluate **once**.

## 2. Scorecard — best family (segment_gen, R56–R61) vs every criterion

Two operating points matter, and they do not coincide:
**P_A** = brk 0.143 / w_loc 0.6 / d_glob 30 (best curve, R58) and
**P_B** = brk 0.030 / w_loc 0.6 / d_glob 30 (§3b ratio-span in band, R61).

| criterion | real / band | best measured | at | status |
|---|---|---|---|---|
| g1 id_twonn * | 17.23 | 4.31–4.87 | everywhere | **✗ 3.5×, invariant to 4 levers** |
| g5 rel_contrast * | 1.369 | 1.354 | P_A | ✓ there; 1.596 at P_B |
| g6 hubness * | 1.696 | 1.681 | P_B | ✓ there; 1.932 at P_A |
| g3 eff_rank | 182.3 | 122–141 | — | ✗ ~30% low |
| g4 dims90 | 359 | 715–717 | — | ✗ 2× high |
| g8 pca_retention | 0.730 | — | — | **never measured** |
| s(4), s(14) | 8.82, 16.08 | 8.2, 16.3 | P_A | ✓ simultaneously |
| s(53), s(500) | 28.88, 35.73 | 23.7, 41.9 | P_A | ✗ one shape defect |
| §3 four-rung ladder | trend +0.451 | — | — | **never measured on this family** |
| §3b ratio span | [+2.227, +2.567] | +2.420 | P_B | ✓ there |
| §3b log G1 span | [−0.602, −0.386] | −0.417 | w_loc 1.15 | ✓ there; −0.889 at P_B |
| §3b **jointly** | both | — | — | ✗ windows disjoint in w_loc (R61) |
| bit-exact / random access / cross-toolchain | required | verified to row 10¹⁴ | — | ✓ (R48, R50, port) |
| emission rate | ~10 MB/s/core | 1.76 MB/s | — | ✗ 6× slow |

**No single configuration currently co-holds any two of the starred items.**
That, not any individual miss, is the true state.

**Assets that do not depend on the generator:** the anatomical model of real
(articles ~23, segments with heavy-tailed lengths, two converging regimes,
adjacency mechanism with its permutation control, P(d|gap) mixture shape), the
registered protocol infrastructure, `hashrng` + `reproducible_matmul`, and the
60-second NRP pod profile that makes a four-arm sweep cost a minute.

## 3. Root causes of the open failures

### 3.1 g1 — quantized nearest-neighbour shells (new diagnosis, quantitative)

R60 found g1 invariant to `d_glob`, `fil_dim`, `brk` (including 0); R61 adds
`w_loc` (4.41–4.55 across 0.35–1.30). The mechanism: in a pure dyadic path,
adjacent rows differ at level 0; gap-2 rows at levels 0+1. The two-NN ratio is
therefore pinned at

```
mu ≈ sqrt(1 + w1²/w0²) = sqrt(1 + decay)
```

— a constant that **none of the swept levers touches**. The path level-variance
decay has been 0.72 since R49: the ninth held-fixed parameter of this arc.

* decay 0.72 → mu 1.311 → TwoNN ≈ 3.7. **Measured: 4.3–4.9.** ✓
* real g1 17.23 → mu 1.060 → **decay ≈ 0.125.**

Two candidate fixes, distinguished by anatomy:
(a) **steepen the decay** to ~0.125 — quantitatively predicted to hit 17, but
levels ≥ 2 become negligible, likely breaking the emergent autocorrelation;
(b) **reintroduce the ball/path mixture within segments** — R42 measured
directly that mix 0.4 gives g1 17.01. Real's k=1 neighbour sits at median index
gap **3**, not 1 (R34): its article is a cloud, not a chain. The mixture
reproduces that; a steeper decay does not. The discriminating measurement is the
**median index gap of the k=1 neighbour** (real: 3; pure path: 1), which becomes
a new anatomical target.

### 3.2 §3b disjointness — a stale verdict

R61's "spans never jointly reachable" was measured in a family whose G1 is
pinned at ~4.4 by §3.1. The log G1 span *contains* G1 at both densities. Once g1
is healthy the span recomputes from different numbers entirely, so the
disjointness conclusion is **conditional on the broken mechanism** and must be
re-adjudicated after Phase A, not before.

### 3.3 s(53)/s(500) — the one unimplemented measured fix

More arrangement levels: refuted (R58). Contiguous sections: refuted (R50).
What has never been implemented is **R39's finding**: real's neighbourhood
subspaces share structure (mean principal angle 68° vs the generator's 80°,
local eff_rank ≈ global 168≈182 vs the generator's divergent 176/111).
Correlated direction sets — articles within a 27-cluster drawing a fraction of
their pool indices from a cluster-shared set, hierarchically keyed so random
access survives — is the indicated mechanism for s(53), g3 and g4 at once, and
it has direct measured support that nothing else touching those quantities has.

### 3.4 Emission rate — constant factors, not architecture

Deduplication bought 20%, so the cost is the ~350 pool gathers/row and the
pure-numpy splitmix64 path (12 hash rounds × dims × levels, with uint64→float64
temporaries). In C/numba, splitmix64 is ~1 ns/op; the 6× gap is a compiled-
kernel problem, not a design problem. The oracle pattern from R55
(`hashgpu.verify`: numpy stays the reference, the fast path asserts bit-equality
at startup) transfers directly.

## 4. The plan

Each phase is one to three NRP sweeps (~60 s each) unless noted. Every phase
carries a prediction and a kill-criterion; anatomy is measured alongside
summaries so nothing passes for the wrong reason (the R46/R57 lesson).

**Phase A — fix g1.**
Sweep decay ∈ {0.125, 0.3, 0.5, 0.72} × mix ∈ {pure path, 0.4 ball}.
Measure: registered g1, k=1 NN index-gap median, autocorrelation curve, s(k),
g5, g6, D_article.
*Prediction:* decay 0.125 → g1 ≈ 17 (confirms mechanism); mix 0.4 → g1 ≈ 17
with NN-gap ≈ 3 (delivers the fix anatomically).
*Kill:* decay 0.125 leaving g1 < 8 falsifies §3.1; mixture then stands on R42's
direct evidence alone or the family closes on g1.

**Phase B — re-adjudicate §3b.**
2-D sweep (w_loc × brk) at the Phase-A configuration; both spans + g5/g6.
*Prediction:* none offered — this is adjudication, not tuning.
*Kill:* spans still disjoint with healthy g1 → §3b declared structurally
unreachable for the family; that is a registered-criterion discrimination
result and goes in the paper.

**Phase C — alignment for s(53)/g3/g4.**
Implement shared-fraction direction sets (ρ ∈ {0, 0.3, 0.6, 0.9}).
Measure: subspace angle (target 68°), local-vs-global eff_rank pattern
(target 168/182), s(53) (target 28.9), g4 (target 359).
*Kill:* angle reaches ~68° with s(53) unmoved → R39's discriminator is a
correlate, not a mechanism; record and stop this thread.

**Phase D — full audit, one configuration.**
Before it: re-band the s(k) curve targets on corpus blocks 2–4 (current curve
targets are single-block; the ladder targets already have four-block sd).
Then one indexed job: all eight gates **including g8**, the **§3 four-rung
ladder (never yet run on this family)**, both §3b spans, s(k) vs banded
targets, anatomy panel (D_article, overlap, NN-gap, P(d|gap)).

**Phase E — throughput.**
Numba/C port of the `hashrng` hot path behind the numpy oracle with mandatory
bit-equality verification at startup. Target ≥ 10 MB/s/core.
*Kill:* if a verified compiled kernel still misses, present the
mirror-vs-regeneration decision explicitly — that is a design call, not a
tuning target.

**Phase F — freeze, or close.**
If Phase D holds bands: freeze parameters, hash generator + manifest, disclose
the **full search budget** (per `GENERATOR_SEARCH` §5.3 — the R54–R61 arc alone
is ~200 arms and must be tallied), then evaluate **once** on held-out protocol:
new seed, corpus blocks 5–6 as targets — which simultaneously services
`PROFILE.md` falsifier P1. If Phase D fails: write the closing document; the
paper's "no generator is offered" section becomes "the best constructed family
and the criteria that exclude it", which is a publishable negative.

## 5. Rigor accounting

* **Multiple comparisons.** The arc's budget is large and must be disclosed in
  full at freeze. The one-shot held-out evaluation in Phase F is the control.
* **Anatomy over summaries.** Every sweep reports the anatomical panel; the
  arc's recurring failure (six instances) was optimising a summary satisfied by
  the wrong geometry.
* **Held-fixed parameters.** Nine instances of "invariant" conclusions caused by
  unswept parameters. Phase A's decay sweep exists because of this pattern;
  any future invariance claim requires listing what was *not* varied.
* **Split hygiene.** The R23 non-exchangeable split has recurred four times,
  including in this document's own preparatory check. `exchangeable_split` is
  mandatory in every new driver.

## 6. What completion means

Two legitimate endpoints, decided by Phase D:

1. **RC-1 admission**: all bands hold at one frozen configuration → RC-2
   one-shot verdict.
2. **Documented exclusion**: the anatomically-constructed best family, with
   every matched quantity and the specific registered criteria that exclude
   it — folded into the measurement paper, whose central claim (the profile
   measures corpus assembly, not embedding) is already established either way.

Estimated effort: Phases A–C a day of sweeps; D one day including re-banding;
E one to two days of kernel work; F one day. The bottleneck is adjudication
honesty, not compute — a four-arm sweep costs a minute.
