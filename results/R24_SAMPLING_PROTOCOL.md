# The target is dense-sampling-dependent, not head-specific — the anchors stand

**Exploratory, not a registered round.** Measurements of the TARGET only; no
generator, no admission claim, seal untouched. Measured 2026-08-09 on Atlas.
Drivers [`uniform_draw.py`](../harness/rc1/uniform_draw.py) and
[`block_draw.py`](../harness/rc1/block_draw.py); records
[`uniform_draw.json`](uniform_draw.json), [`block_draw.json`](block_draw.json).

## The question this had to settle

`R23_F2_TRANSFER.md` reported that the geometry profile is protocol-dependent,
and `geometry.py:load_target` reads `part_*.npy` in order until `cap` rows — so
the registered pool is the contiguous **head** of a corpus that arrives in
Wikipedia's own topical order. If the falling G1 ladder were an artifact of
sampling the head, then R19 and R20 spent three rounds chasing an artifact and
six family exclusions were measured against a target that is not the corpus's
geometry.

## Experiment 1 — uniform draw (confounded, reported anyway)

600k rows drawn uniformly across all 41 parts (41M rows), registered protocol
otherwise unchanged.

| statistic | registered head pool | uniform 1.5% draw |
|---|---|---|
| G1 @ 25k → 200k | 25.97 → 18.28 | 50.5 → 44.6 |
| G1 exponent | −0.168 | **−0.053** |
| s_ratio trend | +0.511 | **−0.003** |

**This test was confounded and cannot answer the question.** It changed two
variables at once: *position* (head vs everywhere) and *density* (600k
consecutive paragraphs vs 600k rows scattered through 41M at 1.5% sampling).
Recorded as a design flaw in the test, not as a result about the target.

## Experiment 2 — density held fixed, position varied

Contiguous 600k-row blocks at four offsets, same density as the registered
pool, registered protocol unchanged. The head block is re-run as an internal
control on the harness itself.

| block | G1 exponent | s_ratio trend |
|---|---|---|
| head (offset 0) | **−0.168** | **+0.511** |
| offset 1,067,268 | −0.178 | +0.503 |
| offset 7,228,966 | −0.132 | +0.304 |
| offset 34,414,820 | −0.200 | +0.487 |

**Every position reproduces both the ladder and the ramp.** The head control
returned −0.168 / +0.511, identical to `scale_probe3`, so the harness is sound.
At offset 34.4M — a completely different region of the corpus — the ladder is
G1 27.34 / 23.04 / 20.34 / 17.94 against registered anchors 26.64 / 22.78 /
19.92 / 18.42, agreeing to a few percent.

## Conclusions

1. **The target is not a head-sampling artifact. The registered anchors stand.**
   R19/R20's premise was sound and the six family exclusions in
   `R21*`/`R23` were measured against a real property of the corpus.
2. **The entire uniform-draw difference is density**, not position.
3. **Block-to-block sampling variance is non-trivial and was previously
   unquantified.** Across four blocks the ramp trend spans +0.304 to +0.511 (a
   1.7x range) and the G1 exponent spans −0.132 to −0.200. Any pass/fail band
   built on a single-block anchor inherits that spread; admission criteria
   should quote it.

## The secondary result: C3, measured in real data

`CAPACITY_CONJECTURE.md` **C3** conjectures that sampling and generation do not
commute — `S(R(n,k,D)) ⊊ R(n',k,D)` with tail coordinates contracting,
"ladders thin" — anchored on the round-9 sampling-operator lesson. Experiment 1
is that effect measured directly on real embeddings: at 1.5% density the ramp
disappears (trend +0.511 → −0.003) and G1 doubles (≈20 → ≈49), because thin
sampling removes the near-duplicate and same-article neighbours that constitute
the local structure.

The operational consequence is sharper than the conjecture: **subsampling a
large corpus does not produce a smaller corpus of the same geometry.** An RC-1
grid built by subsampling probes something systematically different from what a
full-scale index has, and the difference is not small — it is the entire ramp
plus a factor of two in intrinsic dimension. Density, not row count, is the
variable that has to be controlled when comparing corpora across scales.

This also corrects a claim made earlier in this campaign's working notes: that a
uniform draw from the full corpus would be "the defensible choice" of pool. It
is defensible for *representativeness* and wrong for *density*, and a deployed
41M or 10¹² index is dense. The registered protocol was right to take a
contiguous block; its only arbitrary choice was starting at row 0, and
Experiment 2 shows that choice is harmless.

## Next

* Quote the block-to-block spread alongside the anchors wherever bands are set.
* When comparing any two corpora, hold **density** fixed, not row count.
