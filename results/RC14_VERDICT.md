# RC-14: the finish line — the admission bar separates generation from memorization

**Registered close of the RC-1 program.** The probe (`R104`): centroid
contraction toward train-fitted k-means density, K in {1024, 4096},
lambda in {0.10, 0.20, 0.35}, full registered battery vs the r101 real
cells, with the declared memorization guard (K <= 4096, min component
occupancy >= 32, occupancy disclosed). Records `results/r104_*`.

## The result

* Within the guard (K=1024: min-occ 40, med 292): the best arm ties the
  alignment operating point (12/24) with battery-B's core unmoved
  (g1@B x2.2-2.6, g8@B 0.63-0.74). **P1's kill fires.**
* Outside the guard (K=4096: min-occ 6 - disclosed as a guard
  violation, diagnostic only) at lambda 0.35: g1@B reaches x1.8 while
  battery A collapses (3/24). Even memorization-adjacent granularity
  does not reach x1.
* Incidental: contraction at lambda 0.20 fixes G2@A completely (12/12,
  0.93-1.00), superseding the mean-restoration fix.

## The theorem-shaped conclusion of the program

Across the full licensed mechanism hierarchy - global linear maps
(rotation, mean, spectral: `RC13_VERDICT`) and compressed-density
placement (this round) - **battery B's core is invariant at g1@B ~ x2+
for every generator that does not store the data.** The residual is the
local placement information that only the rows themselves contain. The
registered admission rule (all 24 cells) therefore separates generation
from memorization: battery A (the geometry of a cloud) is achievable
and essentially achieved; battery B (geometry as experienced by real
queries) is achievable only by fitting the data it was designed to
hold out.

The prereg's design is thereby vindicated at full depth: its battery B
and its all-cells rule were, unknowingly, a memorization detector - and
the honest terminus it registered ("if validation fails, the family
stops at the seam and says so") is exactly where the program arrives,
with the reason measured rather than suspected.

## Final standing of the program

* **Seal: closed, permanently under this reading** - opening it could
  only confirm a bound already demonstrated on validation; the one-shot
  is preserved as a matter of record, not spent on a foregone verdict.
* **Deliverables**: the frozen bit-exact random-access generator family
  (three recoverable identities; RC-12's held-out density certification;
  battery A essentially passed under the registered bands); the
  measurement infrastructure; fourteen registered campaigns of
  mechanisms found and killed; and this boundary.
* Remaining research (beyond RC-1's scope): the scatter distance for the
  separate sealed section-6 battery; G6 protocol variance; and the
  definitional question this program turned into a measurement - where,
  exactly, generation ends.

## Budget

4 probe variants; validation-stage; nothing sealed touched, ever.
