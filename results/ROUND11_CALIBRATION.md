# Round 11 — pre-freeze calibration: the dial is real and monotone at the pool; pool→subsample transfer FAILS (the prereg's failure clause fires)

**Calibration only.** `PREREG_ROUND11.md` remains **DRAFT ⚪ — not frozen**; no
gates were scored, no admission ran, and nothing here freezes anything. The
prereg explicitly allows this one sweep before freeze ("Calibration allowed
BEFORE freeze: one sweep mapping (m, p, n_shell) → (S_k, count_max, RH) on the
pool, published with the prereg"). The freeze decision is the author's.

## Provenance

- Driver: `harness/rc1/r11_calibration.py` (commit `6cd9304`, which also adds
the `local_centers` primitive). The copy that ran on Atlas
(`/home/claude/r11/r11_calibration.py`, md5 `b147285d70935c7cb5e051654f99a8b0`)
is byte-identical to the committed file.
- Run: Atlas, 2026-07-24, log `/home/claude/r11/r11_calibration.log`, terminal
marker `R11_CALIBRATION_DONE`, wall ~26 min.
- Operating point: `fit_v10_result.json` params, nonparametric spectral target
`spectrum_target_wiki1024.json`; one 472,500-row dim-1024 seed-0 instance
generated once, the overlay re-applied per cell (isolates the dial).
- Pool 420,000 = max(N_GRID) + 220,000; ladders n ∈ {25k, 50k, 100k, 200k}
drawn with the grid's own sampling operator, 2 subsample draws each; k ∈
{10, 30, 100}; battery-A uniform holdout as query set; real corpus measured
under the identical protocol (sealed rows excluded, holdout seed 7).
- Dial grid: m ∈ {4,16,64} × p ∈ {2,8,32} × n_shell ∈ {512,2048,8192};
radius 0.15, center_jit 0.05. The 10% mass cap skipped 9/27 cells (all
m=16 s8192, all m=64 s2048 and s8192) — 18 dial cells + baseline + real
= 540 rows.
- Artifact: [`r11_calibration.json`](r11_calibration.json), md5
`a21ccaeaac543fb698eff5d759ed06b5`.

## 1. Dial table at the pool (n = 400,000 base rows after holdout)

(m, p, n_shell) → S_k count skew / count_max / Robin Hood index, per k.

| corpus | (m, p, n_shell) | S_k k10 | cmax k10 | RH k10 | S_k k30 | cmax k30 | RH k30 | S_k k100 | cmax k100 | RH k100 |
|---|---|---|---|---|---|---|---|---|---|---|
| r10_baseline | (0, 0, 0) | 3.25 | 15 | 0.807 | 2.74 | 27 | 0.577 | 2.44 | 76 | 0.413 |
| lc_m4_p2_s512 | (4, 2, 512) | 3.33 | 16 | 0.807 | 2.75 | 27 | 0.576 | 2.44 | 75 | 0.412 |
| lc_m4_p2_s2048 | (4, 2, 2048) | 11.68 | 56 | 0.807 | 3.78 | 56 | 0.575 | 2.51 | 77 | 0.411 |
| lc_m4_p2_s8192 | (4, 2, 8192) | 130.19 | 206 | 0.807 | 45.11 | 206 | 0.571 | 7.32 | 207 | 0.403 |
| lc_m4_p8_s512 | (4, 8, 512) | 3.42 | 12 | 0.807 | 2.73 | 20 | 0.576 | 2.42 | 76 | 0.413 |
| lc_m4_p8_s2048 | (4, 8, 2048) | 21.69 | 52 | 0.809 | 5.86 | 52 | 0.577 | 2.70 | 76 | 0.411 |
| lc_m4_p8_s8192 | (4, 8, 8192) | 101.90 | 204 | 0.816 | 64.12 | 204 | 0.576 | 16.35 | 207 | 0.404 |
| lc_m4_p32_s512 | (4, 32, 512) | 3.35 | 15 | 0.807 | 2.97 | 27 | 0.578 | 2.44 | 76 | 0.413 |
| lc_m4_p32_s2048 | (4, 32, 2048) | 8.21 | 25 | 0.810 | 13.62 | 58 | 0.585 | 3.68 | 72 | 0.413 |
| lc_m4_p32_s8192 | (4, 32, 8192) | 42.50 | 90 | 0.821 | 48.78 | 204 | 0.607 | 26.84 | 206 | 0.413 |
| lc_m16_p2_s512 | (16, 2, 512) | 3.71 | 16 | 0.807 | 2.78 | 27 | 0.575 | 2.44 | 76 | 0.411 |
| lc_m16_p2_s2048 | (16, 2, 2048) | 25.88 | 60 | 0.808 | 6.79 | 61 | 0.570 | 2.77 | 80 | 0.401 |
| lc_m16_p8_s512 | (16, 8, 512) | 5.62 | 19 | 0.809 | 2.99 | 27 | 0.576 | 2.43 | 72 | 0.410 |
| lc_m16_p8_s2048 | (16, 8, 2048) | 33.82 | 60 | 0.817 | 13.20 | 60 | 0.576 | 3.57 | 80 | 0.403 |
| lc_m16_p32_s512 | (16, 32, 512) | 3.58 | 15 | 0.810 | 3.49 | 26 | 0.584 | 2.45 | 77 | 0.412 |
| lc_m16_p32_s2048 | (16, 32, 2048) | 11.70 | 26 | 0.820 | 16.15 | 59 | 0.608 | 5.70 | 80 | 0.412 |
| lc_m64_p2_s512 | (64, 2, 512) | 5.39 | 20 | 0.807 | 2.94 | 23 | 0.570 | 2.43 | 80 | 0.400 |
| lc_m64_p8_s512 | (64, 8, 512) | 8.50 | 20 | 0.816 | 3.51 | 23 | 0.575 | 2.46 | 80 | 0.402 |
| lc_m64_p32_s512 | (64, 32, 512) | 4.24 | 15 | 0.818 | 4.57 | 23 | 0.605 | 2.52 | 79 | 0.409 |
| **real** | — | **2.30** | **5** | **0.799** | **1.61** | **12** | **0.532** | **1.46** | **33** | **0.331** |

What the pool response establishes:

1. **The mechanism claim holds at the pool.** count_max is set by n_shell
alone, near-deterministically and independent of m and p: ≈15–20 at s512
(below the background max — the dial is off), 52–61 at s2048, 204–207 at
s8192 — ≈ 0.025 × n_shell for n_shell ≥ 2048 (the holdout-query fraction of
the shell). S_k is monotone in the same direction; "G6's count-tail becomes
a dial" is confirmed *at the pool scope*.
2. **Slot competition behaves as predicted.** Per-row planted means at s2048
fall with p (p=2: ≈47, p=8: ≈44, p=32: ≈17) — planted count ≈
n_shell·(slots taken), matching the STRATA fixture response quoted in the
prereg.
3. **RH is not a dial output.** The Robin Hood index barely moves (0.807 →
0.821 at the heaviest overlays): the primitive moves the extreme tail
(S_k, count_max) without moving bulk count concentration. RH remains
diagnostic only at these mass fractions.

## 2. Pool → grid-subsample transfer — **FAILS; the failure clause fires**

S_k ratio to the real reference (measured at the same scope, same operator),
k = 10, mean over the 2 subsample draws:

| corpus | pool | n25000 | n50000 | n100000 | n200000 |
|---|---|---|---|---|---|
| r10_baseline | 1.42 | 1.40 | 1.57 | 1.62 | 1.59 |
| lc_m4_p2_s512 | 1.45 | 1.40 | 1.57 | 1.62 | 1.60 |
| lc_m4_p2_s2048 | 5.08 | 1.41 | 1.58 | 1.97 | 2.43 |
| lc_m4_p2_s8192 | 56.65 | 2.49 | 8.18 | 9.95 | 30.40 |
| lc_m4_p8_s2048 | 9.44 | 1.44 | 2.04 | 3.67 | 5.24 |
| lc_m4_p8_s8192 | 44.34 | 3.24 | 13.60 | 29.41 | 45.09 |
| lc_m4_p32_s8192 | 18.49 | 7.91 | 20.57 | 28.42 | 29.56 |
| lc_m16_p2_s2048 | 11.26 | 1.44 | 1.75 | 3.46 | 5.95 |
| lc_m16_p8_s2048 | 14.72 | 1.66 | 2.84 | 5.07 | 10.97 |
| lc_m16_p32_s2048 | 5.09 | 2.12 | 4.54 | 8.25 | 8.39 |
| lc_m64_p8_s512 | 3.70 | 1.40 | 1.60 | 1.86 | 2.67 |

(k=30 and k=100 show the same pattern, attenuated; full data in the JSON.)

**A dial setting calibrated at the pool does not hold its statistics on
subsampled ladders.** This is the prereg's named failure clause, and it fired.
Three measured components:

1. **Planted-row survival thins to nothing at low p.** Ladder retention is
n/400k (6.25% at n=25k, on top of the ~10% holdout). For p=2, m=4 (8 planted
rows, 6 surviving the holdout) the n=25k subsamples retain 0–1 planted rows —
one of the two draws contained **no planted row at all**: the dial is silently
off for that draw. The planted counts are literally thinned out of the
distribution, exactly as anticipated.
2. **The dial's effect is scale-covariant in the wrong way.** Surviving
planted rows keep their *absolute* counts roughly n-invariantly (the query
set is fixed: e.g. s8192 planted_max ≈ 204–208 at every scope; s2048 ≈
38–56), but the background count distribution and the real reference both
move strongly with n (real count_max at k10: 50.5 at n25k → 10.0 at n200k;
this is the same real-corpus thinning round 9 measured as the falling A-side
G1). The ratio statistic a pool calibration would freeze therefore swings by
more than an order of magnitude along one ladder: lc_m4_p2_s8192 at k10 runs
56.7× (pool) → 2.5× (n25k) → 30.4× (n200k). Any pool-frozen dial value
violates the |Δslope| ≤ 0.05/decade criterion before it ever reaches a gate.
3. **Subsample variance is large where the dial is strong.** Between the two
draws at fixed n, S_k differs by up to 26.9 (lc_m4_p2_s8192) and 10.3
(lc_m4_p8_s8192) — against 0.27 for the real reference and 0.35 for the
baseline. A handful of surviving planted rows makes the ladder statistic a
high-variance quantity; a single pool number is a point estimate of the wrong
distribution.

**Verdict, per the prereg's own words:** this is the sampling-operator lesson
(round 9, `ROUND9_RESULT.md` §"What round 9 established" item 2) recurring at
mechanism level. The fix is **subsample-aware calibration** — calibrate
(m, p, n_shell) against the ladder statistics under the grid's own operator,
with retention n/pool folded into the planted-mass budget — **not band
adjustment**. No band was touched here.

## 3. Coverage of the RC-1 battery-A G6/G1-relevant ranges

Real reference under this protocol (cross-checks `rc1_targets_v3.json`
battery-A `g6_hubness_skew`, which is 1.62–1.78 across n=25k cells; same
estimator family, step-1 conventions):

| scope | S_k k10 | S_k k30 | S_k k100 | cmax k10 | cmax k30 | cmax k100 |
|---|---|---|---|---|---|---|
| pool | 2.30 | 1.61 | 1.46 | 5 | 12 | 33 |
| n25000 | 1.76 | 1.90 | 1.89 | 50.5 | 117 | 318 |
| n50000 | 1.55 | 1.61 | 1.72 | 30 | 67.5 | 180.5 |
| n100000 | 1.61 | 1.58 | 1.73 | 16 | 43 | 122.5 |
| n200000 | 1.79 | 1.54 | 1.61 | 10 | 25 | 66 |

Against the RC-1 equivalence band [0.85, 1.15] on the 12 ladder cells
(4 n × 3 k):

- **The baseline is already out of band high in 12/12 cells** (S_k ratio
1.19–1.68, count_max ratio 1.25–2.14). This is the round-9/round-10 battery-A
G6 overshoot (1.54× in round 9, ~1.7× in round 10) reproduced under the count
protocol: the fit_v10 point carries too much emergent hub mass before any
planting.
- **`local_centers` moves S_k monotonically UP.** The overlay can only add
count-tail mass. Consequently **no dial region reaches the G6-relevant band
on the ladders**: best coverage is 1/12 cells (six settings touch band at the
single cell n25k/k100, ratios 1.10–1.14), and inspection shows those entries
come from shell mass inflating the count variance (the skewness denominator),
not from matching the tail — count_max in the same cells is still 1.36–1.45×
over. The dial's reachable range at the pool is [baseline … ≈57× real]; the
RC-1-relevant range lies *below* baseline.
- **Implication for H11:** the primitive does what the prereg says it does
(a near-deterministic count-tail dial), but from the fit_v10 operating point
the battery-A G6 gate is not reachable by the overlay alone in any (m, p,
n_shell) region measured. Reaching band requires jointly *reducing* the
emergent cloud/hub mass at the operating point (round-10 target 2, the
G1-slope/G6-level joint constraint) and then planting a subsample-calibrated
tail on top.
- **G1 was not measured in this sweep.** The calibration maps only the count
family (S_k, count_max, RH); G1 (TwoNN ID) and the origin-shell centrality
claim behind P-B are untested by this data. There is no G1 dial map yet — an
anatomy/G1 pass belongs in the pre-freeze protocol if P-B is to be frozen on
evidence rather than on the fixture argument.

## 4. Recommendation for the freeze decision (the author's call — nothing frozen here)

Do not freeze the prereg on pool-calibrated dial values: §2 shows any such
value gates on a statistic known not to transfer, and §3 shows the dial as
overlaid on fit_v10 cannot reach the G6 band in any measured region because
the baseline itself is out of band high. If round 11 proceeds, the evidence
supports amending the draft before freeze to:

1. **Subsample-aware calibration** (the prereg's own named fix): calibrate
(m, p, n_shell) per ladder n under the grid operator, with planted-mass
retention n/pool in the budget, and require the dial statistic to be stable
across the ladder (the |Δslope| criterion) *at calibration time*.
2. **A joint operating-point move**: lower the emergent hub mass (cloud
density) so the un-planted baseline sits at or below band, making the
monotone-up dial able to land inside it. As measured, the binding constraint
on battery-A G6 is the baseline overshoot, not dial reach.
3. **Add a G1/anatomy measurement to the pre-freeze protocol** so P-B is
frozen against data, not only the fixture construction.

The alternative — freezing as drafted — would register P-A against a
transfer already measured to fail, which the failure clause would then simply
report. That choice, either way, is the user's.

## Artifacts

[`r11_calibration.json`](r11_calibration.json) (this commit, md5
`a21ccaeaac543fb698eff5d759ed06b5`) · driver `harness/rc1/r11_calibration.py`
@ `6cd9304` (Atlas copy byte-identical) · run log
`/home/claude/r11/r11_calibration.log` (`R11_CALIBRATION_DONE`) ·
targets [`rc1_targets_v3.json`](rc1_targets_v3.json) · context
[`ROUND9_RESULT.md`](ROUND9_RESULT.md), [`PREREG_ROUND11.md`](PREREG_ROUND11.md).
