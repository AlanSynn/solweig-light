# N9: 마지막 최적화 판정과 main 머지 대상 확정

기준일: 2026-09-23. 이 패킷은 설계와 제한된 독립 디코더 실험입니다. SOLWEIG 전체나 M1 native 실행을 이 세션에서 검증한 결과가 아닙니다.

## 목적

`perf/native-optimization`에서 한 번의 범위가 닫힌 후보를 평가합니다. 성공하면 native를 검증된 범위에서 기본 적용할 머지 대상을 만듭니다. 실패하거나 자격을 입증하지 못하면 CPU-only 머지 대상을 정리하고 native 연구를 이번 릴리스에서 종료합니다. 다음 세션에 다시 OPEN을 넘기는 구조를 없앱니다.

- 확인한 소스: `7abe526aae2f97e689b1a1e4ae183e5370f29aa1`.
- 확인한 main: `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`.
- 이 SHA로 reset하지 않습니다. 실행 시작과 종료 시 실제 상태를 기록합니다.
- 원천 브랜치: `perf/native-optimization`. 대상: `main`.
- 이번 패킷은 push/PR/main merge/release 권한을 부여하지 않습니다. 최종 검토용 SHA와 diff를 고정합니다.

## 달라진 판단

1. N8의 선택 기록은 B와 C가 모두 기본 통합되지 않았다고 명시합니다. `numba_improvement_only_native_goal_open`이라는 이름만으로 새로운 B 가속이 배포됐다고 쓰지 않습니다.
2. N8의 B=1024 값은 여러 component의 min-of-9를 합한 비용 회계입니다. 실제 연속 wrapper나 전체 프로그램의 end-to-end 시간과 구분합니다.
3. 현재 비활성 region 경로는 전체 장면의 세 visibility와 두 mask를 펼친 뒤 fanout합니다. 최종 후보는 이 경로를 그대로 켜지 않습니다.
4. 모델/플랫폼을 늘리지 않습니다. 기존 ISPC/Numba, mode별 decode, 직접 mask 생성, prepared ownership, bounded scratch만 다룹니다.
5. 성능 미달이면 판단을 내리고 정리합니다. 성공할 때까지 프로토콜·threshold·타깃을 변경하지 않습니다.

## 읽을 순서

- 실행: `START_HERE.txt`, `CLAUDE_CODE_EXECUTION_PROMPT.md`, `PLAN.md`.
- 구현자: `LAST_ATTEMPT.md`의 소유 구간만.
- 측정자: `MEASUREMENT.md`, `evidence/n8_attribution.json`.
- 통합자: `MERGE_SCOPE.md`, `DECISION_CONTRACT.md`.
- 독립 reviewer: 해당 diff, 실제 raw 결과, 위 계약. 이미 유효한 테스트를 전부 재실행하지 않습니다.

## 도구

- `probes/decoder_probe.py`: Linux x86에서 실행한 독립적인 decode 비교. 실제 패키지를 import하지 않습니다. 비교 함수는 소스의 core recurrence를 전사한 것입니다.
- `evidence/decoder_probe_result_v2.json`: 이 세션의 합성 측정. raw 128은 개선이 없었고 초기 variant의 raw regression도 기록합니다. M1/전체 실행 속도 예측으로 사용하지 않습니다.
- `tools/cost_model.py`: N8 구간 회계와 조건부 speedup 계산. 실행 증명 기능이 없습니다.
- `tools/check_final_record.py`: 최종 기록의 필수 필드와 모순을 검사합니다. 기록이 참인지 독립 reviewer가 확인해야 합니다.
- `tests/test_packet.py`: 위 보조 계산과 기록 규칙의 테스트일 뿐, SOLWEIG 수치 검증이 아닙니다.

기본 사용법은 동일한 `pip install`과 `from solweig_light import ...`입니다. 새로운 env, native compiler, runtime download, 입력 변경, 출력 축소를 요구하면 안 됩니다. 기존 GDAL 설치 전제를 해결했다고 주장하지 않습니다.
