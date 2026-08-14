# RC-7 Phases A/B: the continuum's anatomy, the hybrid's 9/10, and the R85 lever map

**Exploratory, not registered rounds.** R86/R87: 32 arms on NRP; R85
extensions (p 0.038 dose, dup_window 50k): 8 package runs on Atlas.
Raw: `results/r86.txt`, `r87.txt`, `r85_b1t.json`, `r85_b1w.json`.

## R86 - the pure continuum trades anatomy for geometry

Replacing the cluster arrangement with a band-limited random field over
article latents: at (lat 2, bw 0.5) the ANATOMY goes real-like for the
first time - same-article fraction 0.61 (real ~0.66), rp1 0.601 (real
0.53), np95 9, all with honest occupancy - but the crowded 2-d sheet
makes hubs (g6 2.6) and crushes g8/g3. At high lat/bw the field
decorrelates: geometry nearly all-in (g3 202 vs hi 200.4) but sa 0.95
and scatter gone. The continuum is also a strong g1exp mechanism
(-0.23..-0.31 at low lat/bw). Pure replacement cannot hold both ends.

## R87 - the hybrid: cluster backbone + thin continuum sheet

**F8 (w_cont 0.25, lat 2, bw 0.5, p_dup 0.05): 9/10 harness flags** -
the best geometric configuration ever measured on any family. The sheet
supplies the coarse effective rank the family always lacked (g3 121 ->
154..186 across sheet weight, a proper dial) while dups carry g1exp
(-0.150) and gspan stays in (-0.282). F7 (w_cont 0.40): also 9/10, g3
171. Only g4 remains out. Scatter unchanged (np95 2-4): the thin sheet
does not crowd; that tension is RC-7's remaining front.

## R85 extensions - the dup lever map is complete

Three statistics, two knobs (p_dup, dup_window), measured slopes:

* p 0.038, W 600k: g1exp 4/4 in (thin margins), gspan 1/4 - the dose
  pinch is real; no robust joint by dose alone.
* p 0.05, W 50k: gspan REPAIRED (-0.41..-0.43, deep in - the prefix-pool
  resolution argument confirmed) and g1exp -0.146..-0.158, but **g1
  crashes to 13.4**: a small window resolves every dup in the g1 gate
  too, doubling the effective dose there. g1/g1exp/gspan are three
  constraints on two knobs with aligned resolution profiles.
* The way out is measured, not conjectured: the hybrid sheet keeps gspan
  in band at full dose and W 600k (F8), where g1 = 15.6. The window
  stays documented as a knob; the hybrid composition is the path.

## Hand-off to Phase C

Port the continuum sheet into the package (frozen quarter-wave cosine
table - no libm in the byte path), verify F8 on the package (g3's edge
should lift as it did on the harness), 4-seed. The scatter front
(crowding vs geometry) remains open with a measured trade curve.

## Budget

RC-7: 32 harness arms + 8 package runs; RC-7 total 40. No real blocks
consumed; sealed set untouched.
