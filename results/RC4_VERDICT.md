# RC-4: both mechanisms refuted within the envelope — the frontier stands at RC-3's frozen point

**Registered close, no freeze, no one-shot spent.** Three harness sweeps
(48 arms, `R75`–`R77`, drivers `harness/rc1/rc4a-c.py`, raw
`results/r75-77.txt`), executed against `RC4_PLAN.md`'s pre-registered
kills. The plan said: "If either is refuted, that is the registered
finding." Both were.

## Mechanism 1 — spectral reshaping for the g4+g8 joint: refuted in four forms

The target: dims90 ≤ 363 and PCA retention ≤ 0.743 simultaneously
(real holds both; the RC-3 frozen family holds retention but not dims90).

1. **Power law** (`pool_alpha`, RC-3): g4 in band only where g5/g6 break
   (`R70`).
2. **Two-scale max(power, floor)**: the floor protects g5/g6/g3 but then
   g4 *rises* — the plateau adds tail dimensions faster than the head
   removes them (`R75`).
3. **Pool-size composition** (lp 9.5–9.7 × α × floor): g4 ≤ 363 needs
   lp ≲ 9.55; g8 ≤ 0.743 needs lp ≳ 9.9 — disjoint, and even the flat
   profile at lp 9.5 has g8 0.748 (`R76`).
4. **Partitioned pool** (fine components confined to tail slots so the
   head can concentrate hub-free): under a global amplitude profile the
   fine components are crushed and the geometry collapses — g3 33–81,
   g5 1.6–5.0, g1exp sign-flips (`R77`). A profile applied to
   centre-draws only was identified but lies outside the envelope.

The durable statement: **in this family, neighbour structure and global
spectrum are coupled through the shared pool, and every reshaping of that
pool moves dims90 and retention together** — while real holds dims90 357
with retention only 0.737, i.e. real's neighbour-relevant variance lives
partly outside its top-256 PCA dimensions. Decoupling them needs a
mechanism that gives fine components full amplitude in directions the
global spectrum suppresses — recorded for any successor, untried here.

## Mechanism 2 — g1exp: two refutations

1. **Chapters** (above-article shared centres): wrong sign — g1exp goes
   *shallower*, monotonically in weight (−0.113 → −0.064), because
   ~370-row chapters are resolved even by small samples and add
   n-independent variance (`R75`).
2. **Article-length tail** (`size_spread` 1.3–1.8): moves g1exp the right
   way locally (−0.136 at ss 1.4, in band) but the gain vanishes under
   re-centering — restoring the trend via brk returns g1exp to −0.10.
   The lever slides along the existing trend↔g1exp trade curve rather
   than shifting it (`R76`, `R77`). Refuted as a frontier mechanism.

## Verdict

No RC-4 configuration robustly beats the RC-3 frozen D12 (held-out 8/10,
`results/RC3_VERDICT.md`). Re-freezing D12 to spend a one-shot
re-confirming RC-3 would burn held-out blocks for nothing; the fresh
offsets stay clean. RC-4 closes as a registered negative with two
precisely-shaped open problems:

* a spectral mechanism that decouples neighbour-relevant variance from
  the global spectrum (for g4+g8);
* a density-response mechanism whose effect survives trend re-centering
  (for g1exp) — everything tried so far reparametrises one frontier.

## Budget

48 arms (Phase A 16, B 16, C 16); no real blocks consumed; the RC-3
identity `e8423665…` remains the frozen deliverable.
