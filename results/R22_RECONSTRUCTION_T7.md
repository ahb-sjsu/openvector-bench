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
| 4 | corrupted chunk detected and rejected | **PASS** (tamper); signature **not exercised** |

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

1. **The signature is untested.** There is no GPG secret key on Atlas, so the
   run used `--sign` unset. Criterion 4's tamper clause passed; its signature
   clause did not run. `DISTRIBUTION.md` wants the same identity that signs the
   repository's commits, so this needs the author's key rather than an
   ephemeral one — the code path exists (`sign_manifest`/`verify_signature`).
2. **All sources were local filesystem.** No NRP S3 bucket, no Zenodo DOI, no
   origin fetch. Phase 1's multi-region and durable-mirror claims are untouched,
   and the per-source latencies above are storage-local, not network.
3. **One toolchain.** Regeneration was exact within a single Python/numpy build.
   The reportable §3 actually cares about — regeneration-success rate *across*
   toolchains and platforms — is untested here, and it is the interesting one,
   since it decides whether the regeneration tier is a reliable source or an
   occasional optimisation.
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

1. Re-run with `--sign <keyid>` to close criterion 4 properly.
2. Publish one shard set to a real remote (NRP S3 or Zenodo) and re-run so the
   fetch tier is network-backed and the latency figures mean something.
3. Run regeneration on a second toolchain (different numpy/platform) and report
   the cross-toolchain success rate — the number §3 is actually about.
