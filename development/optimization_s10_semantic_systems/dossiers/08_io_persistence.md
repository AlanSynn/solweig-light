# D08: Repeated traversals, input identity, checkpoint and publication

Candidates S05/S07-S12. Sources S14/S15/S17/S18/S30. Treat this as an integrity-preserving I/O project, not permission to remove safeguards.

## Input hashes
InputGuard rehashes file contents at several checkpoints. Those checks detect external changes and cannot simply be cached by path/mtime. Distinguish: (1) hashing the SAME bytes during an already mandatory traversal, (2) remembering a hash within a truly immutable snapshot, (3) incorrectly assuming the file never changes. Only 1 or proved 2 preserves the contract. Raster-value hashing does not replace file-byte hashing.

A new snapshot protocol would itself be a versioned behavior change unless it retains external-change detection at original boundaries. The first implementation should reduce redundant traversal WITHIN a checkpoint and reuse implementation manifests only where runtime source is fixed. Measure bytes per checkpoint before investing; many small source hashes may be negligible compared with raster decompression.

## Legacy geometry export verification
Current _compare first validates archive/schema, then reads TIFF values, then imports NPZ, re-encodes visibility and decodes expected/actual to compare. A single stored-stream validator can combine integrity and value checks in one pass, but must still consume all payloads and validate CRC, dtype, endian, shape, member names, duplicates, extra/truncated data and metadata. Never substitute a digest of the in-memory candidate for verification of the stored artifact.

Exception precedence matters. If current schema/CRC validation finishes before value comparison, early mismatch must not hide a later schema error. Either defer mismatch reporting until the structural traversal completes or re-run the original validator only on failure. Successful work can be one pass while rare failure retains original taxonomy.

Keep streaming workspace bounded. Equality/hash byte order must match original raster order, not convenient block order. GTiff may canonicalize signed-zero-only blocks; retain stored-byte rules. Do not change compression, TIFF tiling or NPY serialization layout under a byte-level artifact contract without explicit authorization. Schema-equivalent compression is a separate policy if byte equality is not required.

## Checkpoint serialization
Current `_encode` builds a complete NPY in BytesIO and obtains payload bytes, then writes and hashes them. It already avoids a second disk read for that hash. New target: eliminate large temporary byte copies using a hashing sink or explicitly serialized header+bounded array chunks. Verify actual np.save seek/write behavior and header alignment. Preserve scalar vs ndarray/container tags, Fortran order, endianness, filenames, exact hashes and durable write order.

Deduplicating unchanged checkpoint payloads is lower priority. Prior payload can be corrupted after it was once validated. Reusing it must preserve corruption checks, fsync commitments, manifest reachability and cleanup. Pointer or ndarray identity does not prove immutable content. No checkpoint interval change under the default workload.

## Output overlap and publication
A bounded queue may overlap independent work only when the writer gets an immutable snapshot or a transferred buffer lease. Caller cannot reuse it before acknowledgement. Cursor commit waits for all bands/state required by that checkpoint. On writer failure cancel/drain workers, close handles and fail loudly. Publication order and destination locks remain as in main.

Geometry export staging can run across independent tiles while final publication stays ordered. Measure serial publication as its own phase. Parallel compression competes for CPU; include it in budget. A failed tile must not leave later outputs visible when the original ordering would not.

## Preprocessing reuse
Public create_tiles can clear/recreate folders and write exact logical windows with one-sided overlap. Read-only view/VRT or hardlink shortcuts can alter resulting artifacts, permissions and source ownership. Prefer documented validated reuse only if existing output/error semantics can be retained; otherwise keep this as a separate opt-in operational proposal, not a default optimization.

## Failure suite
Same-size/mtime source replacement; mutation during read; late NPZ CRC failure; missing/duplicate members; raw nonfinite payload; TIFF zero canonicalization; disk-full simulation; interruption before/after fsync/rename; rollback of partial publication; stale or corrupt checkpoint generation; concurrent destination owners; read-only install; descriptor leak; writer lag and buffer overwrite. Start tiny, not 1024-scale corruption campaigns.
