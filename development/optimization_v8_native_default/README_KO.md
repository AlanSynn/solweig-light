# SOLWEIG-light v8: 의미 있는 native 기본 실행과 Zero-DX-change

## 실행

저장소 루트에 `optimization_v8_native_default/`를 두고, 이미 GLM-5.3로 동작하는 Claude Code에 `START_HERE.txt` 본문을 일반 요청으로 전달한다. `/goal`은 필요 없다. 기존 `perf/native-optimization` 브랜치를 계속 사용한다. 새 named integration branch를 만들거나 과거 SHA로 reset하지 않는다.

이 문서는 실행 패킷이다. 패킷 작성자는 SOLWEIG/native 성능을 새로 측정하거나 이 구현을 완료하지 않았다. `evidence/packet_checks.json`은 보조 도구 검사일 뿐 모델·wheel·native 검증이 아니다.

## 무엇을 완성할 것인가

목표는 ISPC를 켜는 스위치가 아니라, 기존 사용자가 같은 패키지·설치 흐름·import·함수·CLI·TIFF를 사용하면서 **지원되고 검증된 환경에서는 더 빠른 native 경로가 자동 선택되는 제품**이다. 기본 옵션과 기본 block=128에서도 시험한다. 예전 block=1024·T4만 이기는 것으로 완료하지 않는다.

일반 wheel 사용자는 ISPC, CMake, C/C++ compiler, zsh, 별도 extra, backend 환경변수를 추가로 준비하지 않는다. 기존 main의 GDAL 등 사전조건은 유지한다. 이 패킷이 GDAL 배포 문제까지 해결했다고 주장하지 않는다. Native 바이너리는 같은 배포 패키지의 platform wheel에 포함하며, 첫 실행에 다운로드하거나 컴파일하지 않는다.

**중요한 설치 구분:** wheel에는 사전 빌드한 바이너리를 실을 수 있지만, native 바이너리도 compiler도 없는 Git/source checkout에서 기계어를 저절로 만들 수는 없다. `pip install .`/sdist/editable은 새로운 compiler 요구 없이 main처럼 동작하도록 기존 Numba fallback을 제공한다. Native를 제공하는 wheel이 설치된 환경에서 자동 가속을 보장한다. Source install이 성공했다는 사실을 native 설치 성공으로 기록하지 않는다. 동일 source에 대응하는 검증된 local binary가 이미 있다면 빌드 도구가 이를 포함할 수 있지만 몰래 내려받지 않는다.

## 우선순위

1. 실제 worker의 비용·native 호출·fallback을 계측한다. 1.5~2.2% synthetic dense-wrapper 비중을 실제 packed pipeline 비중으로 사용하지 않는다.
2. Process/workflow 준비를 hot loop에서 제거한다. 한 번 확정한 native handle에는 compiler·artifact·ISA·ABI·math profile이 포함된다.
3. 기존에 빨랐던 Numba AoSoA control과 ISPC에 맞춰 decoder/classifier가 최종 layout을 직접 생산한다. Packing 비용을 숨기지 않는다.
4. 작은 microblock은 유지하되 dispatch region을 키운다. Region 내부 multicore와 tile worker의 CPU·RAM 예산을 함께 제한한다.
5. 충분히 큰 잔여비용이 있으면 longwave 전용 4-bit visibility predicate cache, 정확한 classifier 재사용, export 단일 traversal을 적용한다.
6. Prebuilt wheel, source fallback, 자동 선택 정책을 완성하고 **설치된 기본 호출**로 채택을 판단한다.

CPU-native 후보가 layout을 개선한 Numba보다 느리면 native 기본 승격은 미완료다. Numba 개선만 통합해도 좋지만 그것을 native 성과로 이름 붙이지 않는다. 목표를 억지로 만족시키려고 성능 gate나 수치 계약을 완화하지 않는다.

## 문서 지도

- `CLAUDE_CODE_EXECUTION_PROMPT.md`: coordinator가 실행할 전체 지시.
- `DESIGN_AUTHORITY.md`, `DX_CONTRACT.md`: 변경 가능한 범위와 불변 사용자 계약.
- `ARCHITECTURE.md`, `KERNEL_CONTRACT.md`: handle/region/buffer/수치 구조.
- `PLAN.md`, `TASKS_CLAUDE.yaml`: 구현 DAG와 파일 소유권.
- `BENCHMARK_PROTOCOL.md`, `PROMOTION_POLICY.md`, `THROUGHPUT.md`: 측정·기본 활성화·처리량 판단.
- `dossiers/`: 구현별 상세 레시피와 반례.
- `PACKAGING_AND_DISTRIBUTION.md`: compiler 없는 wheel 및 source 설치 전략.
- `VALIDATION_POLICY.md`, `BRANCH_AND_CI.md`, `DELEGATION.md`: 작은 검증, 같은 브랜치, 독립 위임.
- `FUTURE_OPTIMIZATION.md`: 이후 최적화가 같은 실수를 반복하지 않도록 하는 절차.

항상 읽는 `CLAUDE.md`에는 짧은 `CLAUDE_PROJECT_RULES.md`만 연결한다. 모든 dossier와 예전 패킷을 매 agent에 자동 import하지 않는다.

## 사용 가능한 도구

도구는 표준 라이브러리만 사용하며 SOLWEIG를 자동 실행하지 않는다. 먼저 `python optimization_v8_native_default/tools/preflight.py --repo .`로 읽기 전용 상태를 확인할 수 있다. `install_assets.py`, `prepare_worker.py`는 기본 dry-run이다. `--apply`에서도 기존 파일 충돌·다른 브랜치·symlink 경로는 거부한다.

최종 목표는 24개의 실제 공간 타일에 각 24개 시점이다. 598.9초의 두 장면 기록이나 네 synthetic 타일 기록은 이 목표의 완료가 아니다. 큰 실행은 최종 고정 후보에서만 수행하며 corpus가 없으면 해당 목표는 미검증으로 남긴다.
