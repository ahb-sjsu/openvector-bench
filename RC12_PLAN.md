# RC-12: closing the knife edges

**Status: plan, 2026-08-14.** One composition sweep. The RC-11 echo cell
(`p_echo 0.12, k 3, alpha 0.96, echo_win 100k`, F8-minus-dups base) is
**held fixed**; only the two mapped levers for the two remaining dose
costs move:

* **g5** (−0.003…−0.010) and **g8** (−0.002…−0.013): `pool_alpha` raises
  both (`R70`); `fil_scale` reduction lifts both (less fine variance →
  tighter r10 → higher contrast; fewer neighbours carried outside the
  top-256 → higher retention). Small doses of each, alone and combined.

**Prediction:** a cell holds all ten minus g4, seed-robustly — the
project's first 9/10-robust profile with real density response.
**Kill:** the levers disturb the co-held seven (rspan and trend are the
watch items — pool_alpha lowers rspan, fil_scale moves g1).

One sweep (16 arms incl. three seed checks); if a cell holds, RC-12
proceeds directly to package port → 4-seed → the ≥8-block one-shot
declared in a separate freeze document. Budget so far: 0.
