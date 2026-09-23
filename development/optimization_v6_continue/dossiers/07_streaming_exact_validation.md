# D07: validate stored exports once, not less thoroughly

## Source-grounded motivation

Fresh `_export` writes all legacy artifacts and invokes `_compare`. `_compare` calls `_validate`; legacy validation consumes the NPZ members completely to check length/CRC. `_compare` then imports the NPZ again, reencodes it into packed channels and iterates patches/pixel chunks to compare against the native fields. TIFF payload/schema reads also repeat. [S05/S14]

At 1024/P153, three float32 visibility cubes contain 1,836 MiB of uncompressed payload. This is the serialized size, not DRAM traffic and not compressed on-disk size. Multiple full decompressions/encodings are plausible cold-work costs. Measure the exact active call sequence and bytes, not just expected compression ratios.

## Proposed success-path validator

Open each immutable STAGED NPZ member once. Validate archive member set/duplicates, NPY version, dtype/endianness, C/F order, shape, declared byte count and actual EOF/CRC. For C-order [rows,cols,patches], read bounded complete pixel rows `(B,P)` and compare uint32 views with the correspondingly decoded native channels. Full CRC verification requires consuming through EOF/close; do not stop reading on the first mismatch and silently skip CRC.

No full dense cube, no import-to-packed-to-decode roundtrip, no stored time history. Reuse caller-owned BxP expected/actual workspaces. F-order arrays, alternate valid endian/layout or other public supported formats may use the old path until the streaming adapter preserves exact byte interpretation. Malformed formats must not become accepted. The exported format remains unchanged.

For TIFFs, extract/consume a ZIP member for full CRC once, validate the GDAL metadata and compare bounded stored pixels in the same file pass. Keep nodata, masks, metadata domains, affine transform, projection rules, dtype, member names and completeness checks. Do not replace stored-read equality with equality of a producer-side buffer.

## Preserve failure precedence and ownership

The baseline checks schema/CRC before numerical mismatch. A fused loop may discover a value mismatch before EOF reveals bad CRC. Store a mismatch flag/location, finish structural validation and raise in original precedence. For complex combined-corruption cases, fall back to the untouched validator to classify the same failure; failure performance is not the target. Bounds and zip-bomb safety must be maintained.

New staged files are private to a producer until publication. The verifier still uses required stable-source checks and destination locks; do not generalize to mutable external artifacts without guarding their lifetime. Exact verification is a certificate of the stored bytes just read. It is not permanent trust against later external corruption. Warm cache opens still follow their required integrity policy.

After validation, required fsync, sorted destination ownership, atomic manifests, rollback and publication remain unchanged. Checkpoint interval/readback guarantees remain unchanged. The successful single pass can reduce repeated work without weakening content validation.

## Minimum experiments

1. Count actual decompressions/imports/NPZ logical bytes in a tiny fresh export and separate kernel production from I/O.
2. Test original and new validator on generated binary/ternary/raw -0/NaN payloads and valid endian/layout variants, one corruption at a time.
3. Test combined malformed shape+CRC/value errors to preserve accepted-domain and diagnostic failure behavior.
4. Round-trip full 19-field geometry and ensure no temporary path leaks, changes to legacy names or changed output flags.
5. Crash/rollback tests keep existing artifacts intact. Warm existing cache mutation invalidates trust.
6. Time complete small cold pipeline; savings from duplicate geometry and validator read reductions are not multiplied, but inserted as separate measured phase demands.

This work is conditional on actual E/validation cost after D02. Do not start with elaborate compressed formats, zarr dependency, lower precision or changing default compression to manufacture a favorable benchmark.
