# RC-4: the two named mechanisms

**Status: plan, 2026-08-13.** Successor to `RC3_PLAN.md` after the RC-3
verdict (`results/RC3_VERDICT.md`): 8/10 held-out, mandatory trio IN, the
two misses pre-declared. RC-4 exists to test exactly the two mechanisms
RC-3 identified and did not try. If both land, the family plausibly passes
the full measured slate; if either is refuted, that is the registered
finding.

## 1. Targets

Judged during tuning against the **14-block bands**
(`results/rc4_bands14.json`; every modern-protocol block measured to
date), then a one-shot on fresh offsets. The frozen RC-3 baseline (D12)
against those bands: g4 417 vs [351.2, 363.1] and g1exp −0.109 vs
[−0.228, −0.122]; everything else in.

## 2. Mechanism 1 — two-scale pool profile (for g4)

`R73` showed g3/g4/g8 trade along one curve under the single power-law
`pool_alpha`: concentration that reaches dims90 357 destroys eff-rank and
retention first. The two-scale form adds a **floor**: slot amplitude
`w_j = max((1+j)^-alpha, floor)`, unit mean square — a concentrated head
(drives dims90 down) over a live plateau (keeps eff rank and the tail).
Parameters `pool_alpha` (head), `pool_floor` (plateau level).

**Kill:** if no (alpha, floor) cell reaches g4 ≤ 365 while holding g3 ≥
151 and g8 ≤ 0.743, the two-scale form is refuted and g4 is recorded as
family-level under all tried spectral forms.

## 3. Mechanism 2 — above-article structure (for g1exp)

The family's articles are index-local but its *arrangement* is index-free:
nothing above the article correlates with index position, while real
Wikipedia's ordering does (gap-128 cosine 0.236 vs 0.228 baseline, §4.1 of
the paper). The G1-vs-n exponent is precisely a statement about structure
that only larger samples resolve. Mechanism: **chapters** — blocks of `A`
consecutive articles share a chapter centre with weight `w_chap`, keyed on
the chapter id (pure function of index; random access preserved).
Parameters `chap_size` (articles per chapter), `w_chap`.

**Kill:** if g1exp does not reach −0.122 at any (A, w_chap) with the
trend/rspan/gspan trio still in band, above-article structure is refuted
as the g1exp driver in this family.

## 4. Phases and discipline

* **A** — harness sweep 1 (16 arms): each mechanism alone on the D12 base;
  signs and cliffs.
* **B** — harness sweep 2 (16 arms): composition + interaction with the
  D12 pocket (brk/alpha re-centring if the new mechanisms move the ramp).
* **C** — package port (both mechanisms parameterised, defaults inert so
  the RC-3 identity `e8423665…` is untouched), verification of 2–4
  winners, 4-seed pre-freeze.
* **D** — freeze + one-shot on fresh offsets (free after the `RC3` ledger:
  2M, 4M, 6M, 9M, 11M, 12M, 14M, 16M, 17M, 19M, 20M, 22M, 24M, 26M, 27M,
  29M, 30M, 31M, 33M, 36M, 38M, 40M), expected outcome declared first.

Envelope ≤3 harness sweeps; multi-seed before any band claim; kills are
verdicts, not detours. Budget so far: 0 arms.
