# Full-computation evidence inventory

## Delivery status

Five verified ZIP archives were prepared for this PR on 2026-10-20. Their
original local files remain at
`/workspace/scratch/2c9f54f632af/evidence_archives_20261020/`.
They can be delivered to the repository owner from the current task.

**Durable upload is not complete.** The standard upload helper first stopped
before upload because its authentication configuration was unavailable. An
escalated attempt was then rejected by automatic approval review: sending the
archives, including logs and environment/provenance metadata, to ChatGPT Library
required explicit authorization for that destination. No upload succeeded and
no alternate transfer was attempted. Dropbox synchronization was not performed.
These local paths are not durable public archive URLs. The PR remains a draft,
and evidence archival closure remains open until an authorized save succeeds.

## Archives

Every ZIP was independently decompressed and checked against its per-member
SHA-256 manifest and CRC. Selected originals were rehashed afterward and remain
unchanged. Every ZIP contains its own README, manifest and checksum list.

| Archive | Exact bytes | SHA-256 |
|---|---:|---|
| `full_compute_evidence_core_20261020.zip` | 4,346,227 | `2847e88a5a3743e17e59b504bb93f98adaa721cf020e8de8709ffec2efb76e7f` |
| `full_compute_round2_pair0_reference_20261020_part01.zip` | 33,916,398 | `faac0629e1288562fdef08aef51dfbcdd9f988c65fdef3568af7e60ed47da6bc` |
| `full_compute_round2_pair0_reference_20261020_part02.zip` | 20,695,573 | `0079f7dbed630f4883ad7c985dc8868830f847bb4cf43261549f2326ed4b975c` |
| `full_compute_round2_pair0_candidate_20261020_part01.zip` | 40,362,239 | `fafaef9e63e11af9f933b3cf0b94e1f73ccb0de80ba9fd7e78bc598ef0fccc4d` |
| `full_compute_round2_pair0_candidate_20261020_part02.zip` | 20,698,172 | `1c6728aac51a1a2a6a7dc36943b570a912ae9d3653256baa9c8f75140445acd9` |

## Included evidence

- **Core archive:** 322 original payload files. This includes the original
  failed first attempt, fixed-budget round 1, final round 2, all trial reports,
  stdout/stderr, stage events, source/environment/input identities, original
  profiles, checker amendment and continuation records, compression and encoder
  family trials, focused validation logs, and the actual generated input scene
  (four TIFFs, meteorology and input manifest).
- **Installed-wheel records:** original validation and manifests, the source-pin
  amendment, bootstrap diagnostic, and unchanged isolated concurrency follow-up.
  The initial 166 passes / three failures remain preserved; two failures
  explicitly report memory admission and the third is a pause/event timeout
  of unestablished cause. The same three tests passed separately. Both main and
  candidate longwave NaN diagnostic failure logs are retained.
- **Representative reference/candidate pair:** the first measured pair from
  final round 2. Each role has two independently readable ZIP parts. Part 1
  contains the three legacy SVF artifacts and the complete TMRT TIFF. Part 2
  contains the complete UTCI TIFF, final checkpoint transaction and generation
  state, and original trial specification/result/inventory. All nine state NPY
  payloads are present. The checkpoint resolves to `next_timestep=19`.

Both representative final checkpoint state hashes are
`5bbc3d1233421fdc55f20248ed710612a73ec3b00848e1673077745829cbc5e0`.

## Deliberate exclusions

Only one representative pair of full output rasters and final checkpoints is
included. Reports and correctness results cover all measured pairs, but this
is **not an archive of every repeated bulk output**. Other trial scenes and
checkpoint histories remain in the original local benchmark directories.

The archives exclude JIT/native geometry caches, installed environments and
wheels, full source snapshots, Git-backed source/document copies, commit-payload
JSON, repeated inputs/outputs, inflated comparison scratch arrays, and bulk
compression-family artifacts. Recorded artifact hashes/sizes are retained.
No selected file was truncated. No required selected validation log is missing.

## Source and reproduction

- Main: `288d70e2b3bd8ca5bba4b65e572048fea37bcc51`.
- Final numerical candidate: `afa54cb3041e9481ad6691b4c71c1e5ec0362d5a`.
- Final comparison JSON SHA-256:
  `273da534cab7c8ba32b6a2d66925d963d661537a2414a7d262faa441aa67eafc`.
- [Round 1](ROUND1.md) records the first profile and preserved checker amendment.
- [Round 2](ROUND2.md) records complete measured trials, exactness, hashes and
  invocation. [The harness protocol](../docs/full_compute_benchmark.md) defines
  the matching public computation and original-data reproduction.

The original Atlanta input tile and `02_CPU_SpeedTest.py` are still unavailable.
The archived generated scene must not be relabeled as those original inputs.
