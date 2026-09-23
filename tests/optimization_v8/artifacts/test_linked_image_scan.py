#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
"""N8-21 maintainer-side linked-image FMA scan (N8-20 review note N2).

Disposition of the note: the scan of the FINAL linked artifact is
VALUABLE but does not belong on the runtime load path --

* BUILD_DESIGN section 8.2: the packaged loader runs "no runtime
  compiler or subprocess tool of any kind" (the loader suite proves zero
  subprocess);
* /usr/bin/otool is an xcrun shim: on a clean macOS install without
  Command Line Tools the scan cannot run, which would convert an
  ordinary supported host into a declined one;
* decisive: the dylib is sha256-pinned by the manifest, so ANY
  post-publication mutation of the linked image already fails the
  loader's content gate.  A linked-image FMA scan therefore adds real
  coverage exactly ONCE, on the machine where the artifact was produced
  -- at build/verify time (build_native.py, N8-20's scope, where otool
  is already a hard requirement for macho_facts).

These tests keep the maintainer-side evidence fresh: the staged
generation's final linked image is re-scanned through the SAME reviewed
regex (build_native.fma_audit) whenever the fixture is present, and the
regex's sensitivity is pinned synthetically so a 0-hit result can never
be vacuous.  The one-time record for the current generation lives in
experiments/optimization_v8/artifacts/linked_image_fma_scan.json.

Skip labels (never fake-pass):
  [no-staged-artifact] -- staged proof generation absent
  [otool-unavailable]  -- maintainer host cannot run otool
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import build_native
from solweig_light._native_dispatch import installed_loader  # noqa: F401  (conftest bootstrap ordering)

STAGE_DIR = (Path(__file__).resolve().parents[3] / 'experiments'
             / 'optimization_v8' / 'packaging' / 'stage')


def _staged_dylib() -> Path:
    dylibs = sorted(STAGE_DIR.glob('*/liblw_native_g8.dylib'))
    if not dylibs:
        pytest.skip('[no-staged-artifact] staged proof generation missing')
    return dylibs[-1]


@pytest.mark.skipif(shutil.which('otool') is None,
                    reason='[otool-unavailable] otool not on PATH')
def test_staged_linked_image_is_fma_free():
    """otool -tV of the FINAL linked dylib through the reviewed B7 regex:
    the .s re-emission audit and the linked image must agree."""
    dylib = _staged_dylib()
    dis = subprocess.run(['otool', '-tV', str(dylib)],
                         capture_output=True, text=True)
    assert dis.returncode == 0, dis.stderr[:400]
    audit = build_native.fma_audit(dis.stdout)
    instruction_lines = sum(
        1 for line in dis.stdout.splitlines()
        if line.split() and line.split()[0].rstrip(':').isalnum()
        and not line.startswith('('))
    assert instruction_lines > 1000, (  # non-vacuous: the scan saw code
        f'otool produced only {instruction_lines} instruction lines')
    assert audit.passed, f'linked image contains contraction: ' \
                         f'{audit.matches[:5]}'


def test_fma_audit_regex_flags_real_mnemonics():
    """Sensitivity pin: the reviewed regex flags each B7 mnemonic when it
    appears as a disassembly mnemonic, and does not flag substrings --
    a 0-hit linked-image scan means 'no FMA', never 'blind regex'."""
    assert build_native.fma_audit('').passed
    for mnemonic in build_native.FMA_MNEMONICS:
        line = f'    1000:\t{mnemonic} s0, s1, s2, s3'
        audit = build_native.fma_audit(line)
        assert not audit.passed, mnemonic
        assert audit.matches[0]['mnemonic'] == mnemonic
    # identifier substrings must not trip it (the lookbehind guard)
    assert build_native.fma_audit('    _my_fmadd_wrapper:\n').passed
