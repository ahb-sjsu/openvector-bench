# Filament family — calibration, and why one characteristic scale cannot work

**Exploratory, not a registered round.** Train/validation only, seal untouched,
no admission claim. Measured 2026-08-08 on Atlas (CPU, 20 threads). Family
`openvector_bench/filament_gen.py`; drivers `scale_probe{5,6}.py` and
`calib_filament.py`; records `/home/claude/ovb_scale/{scale_probe5,calib_filament}.json`.

## Why the family, and why calibration first

`R21B_SCALE_DEPENDENCE.md` measured real's profile as **rising** — s(r) from
15.7 at r = 0.888 to 37.3 at r = 1.063, with beta strengthening from +1.80 to
+4.80 across the ladder. The filament family is the mirror image of the Whitney
failure: low-dimensional threads (`fil_dim`) scattered across a
high-dimensional arrangement (`arrange_dim`), so a neighbourhood runs along a
thread at small radius and reaches neighbouring threads at large radius.

**Process note.** The first filament run guessed its constants and cost 45
minutes to discover four were wrong, which is the fourth time this session that
pattern repeated (bitmap noise floor, bitmap `m0`, the mis-specified null, the
fixed-F artifact). This calibration — one factor at a time, ~25 cells, ten
minutes — is the step that should have come first, and it is what actually
resolved the family. The campaign's own history (R17b power, R17c decision
rule, R20 estimator domain) is the same lesson.

## The transfer function

n = 25,000, 10k queries, registered k grid, so each cell compares directly to
real's 25k row (G1 25.97, s 27.4 → 35.2, beta +1.80, r 0.946..1.124).
Sensitivities are `dlog(statistic)/dlog(knob)` across each swept range.

| knob | → s_lo | → s_hi | → G1 |
|---|---|---|---|
| `arrange_dim` | −0.00 | **+0.62** | +0.01 |
| `log2_filaments` | −1.39 | +0.72 | −0.68 |
| `fil_scale` | −0.62 | +0.42 | −0.57 |
| `fil_dim` | −0.22 | +0.11 | −0.11 |
| `scale_spread` | −0.48 | −0.08 | +0.13 |

**One knob behaves as designed.** `arrange_dim` sets `s_hi` cleanly and
independently of everything else (s_lo sensitivity −0.00, G1 +0.01): 16 → 128
drives s_hi 15.9 → 55.3, so `arrange_dim ~ 56` would place s_hi at real's 37.
This is solvable rather than guessable, which is the point of the table.

**`s_lo` is not reachable.** Real needs 27.4; the base point gives 8.0, and
every route up breaks something else:

- `fil_scale` = 0.05 → s_lo 30.1, but beta flips to **−0.25** (falling);
- `log2_filaments` = 10 → s_lo 15.6, but s_hi collapses to 18.7;
- `fil_dim` = 2 → s_lo 19.3, but beta drops to +0.22.

`log2_filaments` is also not the neutral resolution parameter it was assumed to
be — it moves three statistics at once (−1.39 / +0.72 / −0.68).

## The n-interaction, which is the fatal one

`scale_probe5` found every arm's beta trend NEGATIVE (−0.74 to −1.55) against
real's +1.41. The diagnosis was fixed-F: with the thread count fixed, k = 500
reaches ~330 threads at n = 25k but only ~40 at n = 200k, so the arrangement is
progressively less resolved. Raising F tests it directly:

| arm | n=10k | 25k | 60k | 140k | trend/ln n |
|---|---|---|---|---|---|
| F14 | +2.53 | +1.56 | +1.16 | +0.53 | −0.73 |
| F17 | +2.53 | +1.42 | +1.61 | +1.35 | −0.38 |
| real | — | +1.80 | — | — | **+1.41** |

The diagnosis was right and the fix is insufficient: 8x more threads halves the
decay but does not reverse it. F14 and F17 are **identical** at n = 10k
(G1 24.90, s 4.2 → 25.4, beta +2.53), because once `n/F < 1` the thread count
stops mattering. Behaviour is governed by points-per-thread, not by F.

## Why no parameter can fix it

The family carries **exactly one thread scale**. As n grows the thread gets
resolved, so `s_lo` **rises** — 4.2 → 14.6 across the n-sweep. Real's `s_lo`
**falls**, 27.4 → 15.7. Opposite by construction.

A single characteristic scale saturates once it is resolved; past that point
more data adds no finer structure and the measured dimension can only go up.
For `s_lo` to keep falling, the corpus must have structure continuing down at
every scale, with dimension **decreasing** toward finer scales.

That is neither one scale (this family) nor scale-free (cascades, which hold
beta roughly constant). It is a hierarchy with a per-level dimension decay —
which is exactly what `bitmap_gen`'s `dim_decay` knob was built to express and
has never actually delivered: masked first by an amplitude schedule that
annihilated deep levels, then by finite-depth truncation dominating the signal.

## Status of the family

Excluded, on mechanism rather than tuning. `arrange_dim → s_hi` is a genuinely
useful, isolated control that would transfer to any construction needing a
tunable large-radius dimension. Nothing else here should be reused as-is.

The family was never converted to bit-exact random access (it uses
`default_rng`, like every family in `generator_search.py`); that conversion was
deliberately deferred until the profile justified it, and it does not.
