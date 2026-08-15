# Can you fake a dataset? We spent 22 experiments finding out — and the answer taught us something better

*Draft for LinkedIn — Andrew Bond*

For the last stretch I've been running a research program with an unusual
question at its center: **can a computer program stand in for a real
dataset?**

Here's why anyone would want that. Modern AI search runs on *embeddings* —
every Wikipedia paragraph, every product description, every support ticket
gets turned into a list of ~1,000 numbers, and "search" becomes finding
the nearest lists-of-numbers to your query. Testing search engines at
realistic scale takes billions of these vectors — hundreds of terabytes of
data that almost nobody can host, download, or share. But if a small
deterministic program could *generate* vectors that behave exactly like
the real thing, a benchmark the size of a warehouse would ship as a file
the size of an email. Anyone could rebuild it, byte for byte, and verify
it cryptographically.

So: can it be done? We ran the question to ground — 22 pre-registered
experimental campaigns, several hundred generator configurations, every
prediction and failure logged before touching the test data. Three
findings came out the other side, and each one surprised me.

**1. The "dimension" of an embedding dataset measures the filing system,
not the meaning.**

There's a widely-used statistic called intrinsic dimension — roughly, how
many directions the data actually varies in. Embedding datasets show a
famous, strange pattern in it, and the natural reading is that it reveals
something deep about how language models organize meaning.

It doesn't. We found the pattern is produced by something almost
embarrassingly mundane: *paragraphs from the same article sit next to each
other*. Each row of the dataset has about 23 neighbors from its own
article, and after that it's alone in the crowd. Shuffle the row order —
touching not a single vector — and the entire pattern vanishes. The
statistic everyone computes on the embedding is actually measuring how
the corpus was assembled. One consequence for practitioners: comparing
"intrinsic dimension" across datasets without controlling for sampling
and ordering isn't comparing anything at all.

**2. You can fool every geometry test — and still get caught instantly by
a search engine.**

Our best generator passed 8 of 10 registered geometric criteria on data
it had never seen: dimension, contrast, hubness, even the subtle
density-response behavior that provably no i.i.d. model can have. By every
statistic in the standard playbook, it looks like Wikipedia.

Then we put both through an actual search index. The real corpus makes
the index work hard for its answers. Our impostor was **25× easier** —
the index sees through it immediately, because the fake corpus's
neighborhoods line up neatly with the clusters the index builds, while
real data scatters its neighbors everywhere. None of the geometry
statistics see this property at all. If you benchmark a search system on
synthetic data and don't check this, your difficulty numbers are fiction.
(We've since packaged the check as a one-command audit, and calibrated
it across four real corpora — real datasets themselves vary 3× in
difficulty, which is its own caution.)

**3. The test we built to admit generators turned out to be a
memorization detector.**

The deepest result came from the test we could never pass. Real *queries*
— the things users actually search for — carry information about exactly
where they land in the real data cloud. We proved, across every mechanism
we were allowed to use, that no honest generator can reproduce this: not
with clever math, not with statistical summaries of the data, not even
when we let the generator lean partway toward literal stored rows. The
gap only closes when you cross the line into just... storing the dataset.
And here's the elegant part: the amount of data you compress into the
generator barely matters. We traced the whole curve from "4 megabytes of
statistics" to "the entire dataset" — it's flat. What matters is how far
you *displace* your synthetic points toward the real ones, and the
corpus's own geometry police that displacement. Our admission test,
designed to check realism, was unknowingly a detector for whether a
"synthetic" dataset is secretly a copy.

**What I'd tell my students**

The result I'm proudest of isn't a number — it's that the program was run
so it could lose. Every campaign declared its mechanism, its predicted
outcome, and its kill criterion *before* running; frozen candidates were
judged once, on held-out data, no retries; when a verdict went against
us, it stood. Eleven mechanisms died this way, each killed by its own
pre-stated falsifier — and the map of those failures turned out to be
the publishable result. We even measured the verdict process itself and
caught it being a lottery (small held-out samples flip verdicts on
sampling noise alone — so we fixed the protocol, and the fix is now a
rule).

Science isn't the art of being right. It's the discipline of making it
cheap to find out you're wrong.

The whole record — every experiment, every dead end, the frozen
generator, the audit tools — is public:
**github.com/ahb-sjsu/openvector-bench**. Two papers are on their way.
If you work on vector search, embeddings, or benchmark design — or
you're a student who wants to see what a fully pre-registered research
program looks like in the open — I'd love to hear from you.
