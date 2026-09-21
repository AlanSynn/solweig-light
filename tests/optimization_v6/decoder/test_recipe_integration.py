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
import numpy as np
import pytest

from conftest import retained_route

import solweig_light.radiation.patch_radiation as patch_radiation
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
    """Emulate the recipe's single prepared call behind the three-name demand.

    The integrator replaces the generator expression with one prepared decode;
    the shim feeds the three names from one prepared result through the same
    call order, so define_patch_characteristics runs unchanged otherwise.
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
        stash = {}
        original_block = patch_radiation._block

        def recipe_block(channel, start, stop, count):
            for index, name in enumerate(demand_names):
                if channel is arguments[name] and name not in stash:
                    prepared = decode_longwave_block(arguments['shmat'], arguments['vegshmat'],
                                                     arguments['vbshvegshmat'], start, stop, count)
                    if prepared is None:
                        break
                    stash.update(zip(demand_names, prepared))
                    return stash[name]
            return original_block(channel, start, stop, count)

        monkeypatch.setattr(patch_radiation, '_block', recipe_block)
        try:
            candidate = patch_radiation.define_patch_characteristics(**arguments)
        finally:
            monkeypatch.undo()
    assert_fields_bitwise(baseline, candidate)
    assert set(stash) == set(demand_names)  # the prepared call actually served the demand
