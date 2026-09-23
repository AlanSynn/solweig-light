#!/usr/bin/env python3
#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-13 build driver: compile lw_primary_aosoa.ispc THROUGH N8-20's driver.

The actual build is a subprocess invocation of
experiments/optimization_v8/packaging/build_native.py (``build`` subcommand)
with the B7 contract flags it preloads (--target neon-i32x8, -O2
--opt=disable-fma --math-lib=default --pic) and the pinned ISPC series
(1.31.0). Everything this wrapper adds is N8-13 evidence:

* the generation is published immutably under THIS module's own staging
  (experiments/optimization_v8/native/stage), never N8-20's stage/;
* the packet gate "ISA target and generated FP operations audited" is
  recorded as a JSON audit bound to the SHIPPED assembly in the published
  generation:
    - FMA mnemonic scan (build_native.fma_audit re-run on the shipped .s;
      the build itself already hard-fails on any hit),
    - true-division audit: the reflection's ``fdiv`` must be present and
      no approximate-reciprocal mnemonic (vrecpe/vrecps/vrsqrte/vrsqrts)
      may appear -- a Newton-Raphson reciprocal would change the typed
      graph exactly like a contraction would,
    - ISA/target facts from the verified manifest (target string, arch,
      cpu-feature requirements, math profile);
* build stdout/stderr and ambient loadavg are archived next to the audit
  (numbers never live only in the terminal).

Exit codes: 0 ok (built or already-published generation reused), 3 ispc
unavailable, 4 build failure, 6 verification failure.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent
_KERNEL = _MODULE_DIR / 'lw_primary_aosoa.ispc'
_STAGING = _MODULE_DIR / 'stage'
_EVIDENCE = _MODULE_DIR / 'evidence'
_BUILD_NATIVE = _MODULE_DIR.parent / 'packaging' / 'build_native.py'

ISPC_PIN = '1.31.0'
TARGET = 'neon-i32x8'
ARTIFACT = 'liblw_native_g8.dylib'
# N8-20's driver constraint: its post-build self-verify (verify_generation)
# re-derives the name with the DEFAULT "lw" prefix, so any other
# --gen-prefix fails its own gate. The AoSoA generation therefore keeps the
# lw prefix and is distinguished by living in THIS module's staging dir and
# by its content-derived fingerprint (the kernel sha256 differs).
GEN_PREFIX = 'lw'
# Approximate-reciprocal mnemonics: any hit means a division/sqrt was
# rewritten as an estimate+refine sequence, which is NOT the frozen graph.
_RECIPROCAL_MNEMONICS = ('vrecpe', 'vrecps', 'vrsqrte', 'vrsqrts')
_RECIP_RE = re.compile(r'(?<![A-Za-z0-9_])(?:%s)' % '|'.join(_RECIPROCAL_MNEMONICS))
_FDIV_RE = re.compile(r'(?<![A-Za-z0-9_])fdiv')


def _find_ispc(explicit):
    if explicit:
        return explicit
    for candidate in (shutil.which('ispc'), '/opt/homebrew/bin/ispc'):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _loadavg():
    try:
        return os.getloadavg()
    except OSError:
        return None


def _existing_generation() -> Path | None:
    if not _STAGING.is_dir():
        return None
    candidates = sorted(p for p in _STAGING.iterdir()
                        if p.is_dir() and p.name.startswith('lw-g8-'))
    return candidates[-1] if candidates else None


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ispc = _find_ispc(argv[0] if argv else None)

    reuse = _existing_generation()
    if reuse is not None and not argv:
        gen_dir, build_stdout, rc = reuse, '(reused already-published generation)', 0
    else:
        if ispc is None:
            print('BUILD FAILED: ispc not found (pass a path or put it on PATH)',
                  file=sys.stderr)
            return 3
        cmd = [sys.executable, str(_BUILD_NATIVE), 'build',
               '--kernel', str(_KERNEL), '--staging', str(_STAGING),
               '--gen-prefix', GEN_PREFIX, '--artifact', ARTIFACT,
               '--target', TARGET, '--ispc', ispc, '--ispc-version', ISPC_PIN]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        build_stdout = (proc.stdout + proc.stderr).strip()
        if proc.returncode == 0:
            gen_dir = Path(json.loads(proc.stdout)['generation_dir'])
        elif proc.returncode == 7 and _existing_generation():
            # Same content -> same immutable generation name: idempotent reuse.
            gen_dir = _existing_generation()
        else:
            print(f'BUILD FAILED (rc={proc.returncode}):\n{build_stdout}',
                  file=sys.stderr)
            return 4 if proc.returncode != 6 else 6

    # ---- audit + evidence, bound to the shipped generation -------------
    sys.path.insert(0, str(_BUILD_NATIVE.parent))
    from build_native import fma_audit, verify_generation

    manifest = verify_generation(gen_dir)
    asm_name = next(e['path'] for e in manifest['generated_sources']
                    if e['path'].endswith('.s'))
    asm_path = gen_dir / asm_name
    asm_text = asm_path.read_text(errors='replace')
    fma = fma_audit(asm_text)
    recip_hits = [f'{m.group(0)}@line{i}'
                  for i, line in enumerate(asm_text.splitlines(), start=1)
                  for m in _RECIP_RE.finditer(line)]
    fdiv_count = sum(len(_FDIV_RE.findall(line))
                     for line in asm_text.splitlines())

    audit = {
        'recorded_utc': datetime.now(timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'generation': manifest['generation'],
        'generation_dir': str(gen_dir),
        'kernel': manifest['kernel'],
        'isa_target': manifest['build']['target'],
        'arch': manifest['platform'].get('arch'),
        'cpu_features': manifest['platform'].get('requirements'),
        'ispc': manifest['toolchain']['ispc'],
        'math_profile': manifest['math_profile'],
        'ispc_flags': manifest['build']['ispc_flags'],
        'fma_audit': {'passed': fma.passed,
                      'match_count': len(fma.matches),
                      'mnemonics_scanned': fma.to_manifest('')['mnemonics'],
                      'asm_sha256': manifest['fma_audit']['asm_sha256']},
        'reciprocal_audit': {'passed': not recip_hits,
                             'mnemonics_scanned': list(_RECIPROCAL_MNEMONICS),
                             'hits': recip_hits},
        'true_division_audit': {
            'passed': fdiv_count > 0,
            'fdiv_mnemonic_count': fdiv_count,
            'note': ('reflection divides by the stored float32 pi; a '
                     'reciprocal-multiply rewrite is forbidden (pinned by '
                     'tests) so fdiv must appear and vrecpe*/vrsqrte* must '
                     'not')},
        'ambient_loadavg_at_audit': _loadavg(),
    }
    ok = (fma.passed and not recip_hits and fdiv_count > 0
          and manifest['build']['target'] == TARGET)
    audit['passed'] = ok

    _EVIDENCE.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (_EVIDENCE / f'build_stdout_{stamp}.txt').write_text(build_stdout + '\n')
    audit_path = _EVIDENCE / f'build_audit_{manifest["generation"]}.json'
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n')

    print(json.dumps({'generation': manifest['generation'],
                      'generation_dir': str(gen_dir),
                      'audit_passed': ok,
                      'fma_matches': len(fma.matches),
                      'reciprocal_hits': recip_hits,
                      'fdiv_count': fdiv_count,
                      'audit_path': str(audit_path)}, indent=2))
    return 0 if ok else 6


if __name__ == '__main__':
    sys.exit(main())
