"""Standing E2E route-engagement pin for the landcover golden (wave-1 review).

The wave-1 review demonstrated the census trap by execution: with
SOLWEIG_LIGHT_ANILUM_PACKED=0 the landcover goldens still PASS while only
R03's E2E engagement test fails — T01 (Lcyl/dpc primary) and G01 (prepared
GVF admission) had function-level counter pins but no standing E2E pin on
the production input profile. This test runs one landcover golden tile and
asserts every admitted S10 route actually fires on it:

- T01: Lcyl_v2022a and define_patch_characteristics take the primary on
  every daytime step (14/14 on the July golden date);
- G01: engine.gvf_2018a routes every timestep (24/24) through
  prepared_gvf_step with the serial delegate never used (the production
  f64-Tg / (1,1)-f64-Tgwall profile is admitted, not delegated);
- S10-23: every Lside call lands on an exact non-body path — the seven
  night steps take the C6-20 demanded fast path upstream and the rest are
  admitted by the dispatch twin (primary); the serial reference is never
  used on this profile.  The exact primary/fast-path split depends on the
  ambient np.seterr state (engine.py:333 leaks divide/invalid='ignore'
  after the first daytime step), so the pin asserts total coverage and
  zero fallbacks rather than a fixed split.
"""
import shutil
from pathlib import Path

import numpy as np
import pytest

_SOURCE = Path(__file__).resolve().parents[3] / \
    'tests/reference/optional_original_cpu/landcover/processed_inputs'


@pytest.fixture
def prepared_inputs(tmp_path, monkeypatch):
    """Landcover golden inputs with the bench's GDAL-cap deviation (reverted)."""
    import solweig_light.runtime_memory as runtime_memory
    monkeypatch.setattr(runtime_memory, 'default_gdal_cache_bytes',
                        lambda: 256 * 1024 * 1024)
    prepared = tmp_path / 'processed_inputs'
    shutil.copytree(_SOURCE, prepared)
    return prepared


def test_landcover_golden_routes_engage(prepared_inputs, monkeypatch):
    from solweig_light.radiation import gvf_prepared, patch_radiation
    from solweig_light.pipeline import files_by_key, run_tile

    import solweig_light.radiation.ground_view as ground_view
    counts = {'prepared': 0, 'serial': 0}
    real_prepared, real_serial = gvf_prepared.prepared_gvf_step, ground_view.gvf_2018a

    def counted_prepared(*args, **kwargs):
        counts['prepared'] += 1
        return real_prepared(*args, **kwargs)

    def counted_serial(*args, **kwargs):
        counts['serial'] += 1
        return real_serial(*args, **kwargs)

    monkeypatch.setattr(gvf_prepared, 'prepared_gvf_step', counted_prepared)
    # engine.gvf_2018a resolves its delegate by in-function import.
    monkeypatch.setattr(ground_view, 'gvf_2018a', counted_serial)

    prepared = prepared_inputs
    paths = {n: files_by_key(prepared / n)['0_0'] for n in
             ('Building_DSM', 'Trees', 'DEM', 'walls', 'aspect', 'metfiles', 'Landcover')}
    flags = {f'save_{n}': True for n in ('tmrt', 'kup', 'kdown', 'lup', 'ldown', 'shadow')}

    lcyl_before = patch_radiation.ROUTE_COUNTS['Lcyl_v2022a_primary']
    dpc_before = patch_radiation.ROUTE_COUNTS['define_patch_characteristics_primary']
    lside_primary_before = patch_radiation.ROUTE_COUNTS['Lside_veg_v2022a_primary']
    lside_reference_before = patch_radiation.ROUTE_COUNTS['Lside_veg_v2022a_reference']
    monkeypatch.delenv('SOLWEIG_LIGHT_LSIDE_DISPATCH', raising=False)
    run_tile(prepared.parent, prepared, '2020-07-18', '0_0', paths, flags)
    lcyl_after = patch_radiation.ROUTE_COUNTS['Lcyl_v2022a_primary']
    dpc_after = patch_radiation.ROUTE_COUNTS['define_patch_characteristics_primary']
    lside_primary_after = patch_radiation.ROUTE_COUNTS['Lside_veg_v2022a_primary']
    lside_reference_after = patch_radiation.ROUTE_COUNTS['Lside_veg_v2022a_reference']

    # 24 hourly steps. GVF and its longwave demand run on the 14 daytime
    # steps only; the longwave primaries additionally admit the 10 night
    # steps through the 0-d night Tgwall, so they fire 24/24.
    assert counts['prepared'] == 14, 'G01: prepared GVF must admit every daytime step'
    assert counts['serial'] == 0, 'G01: the exact delegate must stay unused on this profile'
    assert lcyl_after - lcyl_before == 24, 'T01: Lcyl primary on every step incl. night'
    assert dpc_after - dpc_before == 24, 'T01: dpc primary on every step incl. night'
    # S10-23: all 24 Lside calls take an exact non-body route (demanded fast
    # path upstream or the certified dispatch twin); the serial reference
    # must never fire on the production profile.
    lside_primary = lside_primary_after - lside_primary_before
    lside_reference = lside_reference_after - lside_reference_before
    assert lside_primary + lside_reference == 24, \
        'S10-23: every Lside call must be accounted by the dispatch counters'
    assert lside_reference == 0, \
        'S10-23: the serial reference must stay unused on the production profile'
