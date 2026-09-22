# Main block-size default (N8-01 gate evidence)

**The actual main default block size is 128 pixels.** It is defined in main
pin `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`, and the branch carries the
identical value at identical lines:

| Definition site | Main | Branch | Form |
|---|---|---|---|
| `RuntimeOptions.block_pixels` field default | `src/solweig_light/runtime.py:325` | `src/solweig_light/runtime.py:325` | `block_pixels: int = 128` |
| `estimate_memory(...)` parameter default | `src/solweig_light/runtime.py:462` | `src/solweig_light/runtime.py:462` | `block_pixels: int = 128` |
| `estimate_tile_memory(...)` parameter default | `src/solweig_light/runtime.py:510` | `src/solweig_light/runtime.py:510` | `block_pixels: int = 128` |
| Admission usage (only consumer of the option) | `src/solweig_light/runtime.py:563` | `src/solweig_light/runtime.py:563` | `options.block_pixels` |

Context:

- `RuntimeOptions` is a frozen dataclass; the process-wide default instance
  is created at module import (`_DEFAULT_OPTIONS = RuntimeOptions()`,
  `runtime.py:386`) and returned by `get_runtime_options()`. Every public
  workflow resolves its runtime through `get_runtime_options()`, so 128 is
  the effective main default for ordinary calls; there is no CLI flag or
  environment variable that can change it (users override only by
  constructing `RuntimeOptions(block_pixels=...)` and entering
  `runtime_options(...)`, which the DX contract keeps stable).
- `__post_init__` validates `block_pixels` as a positive integer
  (`runtime.py:344-351`).
- `estimate_memory`/`estimate_tile_memory` restate 128 as an independent
  keyword default used for admission accounting (decoded-block term,
  `runtime.py:487`).
- The DX_CONTRACT "one large block" performance lever therefore starts from
  128, not 1024: the README's "four-thread, 1,024-pixel-block" line refers
  to a past inherited optimization matrix that was **explicitly tuned**, not
  to the shipped default.

Captured programmatically in `main_surface.json` /
`branch_surface.json` (key `package.runtime_options.fields.block_pixels` =
`128`) and asserted at runtime by
`tests/optimization_v8/dx/test_dx_surface.py::test_block_pixels_default_is_frozen`.
