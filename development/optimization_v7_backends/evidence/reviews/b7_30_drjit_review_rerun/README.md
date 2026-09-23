# B7-30 drjit review — independent rerun harnesses and logs

Landed 2026-09-22 from /tmp/b7_30_drjit_review/ (volatile) so the paths cited
in reviews/b7_30_drjit_review.json remain resolvable. Content is copied
byte-identical; nothing re-run or edited.

- rerun_*.py + ir_dump_child.py — the reviewer's independent harnesses
  (fixture replay, adversarial suite, divide probe, IR audit).
- logs/rerun_fixture_replay.json, rerun_adversarial.json — rerun results
  backing review findings (520/520 bitwise; 24/24 adversarial).
- logs/ir_child_f32.txt / ir_child_f64.txt — the reviewer's fresh both-spec
  IR dumps (produced via ir_dump_child.py). logs/fresh_ir_f*.txt are
  zero-byte: the reviewer's direct dump path failed and the child-process
  route was used instead; retained for fidelity.
- logs/adversarial_stdout.txt — rerun console log.

The author's audit-cited IR source llvm_ir_symbolic_kernel_raw.txt is landed
alongside, in ../b7_30_drjit_f1_repair/.

SHA256:
{
 "ir_dump_child.py": "aad4d84f605dc08020492caad7ccf2aea66d560e2e28b1d7bcaa9d90391344bf",
 "logs/adversarial_stdout.txt": "946a31890849c2e32ff61c0d8f7cd8b7e1e8433ef5167aa4fbbfdc534fd8f266",
 "logs/fd2_f32.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 "logs/fd2_f64.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 "logs/fresh_ir_f32.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 "logs/fresh_ir_f64.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 "logs/ir_child_f32.txt": "3f4ab7caac0518ce51860efff1bbf95405b58bad6340ff4de37d55094d2c87b2",
 "logs/ir_child_f64.txt": "41bb7385d3bab2e87db0330e82ca84b9166c6d20441a5ca6b00555762a79ea84",
 "logs/rerun_adversarial.json": "e273464925152c9a61b1b286b2922cdfc8a02852039f2726d3a523cf180b1607",
 "logs/rerun_fixture_replay.json": "59907d79afb0a9e6b2cf79abae13145f57d6a8fd4abe57dd67412c01008d90cf",
 "rerun_adversarial.py": "03383ee0af9eaa495947eb207140cb5645bc71e089fb30c4668163cb1636fd8a",
 "rerun_divide_probe.py": "209813be2a71d90a9a2156053207e464cd17e07738ba985e83f71a991b571b66",
 "rerun_fixture_replay.py": "ba1076a2426c48c4a4d408b6b6bdeea44cf5e90e2fdc1113f723da96458f321e",
 "rerun_ir_audit.py": "8bdb846b98cdb6c1b23f23d07b0e06a6e4c14b09ec4ae3a06030527536293e07",
 "../../b7_30_drjit_f1_repair/llvm_ir_symbolic_kernel_raw.txt": "e861f8c8af15598746c7d603a056ac62817b4bf56181fb612c05e60231990ca4"
}
