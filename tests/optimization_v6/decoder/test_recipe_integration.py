"""L1 end-to-end: the integration recipe leaves whole-entry outputs bitwise
unchanged on the real radiation entries.

The recipe (optimization_v6_continue/evidence/decoder/integration_recipe.md)
prepends a prepared attempt to the accepted consumer sequences. Here the
recipe is applied as a test-local shim over the REAL ``Kside_veg_v2022a`` and
``define_patch_characteristics`` entries (retained route, fused OFF), never
by editing integrator-owned sources, and the complete outputs are compared
uint32-exact against the unshimmed entries on identical arguments. Diffuse is
built the production way: identity-shared LazyDiffVisibility over the very
shmat/vegshmat objects passed as channels (pipeline.py builds it once and
reuses the objects).
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path
# Load THIS family's conftest by file path: bare `import conftest` is
# shadowed by sibling families' conftest modules when several test
# directories are collected in one pytest invocation.
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_decoder_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_decoder_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
retained_route = _conftest.retained_route
import numpy as np
import pytest


import solweig_light.radiation.patch_radiation as patch_radiation
import solweig_light.geometry.visibility_prepared as visibility_prepared
from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.geometry.visibility_prepared import decode_longwave_block, decode_shortwave_block


def cube(rng, rows, cols, patches, kinds):
    planes = []
    for patch in range(patches):
        kind = kinds[patch % len(kinds)]
        pixels = rows*cols
        if kind == 'binary':
            plane = rng.integers(0, 2, pixels).astype(np.float32)
        elif kind == 'ternary':
            plane = rng.integers(0, 3, pixels).astype(np.float32)
        else:
            bits = rng.integers(0, 2**32, pixels, dtype=np.uint64).astype(np.uint32)
            bits[0] = 0x40600000
            plane = bits.view(np.float32)
        planes.append(plane.reshape(rows, cols))
    return np.stack(planes, axis=2)


def kside_arguments(rng, rows, cols, patches):
    """Full Kside_veg_v2022a keyword set for the compiled admission profile."""
    lv = rng.random((patches, 3)).astype(np.float32)
    lv[:, 0] = rng.integers(5, 90, patches)
    lv[:, 1] = rng.integers(0, 360, patches)
    return dict(
        radI=np.float64(480.0), radD=np.float64(130.0), radG=np.float64(0.0),
        shadow=rng.integers(0, 2, (rows, cols)).astype(np.float32),
        svfS=.5, svfW=.5, svfN=.5, svfE=.5, svfEveg=.5, svfSveg=.5, svfWveg=.5, svfNveg=.5,
        azimuth=np.float64(123.0), altitude=np.float64(37.0), psi=np.float64(7.0),
        t=np.float64(0.0), albedo=np.float64(.2), F_sh=.8,
        KupE=rng.random((rows, cols)).astype(np.float32),
        KupS=rng.random((rows, cols)).astype(np.float32),
        KupW=rng.random((rows, cols)).astype(np.float32),
        KupN=rng.random((rows, cols)).astype(np.float32),
        cyl=1, lv=lv, anisotropic_diffuse=1,
        rows=rows, cols=cols,
        asvf=rng.random((rows, cols)).astype(np.float32),
    )


def packed_demand(rng, rows, cols, patches):
    shmat = PackedVisibility.from_dense(cube(rng, rows, cols, patches, ('binary', 'ternary')))
    vegshmat = PackedVisibility.from_dense(cube(rng, rows, cols, patches, ('binary',)))
    vbshvegshmat = PackedVisibility.from_dense(cube(rng, rows, cols, patches, ('ternary', 'raw')))
    # Production identity: one LazyDiffVisibility over the exact channel objects.
    diffsh = LazyDiffVisibility(shmat, vegshmat)
    return shmat, vegshmat, vbshvegshmat, diffsh


def bitwise(left, right):
    return np.array_equal(np.asarray(left).view(np.uint32), np.asarray(right).view(np.uint32))


def assert_fields_bitwise(left, right):
    assert len(left) == len(right)
    for index, (one, other) in enumerate(zip(left, right)):
        assert bitwise(one, other), f'field {index} differs'


def test_kside_end_to_end_with_recipe_shim(monkeypatch):
    rng = np.random.default_rng(2022)
    rows = cols = 16
    patches = 5
    arguments = kside_arguments(rng, rows, cols, patches)
    arguments.update(zip(('shmat', 'vegshmat', 'vbshvegshmat', 'diffsh'),
                         packed_demand(rng, rows, cols, patches)))
    with retained_route():
        baseline = patch_radiation.Kside_veg_v2022a(**arguments)

        def recipe(shadow, vegetation, vegetation_building, diffuse, start, stop, count):
            prepared = decode_shortwave_block(shadow, vegetation, vegetation_building,
                                              diffuse, start, stop, count)
            if prepared is not None:
                return prepared
            return patch_radiation._shortwave_visibility_blocks(
                shadow, vegetation, vegetation_building, diffuse, start, stop, count)

        monkeypatch.setattr(patch_radiation, '_shortwave_visibility_blocks', recipe)
        try:
            candidate = patch_radiation.Kside_veg_v2022a(**arguments)
        finally:
            monkeypatch.undo()
    assert_fields_bitwise(baseline, candidate)


def test_kside_end_to_end_raw_modes_with_recipe_shim(monkeypatch):
    rng = np.random.default_rng(2023)
    rows = cols = 16
    patches = 5
    arguments = kside_arguments(rng, rows, cols, patches)
    shmat = PackedVisibility.from_dense(cube(rng, rows, cols, patches, ('raw',)))
    vegshmat = PackedVisibility.from_dense(cube(rng, rows, cols, patches, ('nonfinite',)))
    vbshvegshmat = PackedVisibility.from_dense(cube(rng, rows, cols, patches, ('raw',)))
    arguments.update(shmat=shmat, vegshmat=vegshmat, vbshvegshmat=vbshvegshmat,
                     diffsh=LazyDiffVisibility(shmat, vegshmat))
    with retained_route():
        baseline = patch_radiation.Kside_veg_v2022a(**arguments)

        def recipe(shadow, vegetation, vegetation_building, diffuse, start, stop, count):
            prepared = decode_shortwave_block(shadow, vegetation, vegetation_building,
                                              diffuse, start, stop, count)
            if prepared is not None:
                return prepared
            return patch_radiation._shortwave_visibility_blocks(
                shadow, vegetation, vegetation_building, diffuse, start, stop, count)

        monkeypatch.setattr(patch_radiation, '_shortwave_visibility_blocks', recipe)
        try:
            candidate = patch_radiation.Kside_veg_v2022a(**arguments)
        finally:
            monkeypatch.undo()
    assert_fields_bitwise(baseline, candidate)


def test_longwave_end_to_end_with_recipe_shim(monkeypatch):
    """The wired entry serves the three-name demand from one prepared decode.

    C6-70 integration puts the prepared attempt inside
    define_patch_characteristics' compiled branch, ahead of the _block
    generator: when admitted, _block never runs for the three channels. The
    spy wraps the real decode_longwave_block to prove the wired call site
    actually took the prepared route (called, with the demand channels, and
    admitted) while the outputs stay bitwise against the retained route.
    """
    rng = np.random.default_rng(2024)
    rows = cols = 16
    patches = 5
    shmat, vegshmat, vbshvegshmat, diffsh = packed_demand(rng, rows, cols, patches)
    arguments = dict(
        solar_altitude=np.array(37.0, dtype=np.float32),
        solar_azimuth=np.array(201.0, dtype=np.float32),
        patch_altitude=rng.integers(5, 90, patches).astype(np.float32),
        patch_azimuth=rng.integers(0, 360, patches).astype(np.float32),
        steradian=rng.random(patches).astype(np.float32),
        asvf=rng.random((rows, cols)).astype(np.float32),
        shmat=shmat, vegshmat=vegshmat, vbshvegshmat=vbshvegshmat,
        Lsky_down=rng.random((patches, 3)).astype(np.float32),
        Lsky_side=rng.random((patches, 3)).astype(np.float32),
        Lsky=rng.random((patches, 3)).astype(np.float32),
        Lup=rng.random((rows, cols)).astype(np.float32),
        Ta=np.float32(297.0), Tgwall=np.float32(299.0), ewall=np.float32(.9),
        rows=rows, cols=cols)
    with retained_route():
        # Identical objects for both runs: the entry reads its inputs without
        # mutating them, so one argument set serves baseline and candidate.
        baseline = patch_radiation.define_patch_characteristics(**arguments)

    demand_names = ('shmat', 'vegshmat', 'vbshvegshmat')
    with retained_route():
        calls = []
        real_decode = visibility_prepared.decode_longwave_block

        def spy(shadow, vegetation, vegetation_building, start, stop, count):
            result = real_decode(shadow, vegetation, vegetation_building, start, stop, count)
            calls.append(((shadow, vegetation, vegetation_building), result is not None))
            return result

        monkeypatch.setattr(visibility_prepared, 'decode_longwave_block', spy)
        try:
            candidate = patch_radiation.define_patch_characteristics(**arguments)
        finally:
            monkeypatch.undo()
    assert_fields_bitwise(baseline, candidate)
    # The wired call site actually took the prepared route: at least one
    # admitted decode with exactly the demand channels, in demand order.
    assert calls, 'decode_longwave_block was never reached'
    assert all(admitted for _, admitted in calls)
    served = {name for channels, _ in calls for name, channel
              in zip(demand_names, channels)}
    assert served == set(demand_names), served
    first = calls[0][0]
    assert first[0] is arguments['shmat'] and first[1] is arguments['vegshmat'] \
        and first[2] is arguments['vbshvegshmat']
