"""Invocation-wide compiled scheduling parity on the frozen stream fixtures."""
import numpy as np
import pytest
from stream_test_helpers import make_case, stream_plan, outputs_bitwise
from test_lw_stream import _run_stream
from solweig_light._native_dispatch import lw_batch


@pytest.mark.parametrize('surface_dtype',[np.float32,np.float64])
@pytest.mark.parametrize('rows,patches,capacity', [(8,5,128),(33,5,128),(37,153,16),(131,153,128),(300,9,16)])
@pytest.mark.parametrize('modes_cycle', [('binary','ternary','raw'), ('binary','ternary'), ('binary',)])
@pytest.mark.parametrize('width', [4, 8])
def test_compiled_batch_matches_retained_stream(rows, patches, capacity, surface_dtype, modes_cycle, width):
    case = make_case(rows, patches, seed=rows*31+patches, modes_cycle=modes_cycle)
    case['sun_surface']=surface_dtype(1+2**-25)
    case['shade_surface']=surface_dtype(1+2**-25)
    expected, _, _ = _run_stream(case, rows, capacity)
    plan = stream_plan(case, rows, row='B', block_pixels=capacity, width=width)
    try:
        assert lw_batch._lanes_admitted(plan) == (
            'raw' not in modes_cycle and rows >= capacity and capacity % 32 == 0)
        for parallel in (False, True):
            actual = lw_batch.execute(plan, parallel=parallel)
            assert actual.shape == (7, rows)
            assert outputs_bitwise(actual, expected)
    finally:
        plan.close()


def test_lane_batch_preserves_signed_zero_and_finite_extremes():
    for dtype in (np.float32, np.float64):
        for sun, shade in ((-0., -np.finfo(dtype).smallest_subnormal),
                           (-9e19, 9e19), (-1.25, np.finfo(dtype).max)):
            case = make_case(37, 5, seed=91, modes_cycle=('binary', 'ternary'))
            case['sun_surface'], case['shade_surface'] = dtype(sun), dtype(shade)
            expected, _, _ = _run_stream(case, 37, 32)
            plan = stream_plan(case, 37, row='B', block_pixels=32)
            try:
                assert lw_batch._lanes_admitted(plan) == (abs(shade) <= 1e20)
                for parallel in (False, True):
                    assert outputs_bitwise(lw_batch.execute(plan, parallel=parallel), expected)
            finally:
                plan.close()


@pytest.mark.parametrize('field,value', [('Lsky_down', np.nan), ('Lsky_side', np.inf),
    ('Lup', -np.inf), ('steradian', np.inf), ('sun_surface', 2e20),
    ('shade_surface', np.nan), ('factor', 2.)])
def test_exceptional_radiance_keeps_exact_batch_fallback(field, value):
    case = make_case(37, 5, seed=17, modes_cycle=('binary', 'ternary'))
    if field in case['values']:
        case['values'][field].reshape(-1)[2 if field.startswith('Lsky') else 0] = value
    else:
        case[field] = np.float32(value)
    expected, _, _ = _run_stream(case, 37, 32)
    plan = stream_plan(case, 37, row='B', block_pixels=32)
    try:
        assert not lw_batch._lanes_admitted(plan)
        for parallel in (False, True):
            assert outputs_bitwise(lw_batch.execute(plan, parallel=parallel), expected)
    finally:
        plan.close()


@pytest.mark.parametrize('channel', ['shmat', 'vegshmat', 'vbshvegshmat'])
def test_batch_reserved_code_rejected_before_parallel_launch(channel, monkeypatch):
    from stream_test_helpers import build_channel
    rows,patches=131,5
    case=make_case(rows,patches,seed=13,modes_cycle=('binary',))
    codes=np.zeros(rows,np.uint8);codes[130]=3
    case['values'][channel]=build_channel(rows,['ternary']*patches,codes=codes)
    plan=stream_plan(case,rows,block_pixels=128)
    def forbidden(*args):
        raise AssertionError('parallel launch preceded reserved-code validation')
    monkeypatch.setattr(lw_batch,'_batch',forbidden)
    try:
        with pytest.raises(IndexError,match='Reserved visibility code'):
            lw_batch.execute(plan)
    finally:
        plan.close()


def test_binary_preflight_keeps_malformed_descriptors_on_original_path(monkeypatch):
    from solweig_light.geometry.visibility_compiled import _descriptor
    from stream_test_helpers import build_channel
    payloads, modes = _descriptor(build_channel(131, ['binary'] * 2))
    good = (payloads, modes)
    readonly_modes = modes.view()
    readonly_modes.setflags(write=False)
    lw_batch._preflight_blocks(good, (payloads, readonly_modes), good, 131, 128, 2)
    short_bytes = payloads.copy()
    short_bytes[1] = short_bytes[1][:-1]
    scanned = []
    def record(data, modes, start, stop, patches):
        scanned.append((id(data), id(modes), start, stop, patches))
    monkeypatch.setattr(lw_batch, '_preflight_packed', record)
    lw_batch._preflight_blocks.py_func(good, good, good, 131, 128, 2)
    assert not scanned
    for bad in ((payloads[:1], modes), (payloads, modes[:1]),
                (short_bytes, modes),
                *((payloads, np.array([1, mode], np.uint8)) for mode in (2, 3, 4))):
        scanned.clear()
        lw_batch._preflight_blocks.py_func(good, bad, good, 131, 128, 2)
        assert scanned == [(id(data), id(mode), start, stop, 2)
                           for start, stop in ((0, 128), (128, 131))
                           for data, mode in (good, bad, good)]
    with pytest.raises(ValueError):
        lw_batch._preflight_blocks.py_func(good, good, good, 0, 0, 2)


@pytest.mark.parametrize('dtype', [np.float32, np.float64])
@pytest.mark.parametrize('first_parallel', [False, True])
def test_resident_masks_reuse_only_the_owned_scope(dtype, first_parallel):
    from dataclasses import replace
    rows, patches, capacity = 131, 5, 128
    cases = [make_case(rows, patches, seed=seed, modes_cycle=('binary', 'ternary'))
             for seed in (17, 29)]
    for case in cases:
        case['sun_surface'] = case['shade_surface'] = dtype(1 + 2**-25)
    plans = [stream_plan(case, rows, block_pixels=capacity) for case in cases]
    owners = [tuple(case['values'][key] for key in ('shmat', 'vegshmat', 'vbshvegshmat'))
              for case in cases]
    try:
        expected = [lw_batch.execute(plan, parallel=False) for plan in plans]
        assert not outputs_bitwise(*expected)
        with lw_batch._resident_masks_scope(owners[0]) as outer:
            assert outer.flags is None
            assert outputs_bitwise(lw_batch.execute(plans[0], parallel=first_parallel), expected[0])
            cached = outer.flags
            assert cached.shape == (5, patches, 32) and cached.nbytes == 160 * patches
            assert not cached.flags.writeable
            assert outputs_bitwise(lw_batch.execute(plans[0], parallel=not first_parallel), expected[0])
            assert outer.flags is cached
            assert lw_batch._resident_masks_for(plans[1], False) is None
            assert lw_batch._resident_masks_for(replace(plans[0], total=rows-1), False) is None
            assert outputs_bitwise(lw_batch.execute(plans[1], parallel=False), expected[1])
            assert outer.flags is cached
            with lw_batch._resident_masks_scope() as disabled:
                assert disabled is None
                assert lw_batch._resident_masks_for(plans[0], False) is None
                assert outputs_bitwise(lw_batch.execute(plans[0], parallel=False), expected[0])
            with pytest.raises(RuntimeError, match='scope failure'):
                with lw_batch._resident_masks_scope(owners[1]) as inner:
                    assert outputs_bitwise(lw_batch.execute(plans[1], parallel=False), expected[1])
                    assert inner.flags is not None and inner.flags is not cached
                    raise RuntimeError('scope failure')
            assert inner.flags is None and inner.descriptors is None and inner.owners == ()
            assert lw_batch._resident_masks_for(plans[0], False) is cached
        assert outer.flags is None and outer.descriptors is None and outer.owners == ()
        assert lw_batch._resident_masks_for(plans[0], False) is None
    finally:
        for plan in plans:
            plan.close()


@pytest.mark.parametrize('exception', ['raw', 'radiance'])
def test_resident_masks_keep_noneligible_calls_on_the_strict_path(exception):
    modes = ('binary', 'ternary', 'raw') if exception == 'raw' else ('binary', 'ternary')
    case = make_case(37, 5, seed=51, modes_cycle=modes)
    if exception == 'radiance':
        case['shade_surface'] = np.float32(np.inf)
    expected, _, _ = _run_stream(case, 37, 32)
    plan = stream_plan(case, 37, block_pixels=32)
    owners = tuple(case['values'][key] for key in ('shmat', 'vegshmat', 'vbshvegshmat'))
    try:
        assert not lw_batch._lanes_admitted(plan)
        with lw_batch._resident_masks_scope(owners) as state:
            for parallel in (False, True):
                assert outputs_bitwise(lw_batch.execute(plan, parallel=parallel), expected)
            assert state.flags is None
    finally:
        plan.close()


def test_resident_masks_do_not_bypass_mapped_owner_leases(tmp_path):
    from solweig_light.geometry.visibility_native import open_native_visibility, save_native_visibility
    case = make_case(131, 5, seed=59, modes_cycle=('binary', 'ternary'))
    manifest = tmp_path / 'visibility' / 'manifest.json'
    save_native_visibility(manifest, case['values']['shmat'])
    with open_native_visibility(manifest) as mapped:
        owners = (mapped, mapped, mapped)
        for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
            case['values'][key] = mapped
        with lw_batch._resident_masks_scope(owners) as state:
            plan = stream_plan(case, 131, block_pixels=128)
            try:
                with lw_batch._resident_masks_scope():
                    expected = lw_batch.execute(plan, parallel=False)
                actual = lw_batch.execute(plan, parallel=False)
                assert state.flags is not None and outputs_bitwise(actual, expected)
            finally:
                plan.close()
            mapped.close()
            with pytest.raises(RuntimeError, match='Native visibility is closed'):
                stream_plan(case, 131, block_pixels=128)
        assert state.flags is None and state.descriptors is None and state.owners == ()
