# RC-4 Phase A: both registered kills fire — and each refutation names the redirect

**Exploratory, not a registered round.** Measured 2026-08-13 on NRP A10s
(16 arms, one indexed job). Driver `harness/rc1/rc4a.py`; raw
`results/r75.txt`. Executes `RC4_PLAN.md` Phase A against the 14-block
bands; base is the frozen RC-3 D12 point.

## Kill 1 fires: the two-scale pool form is refuted

The `max((1+j)^-alpha, floor)` profile was supposed to concentrate the
head (g4 down) over a live plateau (g3/g8 safe). Measured, the floor does
protect g5/g6/g3 — floor 0.20–0.30 arms hold g6 at 1.78–1.80 where floor
0.10 arms crash to 2.6–3.1 — **but then g4 rises** (436–443 vs base 413):
the plateau adds tail dimensions faster than the head removes them. The
only cell reaching g4's band (α 0.35, floor 0.10: g4 357) has the same
broken g5/g6/g3 as the pure power law it barely differs from. The form
interpolates between two known-bad endpoints; the g4 ↔ g5/g6 conflict is
about *where* concentrated variance lives (head slots become hubs), not
about head-vs-tail balance.

## Kill 2 fires: chapters move g1exp the wrong way

Above-article chapter centres (A consecutive articles share a keyed
centre) make the G1-vs-n exponent **shallower**, monotonically in weight:
−0.113 → −0.104 (w 0.15) → −0.089 (w 0.25) → −0.064 (w 0.35), with gspan
compressing in lockstep (−0.35 → −0.23). The mechanism is diagnosed by its
own failure: chapter blocks (~370 rows) are coarse enough that even a 25k
sample resolves them, so they add n-independent low-dimensional variance —
compressing the density response instead of steepening it. **g1exp needs
structure that only large samples resolve — finer than the article scale
or in the article-size tail, not above it.**

## The redirects (Phase B, running)

1. **g4/g8**: return to the `R73` D5 point (lp 9.5, g4 361 IN on the
   package, g8 +0.02 too high) and apply the floor there — its one
   reliable measured effect is raising the tail, which is exactly a g8
   reducer. Grid: α × floor × lp around D5.
2. **g1exp**: the article-length tail. Giant articles are precisely the
   structure whose same-article neighbour count keeps growing with n.
   Grid: `size_spread` 1.4/1.6/1.8 (frozen law is 1.2), with brk and D5
   cross-terms.

## Budget

16 arms; RC-4 total 16.
