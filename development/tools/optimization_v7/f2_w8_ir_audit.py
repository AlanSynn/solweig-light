"""B7-30 condition F2: direct W=8 IR/asm evidence for numba layout control B.

The candidate's ir_audit.py builds W=4 kernels only; reviewer F2 requires a
direct IR/assembly dump of the W=8 specializations before the B7-31/32
selection freeze. This script imports the immutable candidate module
read-only (no candidate file is modified) and applies the identical audit
(regex set from the candidate's ir_audit.audit_text) to the W=8 dispatcher
in both schedules and both captured surface specializations.

Run in the numba worktree venv:
  .venv-v7/bin/python tools/optimization_v7/f2_w8_ir_audit.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
CAND = Path('/Users/alansynn/Workspace/solweig-v7-numba/experiments/optimization_v7/numba_layout')
OUT = REPO / 'optimization_v7_backends' / 'evidence' / 'reviews' / 'b7_30_numba_b_F2_w8_ir'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CAND))
sys.path.insert(0, str(REPO / 'src'))

import longwave_primary_b as mod_b  # noqa: E402

FAST_RE = re.compile(r'\bf(add|mul|sub|div|cmp)\b[^;\n]*\bfast\b')


def audit_text(ir, asm):
    counts = {
        'llvm_ir_lines': len(ir.splitlines()),
        'contraction_fmuladd_calls': len(re.findall(r'call\b[^;\n]*@llvm\.fmuladd', ir)),
        'explicit_fma_calls': len(re.findall(r'call\b[^;\n]*@llvm\.fma(?:\.|\()', ir)),
        'fastmath_flagged_ops': len(FAST_RE.findall(ir)),
        'vector_fop_instructions': len(re.findall(
            r'\bf(add|mul|sub|div)\s+<\d+ x (?:float|double)>', ir)),
        'vector_f32_fop_instructions': len(re.findall(
            r'\bf(add|mul|sub|div)\s+<\d+ x float>', ir)),
        'vector_f64_fop_instructions': len(re.findall(
            r'\bf(add|mul|sub|div)\s+<\d+ x double>', ir)),
        'vector_iop_instructions': len(re.findall(
            r'\b(add|mul|and|or|icmp)\b[^;\n]*<\d+ x i\d+>', ir)),
        'scalar_fadd_f32': len(re.findall(r'\bfadd\s+float\b', ir)),
        'scalar_fmul_f32': len(re.findall(r'\bfmul\s+float\b', ir)),
        'fdiv_instructions': len(re.findall(r'\bfdiv\b', ir)),
        'select_instructions': len(re.findall(r'\bselect\b', ir)),
        'asm_fmadd': len(re.findall(r'\bfmadd\b', asm)),
        'asm_fmsub': len(re.findall(r'\bfmsub\b', asm)),
        'asm_fmla_vector': len(re.findall(r'\bfmla\b', asm)),
        'asm_fdiv': len(re.findall(r'\bfdiv\b', asm)),
        'asm_vector_loads': len(re.findall(r'\bld1\s*\{', asm)),
        'gate_branch_in_ir': ('icmp eq i8' in ir or 'icmp ne i8' in ir) and 'br i1' in ir,
    }
    return counts


def main():
    rng = np.random.default_rng(20260922)
    B, P = 64, 153
    W = 8
    sh = rng.choice([0.0, 1.0, 2.0], size=(B, P)).astype(np.float32)
    vs = rng.choice([0.0, 1.0, 2.0], size=(B, P)).astype(np.float32)
    vb = rng.choice([0.0, 1.0, 2.0], size=(B, P)).astype(np.float32)
    sun = rng.random((B, P)) < 0.5
    shade = rng.random((B, P)) < 0.5
    solid, sine, cosine = (rng.normal(size=P).astype(np.float32) for _ in range(3))
    sky_t1 = np.zeros((P, 3), np.float32); sky_t1[:, 2] = rng.normal(size=P).astype(np.float32)
    sky_t2 = np.zeros((P, 3), np.float32); sky_t2[:, 2] = rng.normal(size=P).astype(np.float32)
    gate4 = rng.random((P, 4)) < 0.5
    solar_gate = rng.random(P) < 0.5
    lup = rng.normal(size=B).astype(np.float32)
    directions = rng.normal(size=(P, 4)).astype(np.float32)

    sh_p, vs_p, vb_p = (mod_b.pack_block_major(x, W) for x in (sh, vs, vb))
    sun_p, shade_p = mod_b.pack_block_major(sun, W), mod_b.pack_block_major(shade, W)
    lup_p = mod_b._pack_lup(lup, W)

    cand_sha = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (CAND / 'longwave_primary_b.py', CAND / 'ir_audit.py')
    }
    report = {
        'schema': 'b7-30-f2-w8-ir-audit-v1',
        'condition': 'F2 from b7_30_numba_b_review.json: direct W=8 IR/asm dump '
                     'before B7-31/32 selection freeze',
        'candidate_module': str(CAND / 'longwave_primary_b.py'),
        'candidate_sha256': cand_sha,
        'W': W,
        'specializations': {}, 'verdicts': {},
    }
    print(f'{"kernel":<16} {"surf":<5} {"fmuladd":>8} {"fma":>5} {"fast":>5} '
          f'{"vec_f32":>8} {"vec_f64":>8} {"vec_iops":>9} '
          f'{"asm_fmadd":>10} {"asm_fmsub":>10} {"asm_fmla":>9} {"asm_ld1":>8}')
    for tag, parallel in (('B_W8_serial', False), ('B_W8_parallel', True)):
        disp = mod_b.make_longwave_primary_b(W, parallel)
        for surf, s in (('f64', np.float64), ('f32', np.float32)):
            disp(sh_p, vs_p, vb_p, sun_p, shade_p, solid, sine, cosine,
                 solar_gate, sky_t1[:, 2], sky_t2[:, 2], s(0.9), s(0.8),
                 lup_p, np.float32(0.05), B)  # warm: compile this signature
            # pick the signature whose two scalar surface args match this surf
            chosen = None
            for sig in disp.signatures:
                tys = str(getattr(sig, 'args', sig))
                if f'{np.dtype(s).name}, {np.dtype(s).name}' in tys:
                    chosen = sig
                    break
            assert chosen is not None, f'no {surf} signature compiled'
            ir, asm = str(disp.inspect_llvm(chosen)), disp.inspect_asm(chosen)
            name = f'{tag}_{surf}'
            (OUT / f'{name}.ll').write_text(ir)
            (OUT / f'{name}.s').write_text(asm)
            counts = audit_text(ir, asm)
            report['specializations'][name] = counts
            verdict = {
                'no_contraction': counts['contraction_fmuladd_calls'] == 0
                and counts['explicit_fma_calls'] == 0,
                'no_fastmath_flags': counts['fastmath_flagged_ops'] == 0,
                'no_asm_fma': counts['asm_fmadd'] == 0 and counts['asm_fmsub'] == 0,
                'simd_vector_ops_present': counts['vector_fop_instructions'] > 0
                or counts['vector_iop_instructions'] > 0,
                'gate_branch_in_ir': counts['gate_branch_in_ir'],
            }
            report['verdicts'][name] = verdict
            print(f'{tag:<16} {surf:<5} {counts["contraction_fmuladd_calls"]:>8} '
                  f'{counts["explicit_fma_calls"]:>5} {counts["fastmath_flagged_ops"]:>5} '
                  f'{counts["vector_f32_fop_instructions"]:>8} '
                  f'{counts["vector_f64_fop_instructions"]:>8} '
                  f'{counts["vector_iop_instructions"]:>9} '
                  f'{counts["asm_fmadd"]:>10} {counts["asm_fmsub"]:>10} '
                  f'{counts["asm_fmla_vector"]:>9} {counts["asm_vector_loads"]:>8}')

    all_ok = all(v['no_contraction'] and v['no_fastmath_flags'] and v['no_asm_fma']
                 for v in report['verdicts'].values())
    report['all_no_contraction'] = all_ok
    (OUT / 'f2_w8_ir_audit.json').write_text(json.dumps(report, indent=2))
    print(f'\nall W=8 specializations contraction-free + fastmath-free: {all_ok}')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
