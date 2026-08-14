# RC-10: echo groups — near-parallel structure across a spectrum of scales

**Status: plan, 2026-08-14.** The density-response lead from
`results/RC9_VERDICT.md`, made concrete. Established by elimination:
additive shared components flatten the response at every scale; only
near-parallel resolution structure steepens it; single-dose row pairs
fail held-out (RC-8: insufficient depth, real gspan cost).

## 1. The mechanism

**Echo groups**: a keyed fraction of rows belongs to scattered
near-parallel micro-clusters. A member row is `alpha * prototype +
beta * own` (prototype = a keyed unit vector per group; no recursion,
no additive variance — the blend *replaces* energy). Group sizes follow
a ladder from pairs to ~64 members; `alpha` grades by level (tight
small groups, looser large ones). This is RC-6's topic ladder as
blends: the resolution physics that made topics fail (additive,
moderate-dim) inverted into the form RC-8 proved works (near-parallel,
~zero-dim when resolved).

Why the response deepens: a k-member group resolves *continuously* —
second member in-sample at fraction ~1/k, third at ~2/k — so a size
spectrum yields falling G1 across the whole density range (g1exp), and
prefix pools resolve group mass in proportion to their span (gspan),
with no single dose to pinch.

## 2. Registered predictions and kills

* **P1:** g1exp reaches −0.16 with the trio intact (the RC-8 bar the
  row-dup dose could not). **Kill:** saturation above −0.15.
* **P2:** gspan passes −0.335 (the eight-block shallow edge) somewhere
  P1 holds. **Kill:** the g1/g1exp/gspan pinch reappears in the
  spectrum form.
* **P3 (watch):** echo members from different articles share prototypes
  across cells — same-cell fraction and np95 reported.
* Regression guard: the 14-block bands, RC-8's eight-block bands as the
  honesty check.

## 3. Phases

* **A** — harness screening on the F8-minus-dups base (sheet on, p_dup
  0): echo rate × alpha grade × ladder shape. 16 arms, both panels.
* **B** — composition/re-centring. ≤2 sweeps.
* **C** — package port (pure keyed blends — random-access trivial),
  fidelity, 4-seed.
* **D** — freeze + one-shot under the ≥8-block rule (ten slots = one
  draw), only if the robust scorecard beats RC-8's 7/10 by moving a
  structural residual in.

Envelope ≤4 sweeps. Budget so far: 0.
