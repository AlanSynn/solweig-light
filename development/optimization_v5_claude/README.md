# SOLWEIG-light v5: Claude Code + GLM-5.3 실행 패킷

고수준 설계와 수치 계약은 이 패킷에 고정합니다. Claude Code의 GLM-5.3 coordinator가 구현·검증·통합을 진행하고, 실제 연결된 Anthropic Opus worker/reviewer가 어려운 수치 구현과 독립 검수를 담당합니다. 실행 과정에서 Codex/Astra 세션이나 OpenAI API를 호출하도록 요구하지 않습니다.

**토큰 총량과 논리적 agent 수의 인위적인 제한은 없습니다.** 다만 CPU/RAM/디스크, provider rate limit, 같은 파일의 write ownership, target benchmark의 독점 실행은 지킵니다. Agent를 많이 띄우는 것과 수치 테스트를 동시에 많이 돌리는 것은 다릅니다.

## 시작

저장소 루트에 `optimization_v5_claude/`를 둔 뒤, 이미 GLM-5.3로 동작하는 Claude Code 세션에 `START_HERE.txt` 내용을 일반 작업 요청으로 붙여 넣습니다. Codex의 `/goal`을 실행할 필요는 없습니다. 별도 인증/라우팅 확인 후 실제 Opus를 위임합니다.

| 파일 | 용도 |
|---|---|
| `START_HERE.txt` | 바로 붙여 넣는 시작 요청, 4,000자 미만 |
| `CLAUDE_CODE_EXECUTION_PROMPT.md` | 완전한 실행 계약 |
| `DESIGN_AUTHORITY.md` | 이 챗에서 결정한 설계와 자율 판단 범위 |
| `IMPLEMENTATION_BLUEPRINT.md` | 알고리즘별 guard, 데이터 흐름, 의사코드, 실패 조건 |
| `PLAN.md`, `TASKS_CLAUDE.yaml` | 실행 단계, 병렬 wave, 파일 ownership |
| `MODEL_ROUTING.md` | GLM endpoint와 실제 Opus endpoint 분리 |
| `DELEGATION.md`, `agents/` | coordinator·구현·증명·독립 검수·통합·측정 역할 |
| `VALIDATION_POLICY.md`, `validation_policy.json` | 작은 검증 중심, 최종 1024²×24타일 1회 |
| `BRANCH_AND_CI.md` | 별도 로컬 branch, 자동 push/PR/merge 없음 |
| `STRATEGY_CATALOG.md`, `MATH_AND_PROOFS.md`, `dossiers/` | 48개 후보와 8개 격리 항목 전체 |
| `THROUGHPUT.md`, `THROUGHPUT_EXECUTION.md` | 조건부 계산, 측정 절차와 오차 한계 |
| `OPUS_REVIEW_REQUEST.md` | 별도 Opus 세션에 전달할 독립 검수 요청 |
| `templates/` | task packet, 결과, 의사결정, 자원·routing 기록 |
| `tools/` | 명시적 worktree 준비, agent 설치, 로컬 preflight, packet 검사 |

## 중요한 라우팅 경계

`opus`는 모델 선택 별칭이지 Anthropic 인증이나 endpoint 전환 기능이 아닙니다. Z.ai 설정이 `ANTHROPIC_DEFAULT_OPUS_MODEL=glm-5.3`이면 `model: opus`도 GLM으로 갑니다. `MODEL_ROUTING.md`의 기본 설계는 GLM 프로필과 실제 Anthropic Opus 프로필을 **별도 Claude Code 프로세스**로 분리하는 것입니다. 이미 양쪽을 지원하는 검증된 gateway가 있을 때만 한 세션에서 혼합 routing을 사용합니다. 새 gateway를 만드는 것은 이 최적화 과제에 포함하지 않습니다.

## 설치는 선택적이며, 기본은 preview

GLM 세션에 시작 요청을 주면 coordinator가 읽고 준비할 수 있습니다. 직접 사용하려면, 원래 checkout을 건드리지 않고 별도 worktree를 먼저 만듭니다:

```bash
python optimization_v5_claude/tools/prepare_worktree.py --repo . --destination ../solweig-light-claude-v5
# 출력된 base/path가 맞을 때만 같은 명령에 --apply를 추가합니다.
```

새 worktree로 이 패킷을 복사한 뒤 agent 자산 설치 내용을 확인합니다:

```bash
python optimization_v5_claude/tools/install_assets.py --repo .
# 실제 branch worktree 안에서만 --apply를 추가합니다.
```

설치기는 root CLAUDE.md 전체를 덮어쓰지 않습니다. 짧은 v5 지침 import만 추가하고 `.claude/agents/`에 충돌하지 않는 정의를 배치합니다. 기존 AGENTS/CLAUDE의 과거 Astra 필수 호출·4-agent cap만 새 사용자 지시와 대조하여 조정하고, 수치·보안·승인 경계는 보존합니다. global 설정, 인증키, provider endpoint, CI 설정은 설치기가 변경하지 않습니다.

`isolation: worktree`만 믿고 branch base를 추측하지 않습니다. 사용하는 Claude Code 버전에서 native worktree base를 확인하고, 필요한 worker는 정확한 commit으로 직접 만든 worktree에서 실행합니다.

## 유지된 비용 절감 정책

개발은 L0/L1 작은 실제 kernel, L2 64~128²의 실제 TIFF와 24/48개 시점, L3 128/256² 후보 선별을 사용합니다. 1024²×24타일은 최종 frozen candidate 기본 1회입니다. 새 대규모 baseline 기본 0회, 실제 수치 reference가 없을 때만 최종 단계에서 최대 1회 또는 미검증 표시입니다. 원인 수정 후 후보 재시도 최대 1회이며, 무제한 토큰은 대규모 benchmark 무제한 실행 권한이 아닙니다.

별도 `perf/claude-glm53-cpu-v5` 브랜치에서 종료하고 main에는 머지하지 않습니다. 개발 중 hosted CI를 피하는 기본 수단은 로컬 작업과 자동 push/PR 없음입니다. 필수 CI 우회나 거짓 pass는 허용하지 않습니다.

## 증거 범위

이 패킷은 구현 전략과 실행 도구입니다. v5 작성 중 SOLWEIG, 원본 oracle, 실제 M1 benchmark, Claude Code, GLM/Opus agent 또는 사용자의 GitHub branch를 실행·변경하지 않았습니다. `evidence/v5_packet_checks.json`은 문서/도구의 자체 검사만 기록합니다. 이전 수학적 검사는 `evidence/inherited_v4/`의 과거 자료입니다. 조건부 throughput 숫자는 실측 예측이 아닙니다.
