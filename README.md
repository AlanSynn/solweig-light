# SOLWEIG-light

A CPU-native SOLWEIG implementation for urban thermal comfort — mean radiant
temperature (Tmrt), UTCI and sky view factor — built on NumPy, SciPy and
Numba. No GPU, no Torch, no CUDA. Same workflow and API shape as the
SOLWEIG-GPU era: point it at a scene folder and a date, and it runs.

The compatibility baseline is SOLWEIG-GPU commit
`0d7fe742abeeddd890dd58fc76ed7f78bd47faec`. This is a correctness-first
implementation under numerical verification, not a completed release.

## Quick start

Prepare a scene folder with the three input rasters and a meteorological
file (UMEP-format text):

```
scene/
├── Building_DSM.tif
├── DEM.tif
└── Trees.tif
└── met.txt
```

Install (Python ≥ 3.11; exercised on macOS ARM64 with native GDAL 3.13.3 —
install GDAL before its Python bindings, and use an environment separate from
upstream SOLWEIG-GPU):

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements/macos-arm64-py311.txt
.venv/bin/python -m pip install .
```

Run it — Python:

```python
from solweig_light import thermal_comfort

thermal_comfort(
    base_path="/absolute/path/to/scene",
    selected_date_str="2020-07-18",
    own_met_file="/absolute/path/to/scene/met.txt",
    ERA_5_z0_find=False,
)
```

or the command line:

```sh
solweig-light --base_path /absolute/path/to/scene \
              --date 2020-07-18 \
              --own_metfile /absolute/path/to/scene/met.txt
```

That is the whole setup. There is nothing to tune: logical tiling, thread
use and the compiled kernel routes are chosen by pinned defaults. Per-tile
outputs (Tmrt by default; SVF, Kdown/Kup, Ldown/Lup, shadow, WBGT, Ta and
wind fields opt-in via `save_*` flags) are written under
`<base_path>/output_folder/<tile>/` as GeoTIFFs, streamed band by band.

`landcover` is optional; explicit relative meteorological filenames resolve
against the working directory, as upstream. ERA5-based roughness/wind
generation (`ERA_5_z0_find=True`, the default) additionally requires the ERA5
forcing data described in [optional environment](docs/optional_environment.md).

## Upstream usage guides apply

The workflow, scene layout, meteorological file format and parameter
semantics mirror upstream SOLWEIG-GPU, so its documentation and tutorials
apply directly to `solweig_light`:

- SOLWEIG-GPU documentation: <https://solweig-gpu.readthedocs.io>
- SOLWEIG-GPU repository: <https://github.com/nvnsudharsan/solweig-gpu>
- UMEP (met-file format and SOLWEIG model background):
  <https://github.com/UMEP-dev/UMEP>
- Papers: [SOLWEIG-GPU (JOSS 2026)](https://doi.org/10.21105/joss.09535) ·
  [GLIDE-SOL (GMD 2026)](https://doi.org/10.5194/gmd-19-7389-2026) ·
  [original SOLWEIG (Lindberg et al. 2008)](https://doi.org/10.1007/s00484-008-0162-7)

Where this implementation behaves differently from upstream, the difference
is recorded, not silent: see [model deviations](docs/model_deviations.md).
For running under the legacy `solweig_gpu` import names, see
[compatibility](docs/compatibility.md).

## Options

`thermal_comfort` mirrors the upstream public interface. The commonly used
parameters:

| parameter | default | meaning |
|---|---|---|
| `base_path` | required | scene folder containing the input rasters |
| `selected_date_str` | required | date to model, `YYYY-MM-DD` |
| `building_dsm_filename` / `dem_filename` / `trees_filename` | `Building_DSM.tif` / `DEM.tif` / `Trees.tif` | input raster names |
| `landcover_filename` | `None` | optional land cover raster |
| `own_met_file` | `None` | UMEP-format meteorological file |
| `ERA_5_z0_find` | `True` | ERA5 roughness lookup for wind generation |
| `tile_size` / `overlap` | `3600` / `20` | logical tiling of large scenes |
| `start_time` / `end_time` | `None` | restrict the modeled time window (UTC) |
| `use_uhi` | `True` | UHI handling from the met file |
| `save_tmrt` … `save_wind` | `False` (`save_tmrt=True`) | which fields to write |

Input construction helpers (`build_inputs`, `build_wind_ext_coeff`) and the
standalone SVF entry points (`run_walls_aspect`, `calculate_svf`,
`run_utci_tiles`) are importable from `solweig_light` as well.

Legacy `solweig_gpu` imports are supplied separately by the opt-in companion
distribution; see [compatibility](docs/compatibility.md).

## Expert options

Everything above needs zero configuration. The one opt-in backend switch:
the cylinder-longwave primary reduction can run on an exact ISPC backend
(bitwise-identical outputs, ~3.5x faster at the kernel boundary
single-threaded, ~1.5x on whole small-scene records) — off by default; set
`SOLWEIG_LIGHT_LW_BACKEND=native` to enable. Inputs outside its reviewed
admission domain fall back to the Numba kernel before launch; the shared
library is built on demand into `~/.cache/solweig-light/native` (override
with `SOLWEIG_LIGHT_NATIVE_CACHE`); a missing ISPC toolchain fails loudly
rather than silently falling back. Evidence:
`development/optimization_v7_backends/evidence/`.

## Documentation

| document | contents |
|---|---|
| [numerical contract](docs/numerical_contract.md) | what bit-exactness and tolerance claims mean here |
| [model deviations](docs/model_deviations.md) | documented deviations from upstream physics |
| [compatibility](docs/compatibility.md) | SOLWEIG-GPU compatibility surface, companion distribution |
| [runtime](docs/runtime.md), [cache policy](docs/cache_policy.md) | tiling/threads behavior, cache and restart semantics |
| [optional environment](docs/optional_environment.md) | ERA5/WRF/forcing extras |
| [provenance](docs/provenance.md) | behavioral reference, evidence storage rules |
| [history](development/HISTORY.md) | the consolidated sequential record: port, exactness contract, every campaign, evidence map |

## How this was developed

The full history is consolidated in
**[development/HISTORY.md](development/HISTORY.md)** — the port (P0–P8), the
exactness contract, the v4–N9 campaign line, the S10/S11 campaigns and the
terminal state, with commit anchors and the evidence map. The per-campaign
process documents and packets were archived at the 2026-10-17 closure
(Dropbox `repo_closure_20261017/` and `campaign_s11/repo_cleanup_20261016/`;
deleted trees are also recoverable from git history). The gate tests each
campaign shipped remain under `tests/optimization_v5/` …
`tests/optimization_v8/` and `tests/optimization_s10/`.

## Verification

```sh
.venv/bin/python -m pytest tests/differential/test_pipeline_reference.py -q
```

Executes real raw/prepared TIFF cases, checks every output band against
original upstream CPU artifacts, and requires Torch to be absent. Broader
source-inspection tests additionally require the exact upstream checkout
under `.upstream/SOLWEIG-GPU`; no upstream package is imported into the
candidate runtime.

## Status

Development is **closed** (2026-10-17). The port gates passed independent
review (P6: 3,029 core, 78 optional, 34 forcing-only installed tests, no
skips). The optimization campaigns (v4–N9, S10, S11) are terminal and merged
to main at `cba707db`: on the 24×1024² synthetic-corpus chain (24 steps,
24-CPU node), the end-to-end wall time went from **6840.4 s** (pre-campaign
main) to **1483.9 s** = **4.61×**, with TMRT outputs **bitwise identical**
to the corpus goldens; serial→parallel at the same shape is 7.24×. All
measurements are on the synthetic corpus (`actual_target_status` unverified)
and one node class; see `development/HISTORY.md` for the verified numbers,
rejected directions, and standing caveats. Four approved inherited scientific
exceptions remain failed and documented
([model deviations](docs/model_deviations.md)); P8 release qualification was
never completed, and no further campaign is planned.

## Credits and license

SOLWEIG was originally developed by Dr. Fredrik Lindberg's group (Lindberg,
Holmer & Thorsson 2008, *Int J Biometeorol* 52, 697–713) and is part of
[UMEP](https://github.com/UMEP-dev/UMEP). The immediate baseline is
[SOLWEIG-GPU](https://github.com/nvnsudharsan/solweig-gpu) (Kamath,
Sudharsan et al., JOSS 2026; GLIDE-SOL, GMD 2026). GPL-3.0-or-later; see
[LICENSE](LICENSE).
