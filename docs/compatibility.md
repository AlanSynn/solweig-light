# APIs, integrations and numerical compatibility

## Seven public workflows

The normal package is `solweig-light`, imported as `solweig_light`.
[api.py](../src/solweig_light/api.py) and
[preprocessor.py](../src/solweig_light/preprocessor.py) define argument details.

| Function | Role |
| --- | --- |
| `thermal_comfort(base_path, selected_date_str, ...)` | Full preprocessing-to-output workflow. |
| `preprocess(base_path, selected_date_str, ...)` | Validate/normalize rasters, create logical tiles and per-tile meteorology; returns the preprocessing directory. |
| `build_inputs(lat, lon, ...)` | Build static input rasters through optional acquisition/local adapters; returns their directory. |
| `build_wind_ext_coeff(input_dir, era5_dir, ...)` | Build directional wind-extension coefficient rasters. |
| `run_walls_aspect(preprocess_dir)` | Produce wall heights and aspects for prepared tiles. |
| `calculate_svf(base_path, patch_option=2, overwrite=False)` | Standalone SVF TIFF/ZIP/NPZ exports; `base_path` here is the preprocessing directory. |
| `run_utci_tiles(base_path, preprocess_dir, selected_date_str, ...)` | Execute prepared tiles and stream thermal-comfort outputs. |

For example, the staged equivalent of the local own-met workflow is:

```python
from solweig_light import preprocess, run_walls_aspect, calculate_svf, run_utci_tiles

scene = "/absolute/path/to/scene"
prepared = preprocess(
    base_path=scene,
    selected_date_str="2020-07-18",
    own_met_file=f"{scene}/met.txt",
)
run_walls_aspect(prepared)
calculate_svf(prepared)
run_utci_tiles(scene, prepared, "2020-07-18")
```

Upstream workflow argument names/defaults, tile naming, accepted TIFFs,
masks, timestamps, GeoTIFF metadata and legacy export schemas are retained
within the frozen numerical policy. `export_svf` is an additional keyword-only
option on `thermal_comfort` and `run_utci_tiles`, defaulting to `True`. Setting
it to `False` avoids compatibility export serialization, not geometry or
model computation. `save_svf` requests the separate single-band output only
when no complete legacy SVF artifact set already exists; this upstream
suppression also applies when old exports remain after `export_svf=False`.

The CLI is `solweig-light --help`. Its roughness flag is
`--era5_z0_find`, while the Python argument is `ERA_5_z0_find`. The CLI infers
roughness lookup from whether `--data_folder` is provided unless explicitly
overridden; the Python API default remains `True`. `--start` and `--end`
map to `start_time` and `end_time`. The [upstream input guide](https://github.com/nvnsudharsan/SOLWEIG-GPU/blob/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3/docs/input_data.md)
describes raster and meteorological formats; local differences and limitations
are recorded here and in the [ledger](model_deviations.md).

## Optional integrations

The own-met TIFF core requires no Torch, CUDA, xarray, acquisition clients or
network access. Optional dependencies import lazily:

| Install from repository root | Scope |
| --- | --- |
| `python -m pip install '.[forcing]'` | Local ERA5/WRF NetCDF-to-meteorology processing. |
| `python -m pip install '.[wind]'` | ERA5 roughness and directional wind coefficients. |
| `python -m pip install '.[inputs]'` | Input raster/vector construction and acquisition adapters. |

`build_inputs` follows the executed upstream entrypoint: it builds static
rasters. Meteorological and wind generation are separate operations despite
the broader upstream docstring. Local transforms are covered by real-file
tests; acquisition tests use explicitly offline responses. They do not
establish authenticated Earth Engine, OSM or other live-service operation.
WRF uses the explicit [timestamp repair](model_deviations.md#wrf-timestamp-repair).
The recorded duplicate-domain/hour shape failure remains unsupported.

Pinned optional environments are in
[requirements/optional-macos-arm64-py311.txt](../requirements/optional-macos-arm64-py311.txt).
The retained environment showed a netCDF4 1.7.4 ndarray-size warning in both
oracle and candidate, while real NetCDF read/write/mask tests passed. That
record is not a general ABI guarantee for replacement native libraries.

## Opt-in legacy namespace

The main distribution does not own `solweig_gpu` or the `thermal_comfort`
executable. Install the matching companion only when those names are needed:

```sh
python -m pip install . ./compat
```

`solweig-light-compat` requires the exact matching main package version and
forwards the seven functions to the same CPU objects. Legacy module imports
and the executable are forwarded too. It does not enable GPU execution.

Keep upstream `solweig-gpu` and `solweig-light-compat` in separate environments:
they own overlapping names/files. The companion rejects detected upstream
distribution metadata before forwarding, but cannot prevent an installer from
overwriting files or diagnose every unmanaged checkout. Use a fresh environment
if owners have collided; uninstalling one can delete the other's files.

## Numerical contract

The authoritative field rules are
[comparison_v1.json](../development/benchmarks/protocols/comparison_v1.json).
Shape, categorical geometry, patch identity/order, control state, masks,
timestamps and schemas require exact agreement. Continuous-field gates include:

| Family | Frozen comparison rule |
| --- | --- |
| SVF | Maximum absolute error `1e-6`. |
| Radiation and radiance-valued delay fields | `atol=0.05 W/m²`, `rtol=1e-5`. |
| TMRT and temperature-valued surface state | Maximum absolute error `0.01 °C`. |
| UTCI and WBGT | Maximum absolute error `0.02 °C`. |

The machine-readable file contains field-specific rules; the table is not a
replacement. Finite/NaN/infinity and sentinel masks are checked before numeric
errors. CRS is compared semantically, transforms/NoData separately. Archive
compression bytes need not match decoded semantic contents. Passing a fixture
budget is not universal bitwise identity or independent physical validation.

### Portable math profile

The runtime uses `solweig-portable-sleef-5a1d179d-v1` in both namespaces.
It preserves source-derived float32 SVF/classifier operations using SLEEF
commit `5a1d179df9cf652951b59010a2d2075372d67f68`, with the original NumPy
ufunc path outside the validated helper domain. Its canonical oracle is
original frozen upstream executed in the retained macOS ARM64 SLEEF/Torch
environment. This is a versioned reference amendment, not a universal
Torch/MKL/CUDA parity claim.

Operation grouping, float32 rounding, explicit single-rounding FMA, strict
`<`/`>` boundaries and `fastmath=False` matter. Solar-coefficient float64
NumPy cos/tan remains a finite validated-domain policy rather than proof of
primitive bit equality for arbitrary inputs. No clipping, epsilon or blanket
boundary adjustment is used. Raw visibility and unsupported optimized
profiles retain characterized fallbacks.

Geometry/checkpoint identities include semantic profile and implementation/
runtime fingerprints. Old derived geometry is regenerated and incompatible
state cannot resume. Two-platform admission evidence and its final fallback
repair limits are summarized in [provenance](provenance.md#validation-boundaries).
Historical original-MKL differences remain recorded in the
[ledger](model_deviations.md#transcendental-and-reference-profile-differences).
