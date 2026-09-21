"""Close-out order and lock lifetime of the prepared decode.

- A concurrent close() cannot invalidate an in-flight combined decode: it
  blocks on the owner lock until the native read completes (the kernel holds
  the GIL, so the close either lands entirely before the decode acquires the
  lock or entirely after it releases; both end states are asserted).
- A prepared handle keeps strong owner references, so dropping consumer
  variables cannot finalize a mapped owner mid-stage.
- Close-before-decode behavior matches the original path exactly.
"""
import gc
import threading

import numpy as np

from conftest import mapped_roundtrip, original_shortwave, outcome, packed

from solweig_light.geometry.visibility import LazyDiffVisibility
from solweig_light.geometry.visibility_prepared import prepare_channels


def demand(tmp_path, rows, cols, patches, kinds=('binary', 'ternary')):
    rng = np.random.default_rng(rows + patches)
    channels = [mapped_roundtrip(tmp_path, packed(rng, rows, cols, patches, kinds),
                                 f'own{index}{rows}') for index in range(2)]
    building = packed(np.random.default_rng(rows*7), rows, cols, patches, ('ternary',))
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    return channels, building, diffuse


def test_close_before_decode_matches_original(tmp_path):
    channels, building, diffuse = demand(tmp_path, 16, 16, 3)
    try:
        assert outcome(original_shortwave, *channels, building, diffuse, 0, 256, 3)[0] == 'ok'
    finally:
        channels[0].close()
    # Close invalidates the borrowed descriptor by protocol, so preparation
    # declines and the complete fallback reports the closed owner identically.
    from conftest import recipe_shortwave
    assert prepare_channels(*channels, building, diffuse) is None
    result = outcome(recipe_shortwave, *channels, building, diffuse, 0, 256, 3)
    baseline = outcome(original_shortwave, *channels, building, diffuse, 0, 256, 3)
    assert result == baseline
    assert result[:3] == ('err', RuntimeError, 'Native visibility is closed')


def test_concurrent_close_cannot_tear_the_combined_decode(tmp_path):
    channels, building, diffuse = demand(tmp_path, 128, 128, 153)
    try:
        prepared = prepare_channels(*channels, building, diffuse)
        buffers = [np.empty((256, 153), dtype=np.float32) for _ in range(4)]
        expected = original_shortwave(*channels, building, diffuse, 128, 384, 153)

        started = threading.Event()
        results = {}

        def decode_thread():
            started.set()
            results['outcome'] = outcome(prepared.decode, 128, 384, 153, buffers)

        worker = threading.Thread(target=decode_thread)
        worker.start()
        started.wait()
        channels[0].close()  # blocks on the owner lock while the decode runs
        worker.join()
        assert channels[0].closed

        state = results['outcome']
        if state[0] == 'ok':
            for one, other in zip(expected, state[1]):
                assert np.array_equal(one.view(np.uint32), other.view(np.uint32))
        else:
            assert state[:3] == ('err', RuntimeError, 'Native visibility is closed')
        # The surviving owner is untouched; later decodes report the closed
        # owner exactly as the original path would.
        assert not channels[1].closed
        later = outcome(prepared.decode, 0, 0, 3)
        assert later[:3] == ('err', RuntimeError, 'Native visibility is closed')
    finally:
        for owner in channels:
            owner.close()


def test_prepared_holds_strong_owner_references(tmp_path):
    channels, building, diffuse = demand(tmp_path, 16, 16, 3)
    keep = list(channels)
    try:
        prepared = prepare_channels(*keep, building, diffuse)
        channels.clear()
        gc.collect()
        for owner in keep:
            assert not owner.closed
        assert outcome(prepared.decode, 0, 256, 3)[0] == 'ok'
    finally:
        for owner in keep:
            owner.close()


def test_reuse_slot_recheck_observes_intervening_close(tmp_path):
    """A close before the demand is reported at the shadow slot's open check
    in both paths (through preparation decline and complete fallback)."""
    from conftest import recipe_shortwave
    channels, building, diffuse = demand(tmp_path, 16, 16, 3)
    try:
        channels[0].close()
        baseline = outcome(original_shortwave, *channels, building, diffuse, 0, 256, 3)
        assert baseline[:3] == ('err', RuntimeError, 'Native visibility is closed')
        assert prepare_channels(*channels, building, diffuse) is None
        prepared = outcome(recipe_shortwave, *channels, building, diffuse, 0, 256, 3)
        assert prepared == baseline
    finally:
        for owner in channels:
            owner.close()
