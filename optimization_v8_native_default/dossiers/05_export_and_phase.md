# Conditional cold-throughput track: exact storage validation and phase scheduling

## Residual, not a new geometry duplicate claim

Common geometry recipe and phase adapter already exist. B7-60 recorded cold geometry stage 383.408s, producer 172.6287s; the difference 210.7793s includes storage/validation/compression/cache/publication work, not pure disk IO. These are reported numbers, not this packet's measurements. Split this remainder before implementing anything.

Inspect stored payload traversal count: CRC/schema validation, import/re-encode, expected/actual decode comparison, fingerprinting and transaction fsync. Current checks may read the same large payload more than once. The objective is to perform necessary validations together, not waive them.

## One bounded stored-stream pass

For fresh exported artifacts, parse exact member inventory/header/version/order/endian/shape/size, stream all payload bytes for CRC, compare bitwise against the expected packed field using bounded microchunks, and collect existing required content fingerprint information at the correct file boundary. Do not construct a full dense cube or re-encode a full imported copy solely for comparison.

A byte-stream CRC and a comparison of decoded floating values answer different questions; retain both. Archive errors, truncated data, duplicate names, Fortran layout, big endian and unsupported version get the same contract or an intentional retained diagnostic fallback. If a numerical difference is detected before an eventual CRC error, preserve error precedence by finishing structural checks or calling the old diagnostic validator on failure. Failures never publish artifacts.

## Phase concurrency

Keep native geometry reuse and its barrier. Independent expensive compression/validation may stage in private tile-specific directories under bounded worker admission; ordered parent publication preserves the old prefix/failure contract. Each writer owns its datasets. Count simultaneously staged results and disk queues. Do not let all 24 completed unpublished exports remain resident.

Retain input-change guards at original lifetime boundaries. Do not replace SHA content checks with mtime/size shortcuts. Sharing an immutable input fingerprint within a verified invocation is a separate design requiring an unchanged mutation-detection contract, not a blanket memoization decorator.

## Throughput attribution

CPU service, serialization bytes, disk bytes and latency are distinct. Hardware-compression/thread changes must be inside total CPU admission. Report stage time plus full cold entry, not `export_calls_total` added to its included producer time. Avoid double counting nesting.

This track may improve cold end-to-end throughput without helping native contribution. Report it as storage/system improvement, not native SIMD speed. It can run independently of AoSoA experiments with separate files and review, but benchmark execution remains exclusive.
