# Campaign plan — rounds 17 to 19: families whose attractiveness saturates

**Status: DRAFT ⚪ — not frozen.** Drafted 2026-08-07 after round 16 closed
([`R16_PY_GATE.md`](R16_PY_GATE.md), `682b7e4`). Naming and freezing are the
author's calls. Bands are those of RC-1 §5 as amended, untouched here.

This plan covers three candidate families and one diagnostic that may make
all three unnecessary. It is written as one document rather than three
preregs because the families share an instrument, a target and a failure
mode, and because testing three candidates against one target invites
cherry-picking unless the discipline for that is fixed in advance (§5).

---

## 1. What the measurements now constrain

Two results from rounds 13 to 16 rule out most of the space.

**Real's attractiveness law is not scale-invariant in shape.** Measured in
the only form that survives a change of budget protocol, real's
attractiveness skew rises at **+0.51 per decade** at k = 10, confirmed by
three measurements across two protocols and two ladder widths with a spread
of 0.07. Every construction whose attractiveness is *drawn from a fixed
distribution* rises at +2.5 to +3.8, because deeper sampling of a fixed
heavy tail necessarily reveals more of its extreme.

**The number of attractors is not the operative variable.** Round 16 gave a
codebook a Pitman-Yor popularity law so its atom count grew as n^α, verified
at measured exponents 0.329, 0.509 and 0.730, and the hub scaling did not
move. Changing how many attractors exist adds attractors in the same
proportions. It changes the count and leaves the shape alone.

**Therefore:** a family is worth testing only if attractiveness **saturates**
or **emerges from competition**, rather than being drawn. Zipf-over-atoms,
Dirichlet-over-atoms, Pitman-Yor and their variants are excluded by
measurement, not by taste.

---

## 2. Stage 0 — the diagnostic that may obviate rounds 17 to 19

Round 8's winning point is the campaign's best result and the basis of round
14, and **its attractiveness-skew slope has never been measured**. It is a
corpus/query construction rather than a popularity draw, so it is not
excluded by §1, and it may already have the property the three families
below are being built to obtain.

**Measure it first.** One gate run against a point already frozen in
[`r14_frozen_corpus.json`](r14_frozen_corpus.json), under the §3 protocol.

- **If its slope is within ±0.15 of +0.51**, the corpus/query split already
  scales correctly. Rounds 17 to 19 are not run. Round 14's query-model
  search proceeds directly and the campaign's best family gains a property
  nobody knew it had.
- **If its slope is near +2.9**, the problem is deeper than any family so
  far and rounds 17 to 19 proceed as written.
- **If it lands between**, report the value and decide with data rather than
  by this plan.

Cost is one run. Nothing below is built until this returns.

**Result, 2026-08-07** ([`R17_STAGE0_RESULT.md`](R17_STAGE0_RESULT.md)).
The slope is **+0.904 ± 0.111** over 20 seeds, which is the third case. It
sits 18 standard errors from the codebook reference and 3.6 from real, so the
family is categorically not in the codebook regime and is nevertheless
significantly wrong. The tail-shape diagnostic favours a **power law in all
sixty cells**, which is the same scale-invariant shape round 16 isolated.

**The plan is amended accordingly, under its own instruction to decide with
data.** Round 17 no longer builds a family from scratch. The round-8 family
already holds six gates with real anatomy and scales in the right regime, and
its only measured defect on this axis is that its cluster-choice law is Zipf,
which is scale-invariant by construction. Round 17 replaces **that one law**
with sublinear preferential attachment and freezes everything else, so the
geometry gates and the anatomy guard are inherited rather than re-earned and
P-14C's baseline already records what they must not move by.

Rounds 18 and 19 are **held**, not cancelled. They construct attractiveness
from scratch, which is worth doing only if modifying the best existing family
fails.

---

## 3. The shared instrument

One harness, parameterised by family. Not three gates. A per-family gate
invites per-family tuning of the measurement, and comparability across
families is the point.

**Protocol, identical for every family and for real.**

- Ladder n ∈ {12,500, 25,000, 50,000} at **constant ρ = 4.0**, dim 1024.
- Five seeds, not three. Round 16's per-seed spreads reached 3.9 and three
  seeds could not distinguish a family from noise.
- Readouts in invariant form only, per [`../spec/QUERY_BUDGET.md`](../spec/QUERY_BUDGET.md).
  `attractiveness_skew` carries every claim that crosses n. `tail_excess` is
  reported within cells.
- Target +0.51 ± 0.15 at k = 10. k = 30 is measured and reported and does
  not gate, its own spread being 0.22.

**Two checks per family, and they are separate.** Round 16 passed its
mechanism check and failed its outcome check, which is the reason this
separation is now mandatory rather than tidy.

- **Mechanism check.** Does the knob do what the family claims? Measured
  directly on the object the claim is about, never through a proxy. Round
  16's growth check counted atoms because effective rank saturates against
  the ambient dimension and cannot see growth.
- **Outcome check.** Does the family reach the target? A mechanism that
  works and an outcome that follows are different propositions and a family
  can have the first without the second.

**One new diagnostic, registered for all three.** Measure the attractiveness
distribution's **tail shape** directly rather than only its skew. Fit the
upper decile to a power law and to a stretched exponential and report the
likelihood ratio. This distinguishes "the tail is sub-power-law as the
mechanism intends" from "the skew happened to land somewhere", which the
skew alone cannot.

---

## 4. The families

Each is stated as a mechanism, a knob with a declared range, a mechanism
check and an outcome prediction. All three face §3's instrument.

### Round 17 — sublinear preferential attachment, applied to the round-8 family

**Amended after stage 0.** This was written as a fresh codebook family. It is
now a one-parameter modification of the frozen round-8 point, because that
family measured 18 SEM away from the codebook regime and only 3.6 from real.
Replacing its cluster-choice law is a smaller change with more inherited
evidence behind it than building a fourth codebook.

**Mechanism.** A cluster's probability of being chosen next is proportional to
`m**beta`, with `m` its current membership and `beta < 1`. At beta = 1 this is
classical preferential attachment and yields a power law that keeps
concentrating, which is the measured failure mode. Below 1 the stationary
tail is stretched-exponential rather than power-law, so concentration grows
strictly slower than any scale-invariant law permits.

The reading for the data is direct. Wikipedia topics saturate. There are
only so many articles about one subject, so a popular topic stops accruing
proportionally. `beta` is how strongly it stops.

- **Knob and declared range.** `pa_beta` ∈ [0.4, 1.0].
- **P-17M (mechanism).** The fitted tail is sub-power-law for `pa_beta` < 1,
  with the likelihood ratio favouring stretched exponential, and the effect
  strengthens monotonically as `pa_beta` falls.
- **P-17O (outcome).** Some `pa_beta` in the declared range brings the slope
  within ±0.15 of +0.51, measured on **≥ 20 seeds with SEM ≤ 0.15**. Seeds
  and SEM replace the earlier five-seed spread criterion, because stage 0
  needed twenty seeds to become conclusive at all and range is the wrong
  statistic for the question.
- **P-17G (nothing is paid for elsewhere).** At the fitted `pa_beta`, the
  five geometry gates and `bb_skew` stay within 0.05x of the P-14C freeze
  baseline in [`r14_freeze_baseline.json`](r14_freeze_baseline.json). This
  clause exists only because round 17 now modifies a frozen point rather than
  building a new one, and it is what makes the inherited evidence legitimate.
- **Cost note.** Sequential attachment is O(n) and does not vectorise
  naively. Implement with a Chinese-restaurant style weighted draw over a
  running count vector, blocked, or the family will be too slow to gate.

### Round 18 — competition geometry

**Mechanism.** Attractiveness is not drawn at all. A point's capture basin
is bounded by its neighbours, so adding points shrinks every basin including
the hubs'. Flattening is then a consequence of geometry rather than a
distributional assumption, which is structurally what real data does.
Concretely, a clustered process at large scale with a repulsive short-range
component, so topics cluster while distinct documents within a topic do not
collapse onto each other. A Matérn hard-core or determinantal component
gives the repulsion with tractable parameters.

- **Knob and declared range.** `repulsion_radius` ∈ [0, 0.6] in units of the
  within-cluster scale.
- **P-18M (mechanism).** The nearest-neighbour distance distribution's lower
  tail is suppressed relative to the non-repulsive control, monotonically in
  `repulsion_radius`.
- **P-18O (outcome).** As P-17O.
- **Registered risk.** Repulsion may push G1 up by flattening local
  neighbourhoods, which is the round-3 concentration mechanism in reverse.
  G1 is measured at the fitted point and reported whether or not it moves.

### Round 19 — aging

**Mechanism.** An atom's attractiveness decays with accumulated usage or
with age, so early atoms do not retain their advantage indefinitely. This is
the standard network-science correction for over-concentration and is a
time-indexed relative of round 17.

- **Knob and declared range.** `age_decay` ∈ [0, 2.0].
- **P-19M (mechanism).** The rank correlation between an atom's arrival
  order and its final usage falls monotonically in `age_decay`.
- **P-19O (outcome).** As P-17O.
- **Held as a variant.** If round 17 passes, round 19 is not run separately,
  since `beta` and `age_decay` address the same saturation through different
  parameterisations and running both invites the multiplicity problem of §5
  for no additional mechanism.

---

## 5. Multiple-comparison discipline

Three families against one target, each with a knob swept over roughly five
values, is fifteen opportunities to land within a tolerance by chance. Two
rules, both fixed here rather than after the fact.

1. **A family passing its outcome check is provisional until confirmed on a
   held-out ladder point and five fresh seeds.** The confirmation uses
   n = 100,000, which no fitting run touches. A family that passes at the
   fitted ladder and fails at the held-out point is reported as a fitting
   artefact, which is a result about the family and not a near miss.
2. **A family passing its outcome check while failing its mechanism check is
   reported as a coincidence, not a solution,** and does not proceed. If the
   knob does not do what the family claims, matching the target through it is
   not evidence the mechanism is right.

---

## 6. Ordering and kill criteria

1. **Stage 0** — round 8's slope. May end the plan.
2. **Round 17** — first pick, strongest mechanism, cheapest to reason about.
3. **Round 18** — only if 17 fails, since it is a different kind of object
   and worth spending on only when saturation-by-popularity is excluded.
4. **Round 19** — only if 17 fails on its mechanism check rather than its
   outcome, since that is the case where a different parameterisation of
   saturation is genuinely informative.

Each round's failure closes its family. No family is retried inside its own
round with a second parameterisation.

---

## 7. What closes the programme

If all three fail their outcome checks while passing their mechanism checks,
the finding is that saturation of attractiveness is not sufficient to
reproduce real's hub scaling, and it is the strongest available evidence for
the capacity conjecture. That is a reportable result and it terminates the
family search rather than motivating a fourth mechanism.

The honest prior, stated in advance: the campaign has closed eleven families
and this plan is unlikely to close the gap on its own. Its value is that
each outcome is informative, the cost per family is minutes, and a negative
across all three is a stronger statement than any single negative so far.

---

## 8. Compute

Every run fits the enforcement-exempt envelope (cpu ≤ 1, mem ≤ 2Gi) and
takes minutes on NRP. Anything larger fights a transient clamp for no
reason. See [`../spec/NRP_OPS.md`](../spec/NRP_OPS.md), and note that the
generator must accumulate admixtures per atom slot rather than gathering
`(block, s, dim)`, which is an eightfold difference and OOMed a 2Gi worker
in round 16.
