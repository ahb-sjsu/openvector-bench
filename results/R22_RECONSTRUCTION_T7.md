# The reconstruction experiment passes at 10⁷ rows

**`spec/DISTRIBUTION.md` §6, run for the first time.** That document has said
since it was written: *"Until that experiment passes, this is a design, not a
result."* It is now a result.

Measured 2026-08-08 on Atlas, single-threaded (Package 0 was at 80 °C with an
unrelated job running, so this took one core). Driver
[`harness/distribution/reconstruct_experiment.py`](../harness/distribution/reconstruct_experiment.py),
report [`r22_reconstruction.json`](r22_reconstruction.json), work directory
`/archive/experiments/ovb_recon`.

**Note on provenance:** the driver, `openvector_bench/manifest.py` and
`openvector_bench/reconstruct.py` already existed in registered form. This round
contributes the *run*, not the code.

## Configuration

10,000,000 rows × 128-d **uint8** (`refcorpus.philox-u8:v0`), 10 shards of
1,000,000 rows, 8 MiB chunks, 256 held-out queries, exact k-NN. Corpus 1.28 GB
— which is the `DISTRIBUTION.md` sizing basis (128 TB at 10¹² rows, 128-d
uint8), so this is the T7 rung of the real thing rather than a toy.

## The four registered criteria

| # | criterion | result |
|---|---|---|
| 1 | every shard verifies against its Merkle root | **PASS** |
| 2 | reconstructed bytes identical to the originals | **PASS** |
| 3 | index returns **identical** answers for a fixed query set | **PASS** |
| 4 | signature verifies **and** corrupted chunk detected | **PASS** (both clauses) |

The signature clause was closed in a second run
([`r22_reconstruction_signed.json`](r22_reconstruction_signed.json)) with a real
detached GPG signature from the repository's own commit-signing key
(`ed25519/E5B1306234254456`), giving `4_signature: true` alongside
`4_tamper_detected: true`. That run was executed on the workstation rather than
Atlas because the key lives there; every other number below is from the Atlas
run and the two agree on criteria 1-3 and on all reportables.

Criterion 2 is checked by an independent whole-file SHA-256, not by the
manifest's own chunk hashes, so it is not circular. Criterion 3 is exact k-NN
with identical ids required — not a recall statistic.

## The source mixture was forced, not hoped for

This is the methodological point. §6 requires "deliberately disabling some, so
the mixture includes regeneration, cache, and mirror". The driver mis-salts odd
shards, so regeneration *provably* produces wrong bytes for half the corpus:

| | count |
|---|---|
| regeneration attempts | 10 |
| regeneration hits | **5** |
| forced cache misses → fell through | **5** |
| mirror fetch attempts | 5 |
| mirror fetch hits | **5** |

Every mis-salted shard produced a hash mismatch, was recorded as a *cache miss*
rather than an error, and resolved from the mirror — which is the §3 degradation
path executed end-to-end rather than asserted. A regeneration tier that silently
returned wrong bytes would have failed criterion 2; it did not.

## Reportables (§6 requires these regardless of pass/fail)

- **Total bytes moved: 640,000,000** — 50.0% of the 1.28 GB corpus, exactly the
  half regeneration was sabotaged for. **The 5 regenerated shards moved zero
  bytes.** This is the number that makes the case at trillion scale: with an
  intact generator the figure goes to zero and the corpus is distributed by a
  12 KB manifest.
- **Regeneration success rate: 0.50**, by construction (the other half was
  deliberately broken). This run says nothing about the *natural* rate.
- **Per-source latency:** regeneration 2.198 s for 5 shards (~0.44 s/shard);
  mirror fetches 0.074–0.114 s/shard. The fetches were local filesystem, so
  that comparison is not meaningful for a real network source — see limits.
- **Manifest size: 12,368 bytes** for 1.28 GB = **9.7 MB per TB**. Worth
  recording: `DISTRIBUTION.md` §2 estimates ~4 MB/TB, which is right for raw
  32-byte hashes but roughly half the JSON hex-encoded form actually written.
  Extrapolated, a 1 PB corpus needs a ~9.7 GB manifest and 400 PB needs ~3.9 TB
  — confirming that the enumerated manifest breaks somewhere in the PB range and
  must become **derived** (publish the root; recompute subtree hashes locally;
  ship an O(log N) proof per shard). That fallback is only available because
  regeneration is exact.

## What this licenses, and what it does not

**Licensed:** at 10⁷ rows, the corpus is a cryptographically defined
distributed object. Delete every materialized file, keep the manifest, and
reconstruct byte-identical shards from a mixture of regeneration and remote
sources, with an index that answers identically and corruption detected.

**Not licensed, and each is a real gap:**

1. ~~The signature is untested.~~ **CLOSED** — signed and verified with the
   repository's own commit-signing key, exactly the identity `DISTRIBUTION.md`
   §2 names. Closing it exposed a real bug: `sign_manifest` invoked a bare
   `gpg`, and on Windows a Git-for-Windows install ships its own GnuPG with a
   *separate keyring*, so `gpg` on PATH resolved to a binary that does not hold
   the key — failing with `No secret key`, which reads like a missing key rather
   than the wrong program, while git itself signs commits happily via its
   configured `gpg.program`. `manifest.gpg_program()` now resolves
   `$OVB_GPG` -> `git config gpg.program` -> `gpg`.
2. **All sources were local filesystem.** No NRP S3 bucket, no Zenodo DOI, no
   origin fetch. Phase 1's multi-region and durable-mirror claims are untouched,
   and the per-source latencies above are storage-local, not network.
3. ~~**One toolchain.**~~ **CLOSED 2026-08-11** — regeneration is exact
   *across* toolchains. Sixteen shards, indices 0 to 10^12 (including 2^31-1 and
   2^32+17), regenerated on two genuinely different platforms:

   | | local | remote |
   |---|---|---|
   | platform | Windows-10-10.0.19045 | Linux-6.8.0, glibc 2.39 |
   | python | 3.12.2 | 3.12.3 |
   | numpy | **2.3.5** | **2.4.4** |

   **16/16 byte-identical, a 100% cross-toolchain regeneration-success rate**
   (`results/xtoolchain.json`). Different OS, libc, Python patch and numpy
   *minor* version. This is the reportable `DISTRIBUTION.md` §3 actually cares
   about, and it settles the question in the strong direction: the regeneration
   tier is a reliable source, not an occasional optimisation.

   The reason it holds is structural rather than lucky — `philox_u8` is pure
   integer arithmetic over a counter-based bit generator, with no floating point
   anywhere in the path, so there is nothing for a platform to round differently.
   That property is a design requirement for any RC-1 emitter, not a happy
   accident of this one.
4. **Not the RC-1 corpus.** This is 128-d uint8 from `philox_u8`. It validates
   the distribution mechanism, not any claim about RC-1's geometry.

## Why this mattered enough to run today

Beyond closing a standing gap in the spec, this is the dependency for the
**I-EIP Monitor** (`erisml-lib`, `docs/I-EIP_Monitor_Whitepaper.md` §4), which
names the calibration corpus as an attack surface and lists "signed corpus,
reproducible extraction" as the mitigation. I-EIP needs ≥10k calibration inputs
with that property — four orders below this run — so the mechanism is now
demonstrated well past what it requires.

The same proof underwrites attested reads of large model weights: nobody hashes
20 TB per inference, so a probe that claims to have read the signed weights
needs exactly this partial-verification chain.

## Next

1. ~~Re-run with `--sign`~~ — DONE, criterion 4 fully closed.
2. Publish one shard set to a real remote (NRP S3 or Zenodo) and re-run so the
   fetch tier is network-backed and the latency figures mean something.
3. ~~Run regeneration on a second toolchain~~ — DONE, 16/16 byte-identical
   across Windows/numpy 2.3.5 and Linux/numpy 2.4.4.
