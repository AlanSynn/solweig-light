# SOLWEIG-light: Claude Code CPU backend 실행 패킷

## 바로 실행하기

1. 이 폴더 `optimization_v7_backends/`를 기존 저장소 루트에 둔다.
2. `perf/cpu-optimization`을 사용하는 기존 Claude Code 세션에서 `START_HERE.txt` 본문을 일반 작업 요청으로 입력한다. Codex `/goal` 명령은 사용하지 않는다.
3. Coordinator는 GLM-5.3, 어려운 구현·증명·독립 검수는 실제 사용 가능한 Opus/GLM으로 위임한다. Astra 재호출 단계는 없다.

새 integration branch를 만들지 않는다. 현재 HEAD와 사용자의 미커밋 변경을 보존하고, 분리 작업에는 immutable SHA의 detached worktree만 사용한다. 자동 push, PR, main merge, hosted CI 실행은 하지 않는다. 이전에 branch rename/push가 승인되었더라도 이번 작업의 추가 push 권한으로 해석하지 않는다.

## 이번 작업의 결론과 실행 순서

전체 모델을 MLX/OpenCL로 이식하지 않는다. 첫 실험은 현재 accepted `cylinder_longwave._longwave_primary`의 두 ordered sweep이다. 기존 coefficient/SLEEF 준비, accepted visibility decode, chronological state, GDAL 및 checkpoint는 유지한다.

- **A**: 현재 accepted Numba.
- **B**: 같은 물리식과 typed expression을 유지하면서 layout/scheduling만 개선한 Numba.
- **C**: B와 동일한 layout/schedule의 선택적 CPU backend.

실험 후보는 ISPC(부담이 크면 Highway), Dr.Jit LLVM, PyOpenCL+PoCL CPU다. 설치만 모두 시키지 않는다. Native와 Dr.Jit의 독립적인 소규모 구현을 우선하고, PoCL은 CPU runtime이 사용 가능하며 비용을 정당화할 때 같은 입력으로 평가한다. MLX CPU/Halide는 실제로 큰 pointwise/stencil 잔여 구간이 있을 때만 추가한다. 다른 framework는 이전 검토 문서의 후보로 남긴다.

B가 C만큼 빠르면 B만 채택한다. 어떤 backend도 수치·성능 기준을 통과하지 못하면 기본 Numba를 유지하고 각 실패 이유와 재현 코드를 남긴다. 미구현 stub나 import 성공을 작업 완료로 처리하지 않는다.

## 문서 안내

| 문서 | 읽는 역할 |
|---|---|
| `START_HERE.txt` | 실행 시작 |
| `CLAUDE_CODE_EXECUTION_PROMPT.md` | Coordinator |
| `PLAN.md`, `TASKS_CLAUDE.yaml` | Coordinator/integrator |
| `DESIGN_AUTHORITY.md`, `KERNEL_CONTRACT.md` | 수치 구현·reviewer |
| `dossiers/` | 배정받은 backend의 worker만 |
| `VALIDATION_POLICY.md`, `BENCHMARK_PROTOCOL.md`, `THROUGHPUT.md` | 수치·성능 owner |
| `BRANCH_AND_CI.md`, `DELEGATION.md`, `MODEL_ROUTING.md` | 실행 환경·위임 담당 |
| `reference/FRAMEWORK_REVIEW_KO.md` | 이전 20개 framework 검토, 필요할 때만 |
| `templates/` | 실제 입력 capture, capability, 결과 기록 |
| `tools/` | 패킷 관리·검증·모델 계산 보조 도구 |

`CLAUDE_PROJECT_RULES.md`만 기존 root CLAUDE.md에서 짧게 import할 수 있다. 전체 설계서를 항상 로드하지 않는다. `tools/install_assets.py`는 기본 dry-run이며 기존 지침을 덮어쓰지 않는다. `agents/`의 Opus 역할은 실제 Opus route가 확인된 세션에서만 사용한다.

## 작은 검증과 최종 한 번의 큰 실행

개발: tiny float/guard 검사 → 실제 kernel 16~128² → 64/128² TIFF의 24/48개 시점 → 128/256²의 작은 다중 타일 비교. 153 patches와 물리 모델을 줄여서 속도를 만들지 않는다.

1024² 공간 타일 24개 전체는 최종 combined source와 실행 설정을 고정한 후 기본 1회만 실행한다. 기본 새 대규모 baseline 0회, 필요한 reference 생성 최대 1회 또는 해당 항목 미검증, 원인 수정 후 최종 재시도 최대 1회다. 데이터가 없으면 실제 24타일 목표는 미검증이다. 과거 598.9초는 두 공간 장면의 기록이다.

CPU-only와 GPU 결과는 분리한다. 이번 primary campaign은 CPU-only다. GPU는 자동 선택하지 않으며, 선택적인 작은 연구 probe가 명시적으로 허용된 경우에도 CPU 결과와 합치지 않는다.

## 패킷의 증거 범위

이 패킷은 구현 지시, 검증 정책, 실제 사용 가능한 로컬 보조 코드다. SOLWEIG backend 구현 자체는 포함하지 않는다. `evidence/packet_checks.json`에 기록한 **40개 통과 검사**는 보조 코드·문서·DAG 등의 검사이고, SOLWEIG numerical parity나 framework speedup 증거가 아니다. 사용자 저장소·CI·모델 세션을 이 패킷 작성 중 변경하지 않았다.

검토 기준: 이전 소스 분석 `4689421c81a9dc9ad5e047bd7ff1dcdd704483b9`; 이번 branch 확인 `7a37a6f59924aa4c13444c977991d7f731ba5e8e`. 후자는 CI 기록 이후의 tip이며, 첫 reducer 파일의 Git blob은 같음을 확인했다. 전체 tree의 모든 파일이 같다고 주장하지 않는다. 실행 시 더 새로운 HEAD가 있으면 보존하고 관련 의존성만 다시 확인한다.
