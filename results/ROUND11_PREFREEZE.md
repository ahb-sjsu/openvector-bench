# Round 11 v2 — pre-freeze result: the operating-point move FAILS; the v2 second failure clause fires (joint-constraint infeasibility at the fit_v10 family level)

**Calibration only.** [`PREREG_ROUND11.md`](PREREG_ROUND11.md) remains **DRAFT
⚪ — not frozen**; no gates were scored, no grid admission ran, the sealed 25%
was not touched, and nothing here freezes, retires, or redirects anything —
those are the author's calls. This document executes stage 1 of the v2
pre-freeze program (the operating-point move) and reports its registered
outcome. Stages 2 (subsample-aware dial calibration) and 3 (G1/anatomy pass)
are conditioned by v2 on a *moved* operating point; **no such point exists in
the family**, so they were not run — per v2's own second failure clause, that
result is the deliverable, not a detour around it.

## Verdict, in one paragraph

Across 17 candidate operating points spanning every hub-mass knob of the
fit_v10 family — the cloud pair the prereg names (`cloud_mass`, `cloud_tail`)
plus the non-cloud density-gradient knobs (`branch_tail`, `size_tail`,
`equalize`) — **no un-planted baseline reaches the G6 band on the
grid-subsampled ladders**, and the two levers that move the count tail at all
each break a mandatory companion: removing cloud mass degrades G1 from 2.5×
to 3.7× (the clouds are the family's G1 pinning mechanism), and flattening
the branch hierarchy rotates the (n, k) count profile through the band rather
than lowering it onto the band, driving G5 further out (1.17× → 1.28×) and
violating |Δslope| ≤ 0.05/decade by up to 0.64/decade. This is the prereg's
named outcome: *"a joint-constraint infeasibility finding at the fit_v10
family level … the round-9 'NOT ADMITTED' outcome recurring at the
operating-point level, [which] would redirect round 12 at the fitted family,
not the dial."*

## Provenance

- Drivers (this commit): [`harness/rc1/r11v2_stage1.py`](../harness/rc1/r11v2_stage1.py)
(committed md5 `99aaf9a4c68ac7a6a4b1710acdc9586c`, byte-identical to the
wave-2 Atlas copy; the wave-1 Atlas copy, md5
`a103822c05a75f4c9e7790e147b239d7`, differed only by the absence of the
`R11V2_GRID` env hook added afterward for wave 2 — the measurement path is
identical). Stage-2/3 drivers
[`r11v2_stage2.py`](../harness/rc1/r11v2_stage2.py) /
[`r11v2_stage3.py`](../harness/rc1/r11v2_stage3.py) are committed **unrun**:
they implement the v2 criteria in full and run unchanged the day a viable
operating point exists.
- Runs: Atlas, 2026-07-24, named screens `r11v2s1` / `r11v2s1b`, logs
`/home/claude/r11v2/stage1.screen.log` (~11 min) and `stage1b.screen.log`
(~8 min), terminal marker `R11V2_STAGE1_DONE` in both. CPU path (torch
cu130 wheel sees no CUDA under driver 12.8), OMP 20 threads, package-0
≤ 82 °C throughout. NRP/kubectl untouched.
- Artifacts (md5s verified identical local ↔ Atlas):
[`r11v2_real_ref.json`](r11v2_real_ref.json)
(`800d1c3a2c1437159b873dc14f767c3c`),
[`r11v2_stage1.json`](r11v2_stage1.json)
(`88ecdee63476e6d47eb4b253e02e3c5e`, cloud wave + `op_cmass0` verification),
[`r11v2_stage1b.json`](r11v2_stage1b.json)
(`ef3839ee7a9dbbf7b5986442349353d1`, non-cloud wave + `op_branch_tail0.2`
verification).
- Protocol: pool 420,000 (fit AT the pool, round-10 rule), instance 472,500
dim-1024 seed-0 per candidate; battery-A uniform holdout (20,000, seed 70);
ladders n ∈ {25k, 50k, 100k, 200k} under `measure()`'s own subsample
operator; k ∈ {10, 30, 100}; ratios always against the real reference at the
same (scope, draw, k). "At or below band" = S_k ratio ≤ 1.15 and count_max
ratio ≤ 1.20 (RC-1 §5 bands); G3/G4/G5 spot band [0.85, 1.15]; G1 recorded
alongside. Search phase: ladder ends {25k, 200k}, 1 draw; verification: full
12 cells, 3 draws, + pool diagnostics.

## 1. Real reference (5 draws per ladder n — reusable by any later stage-2 run)

Cross-checks `rc1_targets_v3.json` battery-A under the same estimator family
(G1 26.9 at n25k vs the registered 26.6/27.1; G6 skew family 1.5–1.8).

| scope | S_k k10 (min–max over draws) | S_k k30 | S_k k100 | cmax k10 | cmax k30 | cmax k100 | G1 | G3 | G5 k10 |
|---|---|---|---|---|---|---|---|---|---|
| n25000 | 1.60 (1.43–1.89) | 1.75 | 1.75 | 42.0 | 107.0 | 298.4 | 26.9 | 179.1 | 1.230 |
| n50000 | 1.51 (1.47–1.62) | 1.64 | 1.78 | 24.8 | 64.4 | 188.4 | 22.5 | 179.4 | 1.256 |
| n100000 | 1.58 (1.54–1.62) | 1.53 | 1.69 | 14.2 | 37.4 | 113.4 | 19.7 | 179.6 | 1.285 |
| n200000 | 1.79 (1.79–1.80) | 1.51 | 1.58 | 9.4 | 23.8 | 63.0 | 18.1 | 180.0 | 1.322 |

Context for the stage-2 variance criterion: the real corpus's own
between-draw S_k spread at n25k is 0.46 absolute (≈ 0.29 in ratio units) —
the band-width ceiling (0.30) sits at the real draw noise, i.e. it is a
demand for *real-like* draw stability, not super-real stability.

## 2. Wave 1 — the cloud knobs (the prereg's named lever) do not own the ladder count tail

Search cells (n ∈ {25k, 200k}, sub 0; ranges over k ∈ {10, 30, 100}; ratios
to real, same cell):

| candidate | n25k S_k | n25k cmax | n200k S_k | n200k cmax | G1 25k/200k | G3 | G5 max |
|---|---|---|---|---|---|---|---|
| fit_v10 control | 1.21–1.47 | 1.21–1.96 | 1.55–1.69 | 1.60–2.52 | 1.96 / 2.49 | 0.85 | 1.19 |
| cloud_mass 0.15 | 1.32–2.10 | 1.69–2.78 | 1.58–1.72 | 1.65–2.57 | 2.01 / 3.03 | 0.85 | 1.19 |
| cloud_mass 0.10 | 1.20–1.46 | 1.12–1.51 | 1.46–1.69 | 1.23–2.14 | 2.10 / 3.22 | 0.85 | 1.19 |
| cloud_mass 0.05 | 1.72–2.60 | 1.86–3.71 | 1.58–1.73 | 1.58–2.27 | 2.16 / 3.44 | 0.85 | 1.18 |
| cloud_mass 0 | 1.25–1.42 | 1.04–1.47 | 1.49–1.66 | 1.39–2.02 | 2.25 / 3.74 | 0.85 | 1.19 |
| cloud_tail 0.5 | 1.25–1.49 | 1.25–1.99 | 1.56–1.72 | 1.65–2.48 | 2.09 / 0.81* | 0.85 | 1.19 |
| cm 0.15 + ct 0.5 | 1.33–2.00 | 1.68–2.94 | 1.54–1.74 | 1.58–2.54 | 2.15 / 1.44* | 0.85 | 1.19 |
| cm 0.10 + ct 0.5 | 1.20–1.46 | 1.10–1.53 | 1.46–1.69 | 1.15–2.22 | 2.18 / 3.03 | 0.85 | 1.19 |
| cm 0.05 + ct 0.5 | 1.72–2.66 | 1.84–3.67 | 1.61–1.74 | 1.50–2.41 | 2.20 / 3.44 | 0.85 | 1.19 |

\* single-draw trimmed-two-NN readings at n200k under `cloud_tail` moves are
unstable (0.81/1.44 vs the 2.5–3.7 family line) — an estimator-fragility
observation, recorded, not relied on.

Three measured findings:

1. **The n ≥ 50k count overshoot is invariant to the cloud knobs.** S_k
ratio at n200k stays 1.46–1.74 from `cloud_mass` 0.203 all the way to 0 and
across both `cloud_tail` arms. The prereg's named operating-point lever does
not control the statistic the move must lower.
2. **Clouds are load-bearing for G1.** A-side G1 degrades monotonically as
cloud mass is removed: 2.49× → 3.74× at n200k (2.0× → 2.25× at n25k). The
graded near-duplicate ladder is the family's only G1-pinning mechanism
(round-9 diagnosis), so the named lever *cannot* be pulled without breaking
the other joint constraint — the trade round 10 flagged, now measured.
3. **A small-cloud pathology at cloud_mass 0.05** (S_k up to 2.6×, cmax up
to 3.7× at n25k), reproduced in both `cloud_tail` arms — the thinned cloud
population concentrates onto few owners rather than fading out. Recorded as
family behaviour, not draw noise.

Verification of the closest point, `op_cmass0` (full ladder, 3 draws):
**12/12 cells out of band high** — S_k ratio means 1.26–1.72, count_max
ratio means 1.24–2.04 — and Δslope(S_k) = +0.048/+0.132/+0.052 per decade at
k = 10/30/100 (limit 0.05): fails level everywhere and stability at k30.

## 3. Wave 2 — the hierarchy owns part of the tail but rotates the profile instead of lowering it

Non-cloud hub-mass knobs, same protocol:

| candidate | n25k S_k | n25k cmax | n200k S_k | n200k cmax | G1 25k/200k | G3 | G5 max |
|---|---|---|---|---|---|---|---|
| branch_tail 0.6 | 0.29–1.35 | 0.46–0.88 | 1.27–1.63 | 1.08–1.70 | 1.97 / 2.51 | 0.88 | 1.26 |
| branch_tail 0.2 | 0.34–1.30 | 0.60–0.85 | 1.26–1.62 | 1.05–1.70 | 1.97 / 2.50 | 0.91 | 1.28 |
| equalize 1.0 | 1.21–1.48 | 1.21–1.97 | 1.56–1.69 | 1.60–2.54 | 1.96 / 2.49 | 0.85 | 1.19 |
| equalize 2.0 | 1.22–1.49 | 1.21–1.98 | 1.58–1.69 | 1.60–2.57 | 1.96 / 2.49 | 0.85 | 1.19 |
| size_tail 0 | 1.04–1.44 | 1.31–1.98 | 1.56–1.71 | 1.35–2.56 | 1.95 / 2.38 | 0.85 | 1.19 |
| bt 0.6 + eq 1.0 | 0.29–1.35 | 0.45–0.88 | 1.27–1.63 | 1.08–1.70 | 1.97 / 2.51 | 0.88 | 1.26 |
| cm 0.1 + bt 0.6 + eq 1.0 | 0.33–1.35 | 0.49–1.06 | 1.26–1.65 | 0.94–1.70 | 2.08 / 3.25 | 0.88 | 1.25 |
| bt 0.2 + eq 2.0 + st 0 | 0.30–1.31 | 0.55–1.06 | 1.28–1.66 | 1.03–1.70 | 1.94 / 2.40 | 0.90 | 1.27 |

- **`equalize` and `size_tail` are inert** on the ladder count family
(cell-for-cell identical to the control) — local-density equalization and
leaf-size Zipf are not where battery-A hub mass lives at these settings.
- **`branch_tail` (the Zipf codebook hierarchy) is the one knob that moves
the tail — and it rotates the (n, k) profile through the band instead of
translating it down.** At n25k/k100 it *undershoots* to 0.29–0.34× while
n200k/k10–30 still overshoots at 1.26–1.75×.

Verification of `op_branch_tail0.2` (full ladder, 3 draws): 5/12 cells touch
band, but the ladder is the wrong shape — S_k ratio runs 0.32 → 1.31 along
k100's ladder and 1.31 → 1.59 along k10's; Δslope(S_k) = **+0.075 / +0.312 /
+0.641 per decade** at k = 10/30/100 against the 0.05 limit. The move also
degrades the spots: G5 1.17× → 1.25–1.28× (all 12 cells further out of band)
while G3 rises 0.85 → 0.91 (into band). Flattening the hierarchy is a
different geometry, not a lower-hub-mass version of the fitted one.

## 4. The second failure clause fires

Per PREREG_ROUND11 v2's own terms: *"If the operating-point move cannot
bring the un-planted baseline to band without breaking G3/G4/G5, that is a
joint-constraint infeasibility finding at the fit_v10 family level."* Both
halves are measured:

- No candidate — 17 points across all five hub-mass knobs, two verified on
the full 12-cell ladder at 3 draws — puts the un-planted baseline at or
below the G6-relevant band in 12/12 cells (best: `op_cmass0`, 0/12 in band;
`op_branch_tail0.2`, 5/12 in band with Δslope up to 13× the limit).
- The two knob families that move counts at all each break a joint
constraint: clouds ↔ G1 (2.5× → 3.7×), hierarchy ↔ G5 (1.17× → 1.28×) +
ladder stability. The two knobs that respect the constraints (equalize,
size_tail) do not move the statistic.

Full disclosure on the spot baseline: under this fresh 5-draw protocol the
**fit_v10 control itself** sits out of the G5 band high (1.16–1.19×) and at
the G3 band edge (0.846–0.854) in every ladder cell — consistent with
round 10 closing on fitted-but-never-admitted status. "Without breaking
G3/G4/G5" was therefore assessed both absolutely and relative to the
control; no candidate reaches the count band while staying even
control-neutral on the spots, so the verdict does not depend on which
reading the author prefers.

Bands were not adjusted. The dial was not forced. Stages 2–3 were not run on
an unmoved floor.

## 5. What the negative localizes (input to the round-12 redirect)

1. **The residual battery-A count tail at k = 10, n ≥ 100k (S_k ratio
1.46–1.74) survives every knob in the family.** It is not cloud mass, not
ownership concentration, not leaf-size Zipf, not local-density contrast, and
only partially branch-hierarchy — the flattened hierarchy still carries
1.26–1.6× at n200k. Whatever produces real's count tail *shape* (level ~1.6
S_k that is n-stable per k with cmax falling as n grows), the fit_v10
concentration architecture reproduces its level only by overshooting it and
cannot match its ladder slope. The round-12 target is this mechanism — the
fitted family's core patch/hierarchy geometry — not a new overlay.
2. **The G1/G6 joint constraint is now a measured trade-off curve, not a
conjecture**: cloud mass buys G1 (2.25 → 1.96 at n25k as mass goes 0 → 0.2)
at the price of count-tail mass, and there is no setting where both sit in
band. Round 10's target-2 "joint constraint" is the binding infeasibility.
3. **`local_centers` remains shelved, not retired.** The v1 finding stands:
the primitive is a real, near-deterministic count dial whose reachable range
lies entirely *above* the baseline. Nothing measured here contradicts the
mechanism; what is missing is a floor for it to stand on. The dial-level
failure clause (structural non-transfer) was not triggered because the dial
was not re-run.

## 6. Stage-2/3 disposition and the retention-floor proposal

The stage-2 and stage-3 drivers are committed ready-to-run against any
future viable operating point, implementing the v2 criteria verbatim:
subsample-aware calibration per ladder n (pool never gates), ≥ 2 draws per
(setting, n) and 5 for freeze-candidates, between-draw S_k-ratio spread ≤
band width (0.30) at every n, |Δslope| ≤ 0.05/decade at every k, and the
retention floor. **Proposed floor value (for the author to set at freeze):
expected ≥ 8 surviving planted rows per draw at n = 25k.** Under this pool's
arithmetic — expected survivors = m·p·(400000/420000)·(n/400000) =
0.0595·m·p at n = 25k — that floor requires m·p ≥ 135 and excludes the
entire m = 4 arm of the v1 grid (m·p ≤ 128 → at most 7.6 expected), which is
exactly the arm whose 0–1-survivor draws produced the v1 silent-dial
pathology. The stage-1 real reference (5 draws, this commit) is the
reference dataset those criteria would score against.

## 7. Freeze-readiness assessment (recommendation only — the freeze is the author's call)

**Not freeze-ready.** Recommending:

1. **Do not freeze PREREG_ROUND11 v2 as drafted.** Its generator change 1
(the operating-point move) is the precondition for everything else in the
draft, and it is unsatisfiable inside the fit_v10 family: P-A would be
registered against a floor known not to exist, and the admission run would
simply report this document's numbers back.
2. **Take the prereg's own redirect**: round 12 aims at the fitted family —
the concentration architecture that owns the k10 large-n count tail and the
G1/G6 trade — with `local_centers` held as a validated primitive awaiting a
viable floor. Whether that becomes an amended round-11 draft or a round-12
prereg is a naming decision that belongs to the author.
3. If any freeze proceeds regardless, the stage-2/3 criteria and the 5-draw
real reference committed here are the calibration instruments to use; no
band adjustment is licensed by anything in this document.
