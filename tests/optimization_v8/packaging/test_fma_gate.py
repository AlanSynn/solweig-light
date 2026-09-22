"""FMA-audit gate (N8-20): refuses synthetic bad-asm fixtures, accepts
clean asm and the real staged kernel disassembly."""

import pytest

import build_native

BAD_FIXTURES = {
    "fmadd": "  fmadd s0, s1, s2, s3\n",
    "fmla": "  fmla v0.4s, v1.4s, v2.4s\n",
    "fmsub": "  fmsub d0, d1, d2, d3\n",
    "fnmadd": "  fnmadd s0, s1, s2, s3\n",
    "fnmsub": "  fnmsub v0.4s, v1.4s, v16.4s\n",
    "embedded_in_label": "Lmul_add:\n  fmadd s0, s1, s2, s3\n",
}

CLEAN_ASM = "\n".join([
    "  fadd s0, s0, s1",
    "  fmul s2, s2, s3",
    "  fdiv s4, s4, s5",
    "  ldr s6, [x0, x1, lsl #2]",
    "  fsub s7, s7, s8",
    ""]) + "\n"


@pytest.mark.parametrize("label,asm", sorted(BAD_FIXTURES.items()))
def test_gate_refuses_synthetic_bad_asm(label, asm):
    result = build_native.fma_audit(asm)
    assert not result.passed, f"audit accepted {label}"
    assert len(result.matches) == 1
    assert result.matches[0]["mnemonic"] in build_native.FMA_MNEMONICS
    assert result.matches[0]["text"].strip()  # offending line recorded


@pytest.mark.parametrize("line_no", [1, 7, 42])
def test_gate_reports_line_numbers(line_no):
    lines = ["  nop"] * 60
    lines[line_no - 1] = "  fmadd s0, s1, s2, s3"
    result = build_native.fma_audit("\n".join(lines))
    assert not result.passed
    assert result.matches[0]["line"] == line_no


def test_gate_accepts_clean_asm():
    assert build_native.fma_audit(CLEAN_ASM).passed
    assert build_native.fma_audit("").passed


def test_audit_or_fail_raises_typed_error():
    with pytest.raises(build_native.FmaAuditFailure) as excinfo:
        build_native.audit_or_fail(BAD_FIXTURES["fmadd"], "bad.s")
    assert "FMA AUDIT FAILED" in str(excinfo.value)
    assert build_native.audit_or_fail(CLEAN_ASM, "good.s").passed


def test_staged_kernel_asm_reaudits_clean(staged_generation):
    # the real 213KB disassembly shipped with the proof generation must
    # still pass the same gate the build applied
    asm_files = sorted(staged_generation.glob("*.s"))
    assert asm_files, "proof generation ships no audited disassembly"
    for asm in asm_files:
        assert build_native.fma_audit(asm.read_text(errors="replace")).passed, \
            f"{asm.name} contains contraction"
