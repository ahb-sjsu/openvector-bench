# Round 9 — probe log: four falsifications converge on graded short-range structure

**2026-07-22, Atlas, all at n ∈ {25k, 100k} against the round-2 real battery-B cell
means. Screening probes (single seed), disclosed per campaign practice; no gating run
yet — the round-9 pre-registration follows once the design below is implemented.**

## Probes and verdicts

**Probe A (`dup_mass`/`dup_scale` fine near-dups + `query_tail_n`): both falsified.**
Fine dups (jitter ≪ patch scale) are invisible to the trimmed two-NN estimator — every
dup pair's μ lands in the trimmed decile; G1 drift unchanged. Cluster-Zipf n-coupling
(`query_tail_n`) moves the G6 slope marginally (0.73→0.79 at 100k): the exponent is
saturated above ~2.4. Positive control: `spectrum_decay` 0.54→0.63 brings G3 1.91→1.17.

**Probe B (coarse dups, row-anchored queries at ambient jitter, spectrum knee).**
Coarse dups: still no G1 pin (drift is a level problem, not a mechanism problem —
the round-2 G1 *slope* passed; `local_dim` re-centring is the fix). Row anchoring at
tight jitter: **G6 ratio 1.08→1.06 across 25k→100k — level and growth matched**, the
first mechanism to do it — but as ambient-space jitter it wrecks G1/G2/G7. Spectrum
knee: G4 2.27→1.46, G3 through 1.0 — works, couples into G2/G8 (joint fit).

**Probe C (anchoring at real-scale ambient jitter): falsified, instructively.** Wider
ambient jitter puts queries *off-manifold* — two-NN reads ambient dimension (G1
2–3×), top-k lists decorrelate (G6 collapses). The EC lesson, replayed in query space.

**Probe D (the assembled family: IN-PATCH anchoring + knee).** In-patch anchoring
restores the mechanism: **G6 0.97→0.99 across n (level + slope), G5 1.01, G7
0.94–0.97, G8 1.04** — and **G1 collapses to 0.06–0.08**: the anchored query's r1 is
its anchor at ~`q_jit`×patch-radius while r2 is the patch spacing (~1.0×) — a
structural μ-gap our uniform-sparse patches cannot close at any single `q_jit`.

## The convergent diagnosis

Real's queries have r1 median 0.97 with r2/r1 = 1.024: neighbours exist at *graded*
fractional distances. Our patches are uniform-sparse — nearest-neighbour distances
concentrate at one scale. Every remaining defect traces to this one absence:

- G1 n-flatness (the estimator pinned by a stable short-range μ distribution);
- G2's smooth ball growth through intermediate radii;
- anchored-query sanity (a ladder of neighbours between the anchor and the bulk);
- hub anatomy (real hubs are density-driven: corr(N₁₀, −d10) = +0.67).

This is the third independent arrival at the codebook probe's suspect: **fine-scale
graded near-duplicate/paraphrase structure**. The round-9 design is therefore
**paraphrase clouds**: Zipf-sized point clouds around popular rows with power-law
radius grading (spanning ~0.1–1× patch scale), which simultaneously provides (a) the
short-range μ ladder (G1/G2), (b) natural anchor targets for the query model (G6
level + growth, already proven), and (c) density-driven hub anatomy. Implementation +
pre-registration next; the family (`hier_dupq_corpus`, 21 knobs) already carries the
in-patch anchoring and two-piece spectrum verified here, with the falsified knobs
kept at inert defaults and so recorded.

**Protocol note landed with this commit:** battery-A queries are now sampled
uniformly (registered fix, `corpus_geometry.py`; rationale in
`RC1_ROUND2_CANDIDATE.md` finding 3) — real battery-A targets will be re-measured
under the fixed protocol in the next admission run.

Probe scripts: session scratch (`probe_v9*.py`, preserved on Atlas `ovb_gen/`);
numbers above are single-seed screening readings, not gating results.
