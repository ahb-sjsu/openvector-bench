# Tamper-evident anchoring — RC release checklist

The scientific value of RC-1/RC-2 is that the goalposts were fixed **before** the
sealed data was seen (`PREREG_RC1.md` §1, §6, §7). Today that ordering rests on
git history plus a GPG signature — both of which the repository owner can rewrite
(`git commit --date`, force-push). This checklist removes the author from the
trust path for the one property that matters: **the registered spec and the
frozen candidate provably predate the sealed reveal and the results.**

It uses **OpenTimestamps** (OTS), which anchors a file's hash into the Bitcoin
blockchain and returns a proof. This is *not* "run a blockchain": no chain is
operated, no token is held, no consensus is added to the project. A public chain
is borrowed only as a decentralized, un-backdatable clock — the single blockchain
property this project actually needs (see the design note in the README /
`GENERATOR_SEARCH.md`).

## What OTS proves, and what it does not

**Proves (per anchored file):** the file's exact bytes existed **no later than**
the Bitcoin block time in its proof. Nobody — including the author — can
manufacture a Bitcoin attestation dated in the past, so a spec cannot be
backdated after seeing results.

**Does not prove:**
- **That the seal was never peeked.** A timestamp orders events; it cannot show
  that a copy of the sealed 25% was not evaluated early. Peeking is mitigated by
  *custody* (§7's hashed seal + optional third-party escrow), not by anchoring.
- **That the content is correct or the run was honest.** Anchoring fixes *when*,
  not *whether the numbers are real*. Byte-reproducibility (any party regenerates
  the corpus and re-runs the gates) is what makes the results themselves
  trustless; anchoring only fixes the timeline around them.
- **Non-grinding on its own.** Anchoring ten weakened prereg variants and later
  revealing the convenient one would also produce valid timestamps. This is
  defeated by **public, singular disclosure**: the prereg is committed and
  announced at anchor time (step 1), so alternates would be visible. Anchor +
  public commit together, never anchor alone.

## What gets anchored, and when

Anchor in this order; the whole point is the provable ordering
`T_prereg < T_seal < T_results`.

| # | artifact | anchored when | fixes |
|---|---|---|---|
| 1 | `spec/PREREG_RC1.md` (+ `FAMILY.md`, `GENERATOR_SEARCH.md`) | the moment a spec version is frozen (i.e. now, for v2) | the goalposts |
| 2 | `SEAL.md` (SHA-256 of the one frozen generator source+params, §7) | immediately before the sealed 25% is opened | the candidate |
| 3 | the RC-1 / RC-2 results file | at submission, after the sealed run | the outcome |

Re-freezing any spec, or changing the generator after step 2, starts a **new**
anchor and is reported as a second evaluation (§7) — the old proof is kept, never
replaced.

## Commands

One-time: `pip install opentimestamps-client` (provides the `ots` CLI; needs no
account and no wallet).

```sh
# 1. STAMP at freeze time — produces a pending proof next to the file.
ots stamp spec/PREREG_RC1.md            # -> spec/PREREG_RC1.md.ots
git add spec/PREREG_RC1.md.ots
git commit -S -m "anchor: OTS-stamp PREREG_RC1 v2 (pending Bitcoin confirmation)"

# 2. UPGRADE once Bitcoin has confirmed (minutes to a few hours) — embeds the
#    block attestation so the proof is self-contained and no longer needs the
#    calendar servers.
ots upgrade spec/PREREG_RC1.md.ots
git add spec/PREREG_RC1.md.ots
git commit -S -m "anchor: upgrade PREREG_RC1 v2 proof with Bitcoin attestation"

# 3. VERIFY (anyone, any time). Needs the original file's exact bytes present.
ots verify spec/PREREG_RC1.md.ots       # prints the Bitcoin block time
ots info   spec/PREREG_RC1.md.ots       # human-readable proof contents
```

Repeat 1–2 for `SEAL.md` at seal time and for the results file at submission.
(Exact flags and the Bitcoin-header source used for verification are in the
opentimestamps-client README; `ots verify` will use a public block explorer or a
local node.)

## Proof custody

- Every `*.ots` proof is committed **beside** the file it anchors and listed in
  `spec/ANCHORS.md` (one row: artifact path, sha256, `ots info` block time,
  commit). That index is the human-auditable summary; the `.ots` files are the
  machine-checkable evidence.
- Proofs are **append-only**. A superseded spec keeps its proof; a new version
  gets its own. Deleting a proof is a red flag and is called out in review.
- The proofs are worthless if the original bytes drift, so anchored files are
  frozen: after `ots stamp`, edits require a new version + new anchor, never an
  in-place change.

## Third-party verification (put this in the release notes)

> To check that the RC-1 goalposts predate the sealed result yourself:
> `pip install opentimestamps-client`, then from a clone at the release tag run
> `ots verify spec/PREREG_RC1.md.ots` and `ots verify SEAL.md.ots`. Confirm the
> `PREREG` block time is earlier than the `SEAL` block time. Neither we nor
> GitHub can forge or reorder those Bitcoin timestamps.

## Not adopted (and why)

- **A project-run chain / smart contract / token.** No multi-party consensus
  problem exists here; it would add operational surface and prove nothing extra.
- **On-chain data.** The corpora (10⁶–10¹² vectors) live in content-addressed
  manifests; only 32-byte hashes are ever anchored.
- **A transparency log (Sigstore/Rekor)** is a reasonable *addition* if RC
  submissions ever come from multiple external parties — an append-only Merkle
  log of submissions complements OTS. It is **not** required for the
  single-maintainer case and is left as a future option, not a step here.
