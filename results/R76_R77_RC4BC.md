# RC-4 Phases B/C: the redirects fail informatively; the envelope closes

**Exploratory, not registered rounds.** 32 arms on NRP A10s, 2026-08-13.
Drivers `harness/rc1/rc4b.py`, `rc4c.py`; raw `results/r76.txt`, `r77.txt`.

`R76` (D5+floor, size_spread): the floor is a no-op below the power law's
natural minimum (miscalibrated grid, B1=B2=B3 bit-identical - recorded);
at effective doses it moves g8 by only -0.005 while g4 rises; the lp
route's g4 and g8 windows are disjoint (lp <= 9.55 vs lp >= 9.9). The
article tail moves g1exp into band at ss 1.4 (-0.136) at the cost of
trend 0.175 and g6 1.845.

`R77` (partitioned pool, ss re-centering): partition + global profile
crushes the fine components (g3 33-81, g5 1.6-5.0, g1exp sign-flip) -
refuted as implemented; profile-on-centre-draws-only identified but out
of envelope. Re-centering the ss mechanism returns g1exp to -0.10 at
in-band trend - the lever slides along the existing frontier.

Adjudication in `results/RC4_VERDICT.md`.
