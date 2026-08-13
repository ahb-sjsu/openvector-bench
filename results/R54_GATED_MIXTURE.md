# Gating widens the article as designed, and s(14) still falls

**Exploratory, not a registered round. PARTIAL — 2 of 4 arms; see the run note.**
No admission claim, seal untouched. Measured 2026-08-12. Driver
`harness/rc1/gated_probe.py`; record `results/gated.json`. Follows `R53`.

## The design, and why it is narrow

`R53` measured that the within-article distance distribution is a **mixture**,
not a continuous radial field: `p90` is pinned at the global scale at every index
gap while `p10` moves 47%. A lognormal radius would shift both tails together.

So the mechanism tested is a **Bernoulli gate** on each level of the
within-article path: two rows share a level's component only if they are in the
same block *and* the gate fires. Pairs at one gap then share a varying number of
levels — sometimes many (very close), sometimes none (global) — producing
heteroscedasticity at fixed gap with a saturating upper tail.

Everything else is held at `R49`'s branch-8, three-level baseline. One mechanism,
one knob. The build is written entirely on `hashrng`, so every draw is keyed and
the emitter is random-access; this also advances task 2.

## Anatomical readout, not just s(k)

Per `R52`/`R53`, each arm reports the anatomy directly so an improvement cannot
pass for the wrong reason.

| gate | g5 | eff_rank | g1 | g6 | ratio | rms | s(4) | s(14) | s(53) | **D_article** | d50 same | d50 cross | overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **real** | **1.369** | **182.3** | **17.23** | **1.696** | **4.050** | — | **8.8** | **16.1** | **28.9** | **1.72** | **0.884** | **1.099** | **0.114** |
| 1.0 (control) | 1.662 | 198.9 | 4.33 | 1.563 | 6.347 | 10.43 | 8.4 | 10.7 | 23.3 | 1.22 | 0.895 | 1.289 | 0.000 |
| 0.7 | 1.917 | 157.2 | 5.10 | 7.442 | 6.275 | **9.10** | 7.3 | 6.8 | 18.6 | **1.39** | 0.793 | 1.272 | 0.000 |

## What the anatomy shows

**The control confirms the diagnosis directly.** With no gating, `D_article` is
1.22 against real's 1.72 and the same/cross overlap is **exactly 0.000** against
real's 0.114 — the shell, measured rather than inferred. The within-article
*median* is already right (0.895 against 0.884), so the defect is purely spread,
which is what `R52` concluded from the k-resolved neighbourhood.

**The gate moves the intended quantity.** `D_article` rises 1.22 → 1.39, and the
s(k) rms improves 10.43 → 9.10, the best in this family.

**But `s(14)` falls rather than rises** — 10.7 → 6.8, against a target of 16.1.
The mechanism widens the within-article spread and the dip deepens anyway.

**And g6 explodes**, 1.563 → 7.442. This is `R44`'s mechanism returning: gating
leaves some rows with few active levels, so they sit close to the article centre
with little displacement and become hubs — density inhomogeneity, created this
time by the gate itself.

## Reading, held carefully

The pre-registered falsification condition was: if `D_article` reaches ~1.7 and
`s(14)` still does not move, the `R52`/`R53` interpretation is wrong.

**That condition is not met.** `D_article` reached 1.39, not 1.7, so this is not
the clean falsification — it is one arm of a partial sweep in which the target
quantity moved 35% of the way and the outcome moved the wrong way. Two readings
remain open:

* the spread is still too narrow, and `s(14)` turns once `D_article` passes some
  threshold nearer 1.7; or
* pairwise breadth is insufficient, and what matters is the **conditional**
  breadth versus gap, which the gate does not reproduce — it widens the spread
  without preserving `R53`'s `p90`-pinned shape.

The second looks more likely on the evidence: **`overlap` stayed at 0.000 in both
arms**, and overlap is the part of `R53`'s anatomy that most directly encodes
"some pairs at small gap are already at global distance". The gate widens the
close mode without ever placing a small-gap pair at the global scale.

## Run note — partial, and a thermal event

Four arms planned, **two completed**. Atlas CPU Package 0 reached **99 °C**, one
degree below critical. The probe was shed by script name immediately and
temperatures fell to 81 °C.

The cause was not this job alone: concurrent load from another user's workload
had ramped to load average ~11 (containerd 256%, postgres 125%, a python at
113%, kubectl 107%) while the probe ran. This job was the increment that took an
already-loaded machine to the limit. Nothing else was touched.

Remaining sweeps should move to NRP GPU rather than Atlas: 0 of 4 heavy GPU
slots are in use, and the 1T fleet is swarm-class (1 CPU / 2 Gi / no GPU), so a
GPU burst does not compete with it. The sweep needs only the generator and the
target constants, not the Wikipedia corpus, so it has no dependency on Atlas
storage.

## What is established

* Measured directly: the construction's `D_article` is 1.22 against real's 1.72,
  with **zero** same/cross overlap against real's 0.114.
* Level gating raises `D_article` to 1.39 and gives the best s(k) rms in this
  family (9.10).
* It does not raise `s(14)`, and it reintroduces hubness (g6 7.44).
* `overlap` is unmoved by the mechanism and is the likelier missing quantity.

## What is not

* The falsification test. `D_article` did not reach 1.7; gates 0.5 and 0.3 are
  unmeasured.
* Whether a mechanism that raises `D_article` **and** `overlap` together behaves
  differently. Nothing tried has moved `overlap` off 0.000.
