# SOLWEIG-light 최적화 실행 패킷 v4

**작게 개발하고, 실제 1024² 전체 batch는 마지막에 검증하며, 별도 로컬 브랜치를 남깁니다.** 기존 48개 최적화 후보와 8개 격리 항목의 수학적 내용은 유지하고, 실행·검증·CI 일정을 경량화했습니다.

## 사용

저장소 루트에 `optimization_v4/`를 둡니다. Codex `/goal`에는 `GOAL.txt` 본문을 사용합니다. 일반 상세 요청에는 `ASTRA_EXECUTION_PROMPT.md`를 사용합니다. 둘을 매번 중복 주입하지 않습니다. 이 파일들을 받는 것만으로 root AGENTS, 저장소 소스, Git 브랜치나 GitHub 설정이 바뀌지는 않습니다.

| 문서 | 용도 |
|---|---|
| `PLAN.md` | 새 실행 순서와 완료 범위 |
| `VALIDATION_POLICY.md` / `validation_policy.json` | L0-L4, 증거 재사용, 실행 예산 |
| `BRANCH_AND_CI.md` | 로컬 브랜치, worktree, CI 최소화, 나중 머지 |
| `GOAL.txt` | `/goal ` 포함 4,000자 이내의 실행 지시 |
| `ASTRA_EXECUTION_PROMPT.md` | Astra/Luna 위임 및 구현·검증 지시 |
| `AGENTS_OPTIMIZATION.md` / `DELEGATION.md` | 짧은 상시 규칙과 완료 이벤트 기반 운영 |
| `TASKS_OPTIMIZATION.yaml` | 기존 작업을 초기화하지 않는 v4 작업 의존성 |
| `STRATEGY_CATALOG.md`, `MATH_AND_PROOFS.md`, `dossiers/` | 기존 수학적 최적화 후보와 증명 의무 |
| `THROUGHPUT.md` | 조건부 계산 및 작은 자료에서의 외삽 한계 |
| `templates/` | 최종 프로토콜, validation ledger, worker packet, 머지 검토 기록 |

## 새 기본값

L0/L1은 작은 상태·실제 커널 검사, L2는 64-128²의 실제 TIFF 파이프라인과 24/48개 시점, L3는 128/256² 후보 선별입니다. 실제 153 patches와 필요한 물리를 유지합니다. 구조상 필요한 경우만 256² fixture, 구체적인 scaling 질문이 있을 때만 512² probe를 사용합니다.

1024²는 개발 worker별·커밋별로 실행하지 않습니다. 최종 소스와 wheel을 고정한 뒤 실제 24타일 batch를 기본 1회 실행합니다. 기존 v3의 5쌍 전체 batch 반복은 이 새 프로토콜에서 요구하지 않습니다. 새 대규모 baseline은 기본 0회이며, 필수 최종 수치 reference가 없을 때만 최종 단계에서 1회 한도로 근거를 기록해 생성하거나 그 범위를 미검증으로 남깁니다. 작은 결과를 큰 타일 성능 증거로 간주하지 않습니다.

최종 실패 시 작은 재현 사례로 수정하고 영향을 받은 검사를 통과한 뒤 1회의 추가 전체 실행만 미리 허용합니다. 그 이상은 새로운 캠페인입니다. 실패/timeout은 삭제하거나 pass로 바꾸지 않습니다. 단일 통과는 `target_demonstrated_once`이며 신뢰구간·p95·안정적인 deadline 또는 P7/P8 전체 완료 증명이 아닙니다.

## 브랜치와 CI

`perf/lean-cpu-v4` 별도 로컬 worktree에서 진행하고, family worker마다 독립적인 write scope를 사용합니다. 검토된 변경만 최적화 브랜치로 통합합니다. 자동 push, PR, main 머지, release는 하지 않습니다. 사용자가 나중에 머지를 요청할 때 당시 main과 달라진 의존성 및 필수 CI만 확인합니다.

개발 중 remote push를 하지 않는 것이 기본 CI 절감 방식입니다. PR을 요청받으면 작은 실제 CPU end-to-end 검사와 필수 checks는 유지하고, 큰 workload·플랫폼 matrix는 별도 요청 캠페인으로 분리합니다. `[skip ci]`나 global Actions 중단으로 필수 검사를 우회하지 않습니다.

## 이번 작성의 증거 범위

이 버전은 문서와 실행 템플릿을 개정했습니다. 실제 저장소 브랜치 생성, production 수정, GitHub Actions 설정 변경, SOLWEIG 수치 실행 또는 target benchmark를 하지 않았습니다. `evidence/v4_packet_checks.json`은 길이·JSON/YAML·의존성·링크·정책 정합성 같은 패킷 검사만 기록합니다.

기존 v3 분석 결과는 `evidence/inherited_v3/`에 보관했습니다. 이 파일들을 이번 버전에서 새로 실행한 것으로 제시하지 않습니다. 수학적 synthetic 검사와 조건부 throughput 모델은 production 증거나 실제 속도 측정이 아닙니다.

패킷 구조 검사만 실행하려면:

```bash
python optimization_v4/tools/check_packet.py
```

이는 SOLWEIG를 실행하지 않습니다. 기존 `tools/self_check.py`와 `tools/throughput_model.py`는 선택적 분석 도구이며 매 agent 시작이나 코드 변경마다 실행할 필요가 없습니다.
