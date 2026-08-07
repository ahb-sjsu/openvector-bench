# Round 17 intervention — the cause is densification, not the choice law

Measured 2026-08-07 on NRP. Driver
[`r17_decompose.py`](../harness/rc1/r17_decompose.py), raw record
[`r17_decompose.json`](r17_decompose.json). Ladder n ∈ {12,500, 25,000,
50,000} at constant ρ = 4.0, dim 1024, 20 seeds. Two arms differing in one
thing.

## Result

| arm | cluster count | slope |
|---|---|---|
| FIXED | `2**log2_clusters`, held | **+0.905 ± 0.111** |
| GROWING | scaled as n^0.5 | **+0.393 ± 0.102** |

Difference 0.512 against a standard error of 0.151, so **3.4 SEM**. The
FIXED arm reproduces stage 0's independently measured +0.904 to three
decimals, which is a useful check that the two drivers agree.

**Growing the cluster count moves the family to real's value.** The GROWING
arm sits 0.117 from real's +0.51, inside the ±0.15 tolerance and about 1.1
standard errors away. This is the first time in the campaign that a
registered intervention has moved a statistic onto real's value rather than
merely toward it.

## What it falsifies

The campaign plan's amendment, written two hours earlier, asserted that the
family's only defect on this axis was its Zipf cluster-choice law, and
proposed replacing that law with sublinear preferential attachment. **That
assertion is wrong.** The rise is a densification effect of a fixed cluster
count. Every added row joins one of a fixed number of clusters, so
within-cluster competition intensifies and the local winner takes relatively
more. Replacing the between-cluster choice law would have intervened on a
term that is not carrying the effect.

The assertion was never measured when it was written. It cost one run to
check and would have cost a build to act on.

## Why this does not contradict round 16

Round 16 grew a codebook's atom count and nothing moved, and concluded that
count is not the operative variable. Both readings are correct because the
two families rise for different reasons.

In the codebook families attractiveness is **drawn** from a popularity law.
Growing the atom count adds atoms in the same proportions, so the shape of
the law is unchanged and the rise is unchanged. Count is irrelevant there,
exactly as measured.

In the round-8 family attractiveness is **geometric**. A point's capture
basin is bounded by the neighbours competing with it inside its own cluster,
so the number of clusters sets how many rivals each point has. Growing the
count dilutes the competition directly. Count is the operative variable
here.

The general statement is that two mechanisms produce similar-looking rises
and respond to opposite interventions. Diagnosing which one a family has is
therefore not optional, and the cheap way to do it is the intervention run
above rather than inspection of the code.

## The problem with the fix as implemented

The GROWING arm sets the cluster count from n. **A generator that knows its
own corpus size is not admissible here.** The RC-1 grid subsamples a pool
rather than regenerating at each n, so a scale-aware generator would produce
different geometry under subsampling than under direct generation. That is
the sampling-operator problem rounds 9 and 11 identified, reintroduced
through the back door.

So this run identifies a cause and demonstrates that acting on it works. It
does not supply an admissible mechanism.

## What round 17 should now be

A process in which the **cluster count grows emergently**, as a consequence
of drawing rows rather than as a function of n. A Chinese-restaurant or
Pitman-Yor process over cluster membership does exactly that, and round 16
already established that such a process delivers the growth it promises,
with nominal exponents of 0.3, 0.5 and 0.7 producing measured 0.329, 0.509
and 0.730.

Round 16 applied that machinery to **popularity**, where count does not
matter, and it failed for the reason above. Applying it to **geometric
clusters**, where count demonstrably does matter, is a different experiment
with a measured cause behind it.

The exponent is a fitted quantity with a bracket already measured. At an
effective exponent of 0 the family gives +0.905 and at 0.5 it gives +0.393,
so the value matching real's +0.51 lies near 0.35 to 0.40. That bracket is
registered here, before the family is built, and the fitted value will be
reported as fitted.

## Status

The campaign plan's round 17 is superseded by this result and will be
rewritten. Rounds 18 and 19 remain held. The plan's own instruction, to
decide with data rather than by the plan, is what produced this revision for
the second time.
