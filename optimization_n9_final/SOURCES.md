# Source ledger and scope

Reviewed 2026-09-23. Source observations are fixed to the hashes below; execution must re-check the actual head. Official technical docs support mechanics, not SOLWEIG speed forecasts.

- Branch checkpoint: https://github.com/AlanSynn/solweig-light/tree/7abe526aae2f97e689b1a1e4ae183e5370f29aa1
- Main checkpoint: https://github.com/AlanSynn/solweig-light/tree/14e888760727583ef782a4dc0e7a5c7c6e6ff9d1
- N8 result: `optimization_v8_native_default/evidence/selection/n8_32_selection_record.json` at the branch checkpoint.
- N8 attribution: `optimization_v8_native_default/evidence/trials/n8_31_tierB_record.json` at the branch checkpoint. Source blob 58d4ba41a6db97a779e7fc84fce383775c4f38ce. Values are independently timed minima composed arithmetically.
- N8 closure: `optimization_v8_native_default/evidence/handover/n8_60_handover.md`.
- Direct producer/classifier: `src/solweig_light/_native_dispatch/direct_aosoa.py`, blob b09325abd6e996205825e218298bb995e8fbc50c. Read all source through the relevant producer/classifier boundaries; the bundled isolated probe transcribes the producer core and has an independent synthetic bit expectation.
- Whole-frame routed execution: `src/solweig_light/radiation/_lw_dispatch.py`, blob 962b9aeee54c47357e40a8b2d23fdd9d915a4d9b.
- Native adapter: `src/solweig_light/_native_dispatch/lw_native_aosoa.py`, blob d010ed82b451ed9964423db6d65d2316a45b8954.
- Driver and dispatch seam: `src/solweig_light/radiation/cylinder_longwave.py`, blob e3b26d34dceb64eb64bab34f8cc494c14d392f38.
- Package anchoring: `src/solweig_light/_native_dispatch/__init__.py`, blob 26ece71039ff997d63779868a513d2aab25ff05f.
- Native gates: `optimization_v8_native_default/PROMOTION_POLICY.md`, blob 5803c7589d10d1190e663834d57122ab2c0a70ca.
- Git merge mechanics: https://git-scm.com/docs/git-merge (official, checked in this session).

The repository was read through the GitHub connector. The local container had no direct GitHub network access and no GDAL module. No repository checkout was modified, no remote write/CI trigger performed, no SOLWEIG/native/target-M1 pipeline was executed. The local isolated decode experiment uses Python 3.13.5, NumPy 2.3.5, Numba 0.65.1 on Linux x86_64; project target versions differ. Do not use it as a golden or proof of platform deployment.
