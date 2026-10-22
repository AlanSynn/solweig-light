# SOLWEIG-light

SOLWEIG-light runs SOLWEIG urban radiation and thermal-comfort workflows on
CPU using NumPy, SciPy, Numba and GDAL. The local meteorological-file/TIFF
workflow does not require Torch, CUDA or network services. It calculates mean
radiant temperature (TMRT), UTCI and optional radiation, shadow, SVF, WBGT,
air-temperature and wind outputs.

This repository changes the execution of
[SOLWEIG-GPU](https://github.com/nvnsudharsan/SOLWEIG-GPU), while retaining its
model workload and seven public workflows. The current source comparison uses
upstream commit `1fec79a78002f0c7f3f4af817ce34d1952d8b8f3`; numerical references
remain frozen at `0d7fe742abeeddd890dd58fc76ed7f78bd47faec`. These are different
purposes, not a claim that the latest upstream revision has been revalidated.
See [provenance](docs/provenance.md).

## What changes

| Area | SOLWEIG-light |
| --- | --- |
| Numerical execution | CPU arrays and compiled kernels replace Torch tensor execution. |
| Geometry | Lossless packed visibility, compiled rays and SVF count/replay avoid repeated dense patch work. |
| Radiation | Pixel-owned, ordered LW/SW and anisotropic reductions use bounded blocks and guarded lane kernels. |
| Repeated timesteps | Static geometry and longwave visibility predicates are reused; thermal state stays chronological. |
| Resources and outputs | Explicit CPU/memory admission, controlled workers, streamed bands and resumable transactions. |
| Cache validity | Content identities and checksums replace reliance on legacy artifact existence. |
| GPU support | Not implemented. Existing numerical boundaries leave room for a future backend; no CUDA execution is supplied. |

[Architecture](docs/architecture.md) explains the actual optimization points.
No universal speedup over SOLWEIG-GPU is claimed. First-use compilation,
geometry, exports, scene shape and thread configuration all affect runtime.

## Install and run

Use Python 3.11 or newer in an environment separate from upstream SOLWEIG-GPU.
Install native GDAL first, with a version matching the Python GDAL bindings
required by [pyproject.toml](pyproject.toml) (currently GDAL 3.13.x). Then install
from the repository root:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install .
```

A pinned macOS ARM64 environment is available in
[requirements/macos-arm64-py311.txt](requirements/macos-arm64-py311.txt).
Other platforms need their own matching native GDAL installation.

Prepare aligned GeoTIFFs and meteorological data in a scene directory:

| File | Meaning |
| --- | --- |
| `Building_DSM.tif` | Terrain plus buildings, in metres above the elevation datum. |
| `DEM.tif` | Bare-earth terrain, in metres above the same datum. |
| `Trees.tif` | Canopy height above ground, in metres; zero without trees. |
| `met.txt` | Local UMEP-format meteorological text file. |

Rasters must share dimensions, CRS and geotransform. Land cover is optional
and supplied with `landcover_filename`. Use absolute meteorological paths:
explicit relative met filenames resolve against the working directory.

```python
from solweig_light import thermal_comfort

thermal_comfort(
    base_path="/absolute/path/to/scene",
    selected_date_str="2020-07-18",
    own_met_file="/absolute/path/to/scene/met.txt",
    ERA_5_z0_find=False,
)
```

Or run:

```sh
.venv/bin/solweig-light --base_path /absolute/path/to/scene \
    --date 2020-07-18 --own_metfile /absolute/path/to/scene/met.txt \
    --era5_z0_find False
```

`ERA_5_z0_find=False` selects the local setup above. Its API default is `True`
and attempts ERA5 roughness/wind generation. Optional integrations require the
[corresponding extras](docs/compatibility.md#optional-integrations).

UTCI is always written; TMRT is also written by default. Files live under
`<base_path>/output_folder/<tile>/`, with timestamped GeoTIFF bands. The
`save_kup`, `save_kdown`, `save_lup`, `save_ldown`, `save_shadow`, `save_wbgt`,
`save_ta` and `save_wind` flags enable additional fields. `save_svf=True`
requests a static, single-band `SVF_<tile>.tif` only when no complete legacy
SVF artifact set already exists. Default compatibility exports usually
suppress that separate output, preserving upstream behavior.

`export_svf=False` omits compatibility SVF TIFF/ZIP/NPZ exports without
skipping model geometry or changing `save_svf`. Existing exports remain in
place. The default is `True`; CLI syntax is `--export_svf False`.

## Execution options

CPU controls are separate from the upstream-compatible workflow arguments:

```python
from solweig_light import RuntimeOptions, runtime_options, thermal_comfort

with runtime_options(RuntimeOptions(
    cpu_budget=4, workers=1, threads_per_worker=4,
)):
    thermal_comfort(
        base_path="/absolute/path/to/scene",
        selected_date_str="2020-07-18",
        own_met_file="/absolute/path/to/scene/met.txt",
        ERA_5_z0_find=False,
        export_svf=False,
    )
```

Choose a budget within the available CPUs. Defaults use one worker and one
native thread. Resident longwave predicate reuse is enabled by default; use
`RuntimeOptions(resident_lw_masks=False)` for the lower-memory route. Its extra
allocation is about 52.53 MiB for a 600×600 tile with 153 patches, and grows
with tile area. [Runtime](docs/runtime.md) describes exact accounting,
admission, caches and restart.

## Documentation and verification

- [Architecture](docs/architecture.md): source comparison and optimization mechanisms.
- [Runtime](docs/runtime.md): CPU controls, memory, cache validity and recovery.
- [Compatibility](docs/compatibility.md): seven APIs, CLI/import compatibility, extras and numerical policy.
- [Model deviations](docs/model_deviations.md): inherited limitations, explicit repair and reference-profile boundaries.
- [Provenance](docs/provenance.md): upstream pins, reference evidence and attribution.

A focused local differential check is:

```sh
.venv/bin/python -m pip install '.[test]'
.venv/bin/python -m pytest tests/differential/test_pipeline_reference.py -q
```

It executes real TIFF workflows against retained upstream CPU artifacts;
source-inspection tests elsewhere additionally require the frozen upstream
checkout. Existing tests and manifests provide fixture-specific evidence,
not proof of every scene or platform. Four inherited independent scientific
checks remain failed with a documented compatibility exception. Full release
qualification remains incomplete. There is no shipped GPU backend; historical
patched-upstream CUDA references are separate evidence, and authenticated
acquisition remains unverified. See the [ledger](docs/model_deviations.md).

## Credits and license

SOLWEIG originates with Fredrik Lindberg, Björn Holmer and Sofia Thorsson,
[Lindberg et al. (2008)](https://doi.org/10.1007/s00484-008-0162-7), and
[UMEP](https://github.com/UMEP-dev/UMEP). This implementation derives directly
from [nvnsudharsan/SOLWEIG-GPU](https://github.com/nvnsudharsan/SOLWEIG-GPU).
GPL-3.0-or-later; see [LICENSE](LICENSE). Original source notices and the
vendored [SLEEF Boost license](src/solweig_light/radiation/SLEEF_LICENSE.txt)
are retained.
