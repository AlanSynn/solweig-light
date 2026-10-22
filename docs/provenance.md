# Source provenance and evidence boundaries

## Two upstream pins

| Purpose | SOLWEIG-GPU commit |
| --- | --- |
| Current source/documentation comparison | [`1fec79a78002f0c7f3f4af817ce34d1952d8b8f3`](https://github.com/nvnsudharsan/SOLWEIG-GPU/tree/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3) |
| Frozen numerical compatibility oracle | [`0d7fe742abeeddd890dd58fc76ed7f78bd47faec`](https://github.com/nvnsudharsan/SOLWEIG-GPU/tree/0d7fe742abeeddd890dd58fc76ed7f78bd47faec) |

The latest inspected upstream still uses Torch with CPU/CUDA device selection;
its [driver](https://github.com/nvnsudharsan/SOLWEIG-GPU/blob/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3/solweig_gpu/solweig_gpu.py),
[thermal processor](https://github.com/nvnsudharsan/SOLWEIG-GPU/blob/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3/solweig_gpu/utci_process.py)
and [numerical routines](https://github.com/nvnsudharsan/SOLWEIG-GPU/blob/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3/solweig_gpu/solweig.py)
support the architectural comparison. Upstream is itself installable; CPU-native
execution and the mechanisms described in [architecture](architecture.md) are
the relevant differences. Inspecting newer source does not regenerate or
upgrade frozen numerical goldens.

Reference environments and candidate environments must remain separate.
Never generate an upstream golden from candidate code or install the legacy
compatibility namespace into an oracle environment. For source-inspection
tests, obtain the frozen revision:

```sh
git clone https://github.com/nvnsudharsan/SOLWEIG-GPU.git .upstream/SOLWEIG-GPU
git -C .upstream/SOLWEIG-GPU checkout --detach 0d7fe742abeeddd890dd58fc76ed7f78bd47faec
```

This checkout is excluded from candidate packaging. Reference generation
additionally needs the original dependency/hardware profile and collector,
not merely this Git checkout. The original initial installation lacked Numba;
adding it repaired the environment without changing upstream source.

## Evidence classes

Retained [tests/reference](../tests/reference) manifests bind fixtures,
source/oracle hashes, invocations and outputs. Distinguish original CPU,
original CUDA where recorded, explicitly patched upstream CPU/CUDA,
independent scientific expectations and candidate results. A mock service
response is evidence of an adapter boundary, not live acquisition.

WRF successful references use the retained
[wrf_timestamp_v1 patch](upstream_patches/wrf_timestamp_v1.patch).
Historical GPU correctness work used a separately authorized patched-upstream
CUDA run with a worker-limit patch and isolated checkout. It is reference
evidence, not an implemented SOLWEIG-light GPU backend, an unmodified CUDA
reference, a universal CPU/CUDA equivalence claim or a GPU speed comparison.
The initial macOS oracle had no CUDA; those unavailable checks remain distinct
from the later patched reference work.

## Validation boundaries

The numerical policy is in
[comparison_v1.json](../tests/reference/contracts/comparison_v1.json).
The portable profile is `solweig-portable-sleef-5a1d179d-v1`, derived from
SLEEF commit `5a1d179df9cf652951b59010a2d2075372d67f68` and canonical original
SOLWEIG-GPU on macOS ARM64 (Torch 2.14.0 source
`08187d9e0fba026dc8217405802ab5381dc88d90`, NumPy 2.4.6, macOS 26.6.2).
It is an explicit reference-profile amendment. Original Linux MKL outcomes
remain separate, including historical strict-boundary failures.

Retained admission records report both macOS ARM64 and Linux x86-64 passing
the 45,172-input, 24-timestep, 153-patch actual-call categorical corpus,
14,400 layout/thread variants per platform, original-SLEEF dense1024 and
vegetation1024 all-field/schema/mask comparisons, and direct cross-platform
comparisons. These are finite validated domains, not all-input proofs.

A final accepted-domain repair made out-of-domain fallback call the actual
NumPy ufunc on the original shape/layout. Source/installed regressions and
small chronological cases passed on both hosts; the 118,422-value physical
trace was bitwise unchanged. Large admissions occurred before that fallback-
only repair and must not be described as reruns of the final repaired wheel.
Full release and renewed benchmark qualification remain incomplete.

The [model ledger](model_deviations.md) and
[scientific exception policy](../tests/reference/contracts/scientific_exceptions.json)
retain four failed independent checks. Compatibility agreement is distinct
from physical correctness. Authenticated acquisition remains unverified.

## Interpreting performance

No architecture-level or universal upstream speedup follows from this port.
A valid comparison matches scene, logical tiles, resolution, patches,
chronology, forcing, physical options, requested outputs and cache/export
state. Report first-use JIT, geometry-cold, geometry-warm and kernel-only
measurements separately, with hardware, dependencies, native threads,
process-tree peak RSS and raw trials. Prior synthetic-corpus measurements
are historical evidence for their exact source/workload, not measurements
of latest upstream or a real study-area scene.

New checks should use the smallest relevant regression/fixture set. Do not
loosen numerical gates, replace an inconvenient fixture or silently change
workload after observing a failure.

## Development records and licensing

The [development supplements](../development/README.md) explain validation and
measurement and link to historical records. Current guidance describes durable
behavior; old campaign results remain evidence only for their recorded source
and workload. Removing an obsolete report does not constitute new validation.

SOLWEIG-light derives from SOLWEIG-GPU and UMEP/SOLWEIG. Preserve original
copyright and GPL notices in translated code. Upstream Python notices say
GPL-3.0-or-later while historical setup metadata says GPL-3.0-only; that
provenance discrepancy is recorded, not silently rewritten. This package
uses GPL-3.0-or-later; see [LICENSE](../LICENSE).
The SLEEF-derived helpers retain their separate
[Boost license](../src/solweig_light/radiation/SLEEF_LICENSE.txt).
