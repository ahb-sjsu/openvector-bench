# RC-6: the topical family — sparse shared features

**Status: plan, 2026-08-13.** The first successor-family campaign,
designed from the accumulated negatives rather than from new levers on
the segment family: the RC-5 trade surface (`results/RC5_VERDICT.md`),
the g1exp frontier (`results/RC4_VERDICT.md`), and the R80 partition
catastrophe (`results/R80_ANN.md`).

## 1. The design statement

The segment family forms neighbours by cluster co-membership, so k-means
recovers its neighbour structure (nprobe@95 = 2 vs real's 47–50), its
G1-vs-n response is capped by article-scale structure, and its spectrum
and neighbour variance are coupled through one direction vocabulary.
Real passages are close across articles because they **share rare
features**. The successor keeps everything the segment family got right
(articles, segments, path+ball, per-level arrangement frames, rho — the
held-out 8/10 machinery) and adds one element:

**Per-segment topic draws from a Zipf ladder.** Each segment takes `K_t`
slots; a slot picks a sharing level `L` with probability `2^-(L+1)` (a
leading-zeros bit trick — integer-exact), a topic id uniform in that
level's universe `M0 * 2^(b*L)`, a full-dimensional unit direction from
the topic bank, and a keyed per-segment coefficient scaled by an
IDF-like level weight. Sharing per topic falls from ~thousands (L = 0,
broad themes) to ~5 (the bond regime); the same mechanism therefore
supplies, at different levels: topical bulk variance, cross-article
neighbour bonds that no partition co-locates, and a hierarchy of
structures resolved only above specific sampling densities.

## 2. Registered predictions and kills

* **P1 (partition scatter).** nprobe@95 rises from 2 toward real's
  47–50 as topic weight and bond-level mass rise, at fixed geometric
  gates. **Kill:** if nprobe@95 cannot exceed 10 anywhere the mandatory
  trio holds, sparse bonds are refuted as the scatter mechanism.
* **P2 (density response).** g1exp steepens toward −0.17 *without the
  trend collapsing* — the bond ladder must break the trend↔g1exp trade
  curve that every RC-4 lever slid along. **Kill:** if (trend, g1exp)
  points still lie on the segment family's curve, the ladder is a
  reparametrisation and dies.
* **P3 (spectral decoupling — Phase B).** Confining common levels
  (L ≤ 2) to a profiled bulk subspace moves dims90 down while rare
  full-dim levels hold retention ≤ 0.743 — off the RC-5 trade surface.
  **Kill:** the triple still co-moves ⇒ the family boundary claim
  extends to sparse-feature architectures and RC-6 stops.
* Regression guard: g1/g5/g6, trend, rspan/gspan must stay in the
  `results/rc4_bands14.json` bands at any point advanced to Phase C.

## 3. Targets

Geometric: the 14-block bands. ANN (new, from `R80`, 3 blocks):
nprobe@95 ∈ [44, 54], recall@10 at nprobe 1 ∈ [0.527, 0.541], occupancy
CV ~0.39. The sweep panel adds the R80 IVF protocol (K = 1024, seed 7,
590k/10k) to every arm.

## 4. Phases

* **A** — harness screening: `w_topic` × `K_t` × ladder shape (`b`,
  IDF slope), topics full-dim, P1/P2 instrumented. 16 arms.
* **B** — spectral split (P3): common levels into a profiled bulk frame;
  composition with the D12 base params. ≤2 sweeps.
* **C** — package port (topics integer-exact via leading-zeros level
  draw; defaults inert → RC-3 identity `e8423665…` untouched), fidelity,
  4-seed pre-freeze.
* **D** — freeze + one-shot on fresh blocks (geometric panel AND the ANN
  panel, both registered), expected outcome declared first. Only if the
  robust scorecard beats RC-3's 8/10 *and* the ANN panel is in band —
  the bar is higher now, on purpose.

Envelope ≤4 harness sweeps (larger than usual: it is a new family).
Budget so far: 0 arms.
