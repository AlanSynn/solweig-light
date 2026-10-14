# S10: 의미 보존·시스템 최적화 전체 포트폴리오와 Claude Code 실행 패킷

## 목표
최신 main을 기준으로, 물리 모델과 반올림·API·출력·복구 계약을 유지하면서 실제 사용자의 총시간과 처리량을 개선합니다. Native를 반드시 채택하는 목표가 아닙니다. GLM-5.3 coordinator와 실제 사용 가능한 Opus/GLM worker가 구현부터 독립 검수·최종 판정까지 수행합니다.

## 이번 패킷의 핵심
- **73개 후보**를 수치 표현·장파/단파·분류·GVF·형상·comfort·runtime·I/O·CPU/GPU·연구안으로 분류했습니다. 가능한 모든 프로그램 변환을 완전 열거했다는 의미는 아닙니다.
- 단일값 배열 Tgwall의 원래 dtype 의미를 보존하는 compiled 경로가 첫 후보입니다. `.item()`로 바꾸는 단순 수정은 금지합니다.
- prepared GVF와 스레드 수를 분리하고, 독립적인 aniLum 순회와 실제 I/O·메모리 병목을 작은 독립 작업으로 나눕니다.
- 정확한 contribution table, consumer-specific visibility predicate, 실제 정보량에 맞는 표현, 캐시의 완전한 의존성을 상세 설계합니다.
- 입력의 반복 content hash, export 검증 traversal, checkpoint BytesIO 복사, wind 메모리, 실제 thread budget도 포함합니다. 검증·fsync를 삭제해서 속도를 얻지 않습니다.
- GPU도 전송·동기화·정밀도·설치 비용을 포함한 region에서 이길 때만 선택합니다. 기존 native 실패를 반복하지 않습니다.

## 브랜치 주의 (2026-10-13 갱신)
확인된 최신 main: `b3e5ca59a1080f02eda5ccda5e35a66af07e4bfa` (v5–N9 캠페인 종료, Dropbox 증거 아카이브, development/ 재편성 포함).
역사 캠페인 브랜치(`perf/native-optimization`, `perf/cpu-optimization`, `handover/campaign-line`)는 Dropbox로 아카이브 후 삭제되었습니다. 절대 병합하거나 재생성하지 않습니다. 현재 main에서 새 로컬 브랜치 `perf/s10-semantic-systems`를 시작하고, 이미 존재하면 감사 후 보존합니다. 사용자 변경은 보존합니다. main을 직접 수정하거나 reset/rebase/push/PR/merge/release하지 않습니다.

## 증거 저장
원시 측정·시행 산물은 Git에 넣지 않습니다. 작업 단위가 끝날 때마다 `dbxcli`로 Dropbox `Alan Synn/Research/solweig-light`의 s10/ 하위 트리에 적립(upload)하고, 저장소에는 경로·해시·소규모 결과만 기록합니다. 자세한 정책은 [../docs/evidence_storage.md](../docs/evidence_storage.md).

## 사용
이 폴더는 `development/optimization_s10_semantic_systems/`에 둡니다(저장소 루트도 허용). GLM-5.3 Claude Code 세션에 [START_HERE.txt](START_HERE.txt)의 본문을 일반 작업 요청으로 넣습니다. 전체 문서를 한 프롬프트에 중복해서 붙일 필요는 없습니다. Optional agent 정의는 [agents/](agents/)를 참고해 기존 프로젝트 설정을 보존하면서 설치합니다. 자동으로 provider/credential 설정을 바꾸지 않습니다.

## 문서 지도
| 문서 | 용도 |
|---|---|
| [상세 실행 요청](CLAUDE_CODE_EXECUTION_PROMPT.md) | 구현·검증·종료 지시 |
| [설계 권한](DESIGN_AUTHORITY.md) | 고정 계약과 위임 판단 |
| [소스 검토 범위](AUDIT_SCOPE.md) | 새로 확인한 사실과 아직 필요한 local audit |
| [전체 후보 목록](STRATEGY_CATALOG.md) | 73개 후보별 식·조건·비용·반례·중단 기준 |
| [수치 계약](SEMANTIC_CONTRACT.md) | scalar/singleton/field와 연산 순서 |
| [실행 계획](PLAN.md) | 초기 소수 후보와 한 번의 잔여 선택 라운드 |
| [작업 DAG](TASKS_CLAUDE.yaml) | 22개 실행 작업, JSON 형식의 유효한 YAML |
| [처리량 분석](THROUGHPUT.md) | 동일 자원·전체 경계의 수학적 모델 |
| [측정 정책](BENCHMARK_PROTOCOL.md) | 동결 조건·paired 관측·coverage |
| [작은 검증 정책](VALIDATION_POLICY.md) | 개발 64/128/256, 실제 목표는 최종만 |
| [DX](DX_AND_RELEASE.md) | 기존 사용자 설치·호출 변경 없음 |
| [분기·CI](BRANCH_AND_CI.md) | 같은 브랜치, latest-main reconciliation |
| [위임](DELEGATION.md) | 독립 작업 병렬화, 단일 파일 소유권·측정 owner |
| [모델 라우팅](MODEL_ROUTING.md) | opus 별칭과 실제 provider 구분 |
| [최종 판정](DECISION_AND_MERGE.md) | 실패해도 유한하게 종료하고 merge 대상 고정 |
| [출처](SOURCES.md) | 현재 commit과 문서별 확인 범위 |

## 도구와 검증의 의미
`python tools/check_packet.py`는 이 패킷의 링크·DAG·필드·manifest를 검사합니다.
`python tools/cost_model.py`는 가정에 따른 계산이며 벤치마크가 아닙니다.
`python tools/audit_repo.py --repo /path/to/repo --output /path/to/new-audit.json`은 실제 소스를 실행하지 않는 read-only 인벤토리입니다.
`python -m unittest discover -s tests -v`는 패킷 도구 검사입니다. SOLWEIG 검사 수로 세지 않습니다.
`tools/profile_descriptor.py`는 별도 실제 diagnostic에서 경계 입력의 type/rank를 기록하는 helper이며, 스스로 실행 경로를 증명하지 않습니다.

작성 단계에서는 GitHub 소스와 이전 증거를 검토했습니다. 네트워크 컨테이너 materialization은 DNS 실패였으며, GDAL이 없어 실제 모델·M4·GPU·upstream·설치 wheel은 실행하지 않았습니다. 독립 의미 검사와 계산기·패킷 검사는 별도 evidence class로 남깁니다. 이전 semantic probe는 원문과 원래 결과를 보존하고, 재실행 결과를 별도 파일에 기록합니다.

기존 보고서의 45% 프로파일 비중과 512² 시간은 원본 JSONL을 검증하지 않은 사용자 제공 관측입니다. 패킷의 예상 배수는 그 값을 사용한 조건부 계산이며 새로운 speedup 측정이 아닙니다.
