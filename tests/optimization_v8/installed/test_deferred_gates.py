"""N8-23: gates that CANNOT be tested yet, recorded as labelled skips.

These skips are the honest record of this packet's boundary.  The branch
now carries the N8-41 candidate-wheel MACHINERY (staged generation,
vendored ``_native_dispatch`` package), but no qualified native artifact
exists: the N8-32 selection (``numba_improvement_only_native_goal_open``,
``evidence/selection/n8_32_selection_record.json``) left native promotion
incomplete, the shipped qualification registry is empty, and these
channels gate a native default that was never authorized.  None of these
may be faked as passes (DX_CONTRACT.md gate discipline;
PACKAGING_AND_DISTRIBUTION.md 'local install tests, not just wheel
existence').

The no-env gates in test_installed_noenv_gates.py are origin-parametrized
(``SOLWEIG_DX_PACKAGE_ORIGIN=subprocess:<python>`` capture, fresh-venv
fixtures) so they rerun unchanged against a native wheel's venv if a
future, newly-evidenced campaign reopens promotion (see the selection
record's flip conditions).
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason=(
    "[native-wheel-deferred-N8-41] no packaged native artifact exists on this "
    "branch yet; wheel-channel gates (platform tags, manifest packaging, "
    "qualified-host native execution >0, no-SIGILL on unqualified hosts) "
    "require the N8-41 native wheel"))
def test_native_wheel_install_channel():
    """Platform-wheel channel: install once with ordinary pip, automatic
    native selection, actual native work counted.  Deferred to N8-41."""


@pytest.mark.skip(reason=(
    "[companion-collision-deferred-N8-41] the opt-in solweig-light-compat "
    "distribution is not part of this packet; the companion install channel "
    "and legacy thermal_comfort executable coexistence need N8-41"))
def test_companion_install_coexistence():
    """Install main + companion together; legacy solweig_gpu imports and
    thermal_comfort executable must keep working.  Deferred to N8-41."""


@pytest.mark.skip(reason=(
    "[upstream-collision-deferred-N8-42] upstream collision testing needs the "
    "installed candidate AND the upstream package present in one environment, "
    "which is the N8-42 integration scope"))
def test_upstream_import_collision():
    """No silently colliding solweig_gpu files between the candidate wheel and
    an upstream install in the same environment.  Deferred to N8-42."""


@pytest.mark.skip(reason=(
    "[native-qualification-deferred-N8-42] wrong-arch/corrupt/ABI-mismatch "
    "binary handling and native coverage evidence need the N8-41 artifact; "
    "auto-decline-to-Numba on this no-native install is already exercised by "
    "the no-env gates in test_installed_noenv_gates.py"))
def test_native_artifact_adversarial_channels():
    """Missing/corrupt/wrong-arch binary, stale certificate, unsupported CPU:
    default never executes incompatible instructions, explicit native request
    is distinguishable.  Deferred to N8-42."""
