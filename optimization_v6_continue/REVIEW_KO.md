# 같은 브랜치에서 이어가는 Claude Code 구현 설계

## 핵심 판단

이번에는 새 branch에서 광범위한 수치 재작성을 시작하지 않는다. 기존 `perf/claude-glm53-cpu-v5`의 검증된 변경을 유지하면서, **중복 geometry 생성 → phase 병렬 실행 → 사용하지 않는 복사 진단 계산 → 반복된 준비·검증** 순서로 남은 비용을 줄인다. GLM-5.3 coordinator와 실제 사용 가능한 Opus/GLM 구현·검수 agent가 이 설계를 실행한다. Astra를 다시 호출하는 단계는 없다.

검토한 원격 checkpoint는 `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`이다. 이 값은 reset 대상이 아니며 실제 checkout이 더 새로우면 필요한 코드 차이만 확인한다. 이 문서 작성에서는 production 코드, 사용자 branch, CI를 변경하지 않았다.

## 새로 확인한 가장 중요한 비용 후보

Standalone `prepare_geometry_exports`는 `geometry_identity`에 `construction`과 `standalone_implementation`을 추가한다. Simulation은 이 두 필드가 없는 `geometry_identity`로 native cache를 연다. `GeometryStore`는 identity 전체를 해시하고 비교한다. 따라서 같은 numerical geometry를 요청해도 서로 다른 키가 된다.

기본 full workflow가 standalone SVF 준비 후 simulation을 호출하고 두 키가 모두 cold이면, 동일한 연산을 두 번 수행하는 경로가 만들어진다. 이 경로의 시간은 이번에 실행해 측정하지 않았다. 먼저 작은 실제 TIFF에서 실제 producer를 감싼 call counter로 확인한다. 수치 함수를 mock으로 바꾸어서는 안 된다.

제안은 legacy cache를 무조건 믿는 것이 아니라, **공통 numerical producer/key와 별도의 export provenance**로 분리하는 것이다. 모든 geometry 반환값, 입력 fingerprint, math profile, cache corruption 검사, legacy TIFF/ZIP/NPZ, overwrite 및 save_svf의 관측 동작은 유지한다.

한 번의 geometry 생성이 G, 필수 export·검증이 E, simulation이 S라면:

    기존: 2G + E + S + 기타
    변경:  G + E + S + 기타 + 추가 검증 비용

이것은 loop의 작은 상수 개선보다 큰 후보다. 그러나 원래 시간에서 G의 비중을 측정하지 않고 구체적인 speedup을 약속하지 않는다.

## 그다음 구현 우선순위

1. **Geometry 단계의 병렬 실행.** 기존 persistent simulation pool을 다시 만들지 않는다. 먼저 numerical native-cache 준비를 bounded worker로 수행하고, public export publication은 원래 순서로 유지한다. 이후 측정에서 export가 큰 경우에만 병렬 staging과 ordered commit을 검토한다. Geometry 실패 후의 partial outputs와 error 순서도 계약이다.
2. **Anisotropic Lside의 필요 연산만 수행.** 현재 분기의 반환값은 방향별 원래 `Lup * 0.5`지만, 사용하지 않는 weight·wall·삼각함수를 미리 계산한다. Public general 함수는 유지하고 검증된 private pipeline에서만 생략한다. 경고나 `np.seterr` 오류를 바꾸면 안 된다.
3. **Cylinder longwave의 진단 누적 분리.** TMRT와 state에 필요한 total/side와 두 ordered sweep은 그대로 수행한다. TMRT 계산 이후 diagnostic return에만 추가되는 cardinal projection은 private output demand가 없을 때만 생략한다. Public return을 0으로 채우지 않는다.
4. **Cylinder shortwave의 작은 특화.** 원통 경로는 local reduction 20개 열 중 4개를 사용한다. 불필요한 scratch와 box-only direction 준비를 줄이고, 원래 7개 최종 반환값은 유지한다.
5. **GVF의 실제 expression 재사용.** 이미 snapshot copy 재사용은 적용됐지만 식 평가가 방향마다 반복된다. Water 변경 전/후와 alias를 분리한 뒤 expression 자체를 재사용한다. Python/NumPy block postprocess의 원래 typed DAG를 Numba로 옮기는 변경은 별도 patch다.
6. **Prepared multi-channel decoder.** 실패한 P01 전체 fusion을 다시 켜지 않는다. Immutable owner/descriptor 준비와 channel별 호출을 묶고, 현재 빠른 reducer를 그대로 사용한다. Raw bits, reserved code, independently supplied diffsh와 close lifetime을 지킨다.
7. **저장된 export의 한 번 읽기 검증.** 현재는 NPZ를 CRC용으로 읽고 비교를 위해 다시 import한다. CRC·schema·값 검사를 같은 bounded read에서 수행하되, failure precedence와 fsync·publication을 유지한다.

추가 후보는 dossier 08에서 현재 비용과 적용 영역에 따라 선택한다. 기존의 56개 아이디어 전체를 구현시키지 않는다.

## Throughput의 두 가지 정정

기존 598.9초 기록은 **공간 장면 2개, 각 24시점**이다. 공간 타일 24개의 목표 달성을 뜻하지 않는다. 기존 기록은 보존하고 설명 정정을 append한다.

또한 과거 small portfolio는 같은 Python process에서 RuntimeOptions를 바꿨다. 이것만으로 Numba의 실제 thread mask가 2/4로 바뀌었다고 볼 수 없다. 각 설정을 독립 child process로 실행하고, 설정된 pool과 실제 mask, dispatch route, admitted worker를 기록해야 한다. Threads=1과 >1의 GVF 구현도 다르므로 단순 scaling 식에 무조건 맞추지 않는다.

## 시간 예측 방식

    T = K*I_serial
        + ceil(K/Wg)*chi_g*G/r_g
        + ceil(K/We)*chi_e*E/r_e
        + ceil(K/Ws)*chi_s*S/r_s
        + setup

Geometry 중복을 없앤 뒤에는 두 번째 G를 S에 다시 포함하지 않는다. Serial export라면 We=1이다. Concurrent slowdown chi에는 줄어든 per-worker thread 수와 대역폭 경합까지 포함한다. 전체 worker를 늘렸다는 이유로 같은 CPU를 두 번 계산하지 않는다.

분해한 단계별 수치가 없으면 예측은 가정일 뿐이다. 제공한 phase calculator의 예시 입력은 **실측에 맞춘 값이 아니며**, 모델상 30분 이내라는 결과도 실행 성공으로 표시하지 않는다. 작은 cold/warm multi-tile 실험으로 단계별 시간을 보정한 뒤에만 최종 크기로 외삽한다.

## 실행 비용과 agent 운영

같은 branch에 대한 commit 권한은 integrator 한 명에게만 둔다. Worker는 기록된 SHA에서 detached worktree로 분리하며 새로운 named optimization branch를 만들지 않는다. 같은 파일의 대안 구현은 서로 다른 worktree에서 진행한다.

Agent 수와 inference token의 인위적 상한은 없다. 그러나 local build·test의 CPU/RAM/disk는 합산해서 제한하고 benchmark는 한 owner가 독점한다. Manager의 진행 확인이나 transcript 반복 읽기는 하지 않는다. 완료·실제 blocker 이벤트에서만 결과를 받는다. 수치 검증과 OS 자원 감시는 계속 필요하다.

`opus`라는 alias는 실제 Anthropic Opus의 증거가 아니다. 기존에 인증된 별도 provider 프로필이나 검증된 gateway에서 실제 route를 확인한다. 없으면 독립 GLM 검수라고 기록하고 진행하며, gateway·credential 구축을 이번 수치 최적화의 선행 과제로 만들지 않는다.

## 검증 범위

개발 중에는 actual kernel의 작은 비교와 64/128-square 실제 TIFF의 전체 24/48개 시점 state를 검사한다. 128/256-square의 몇 개 타일로 성능 후보를 선택한다. 1024 실행은 마지막 source/wheel/protocol 고정 뒤 actual 24-tile campaign에서만 한다. 기본 1회, 원인 수정 후 작은 회귀 검사를 통과한 경우 추가 1회만 허용한다.

기존 큰 reference는 두 장면만 덮는다. 나머지 타일의 기준값이 없으면 별도 계획이나 미검증 표기가 필요하다. 두 reference를 복제해 전체 target의 수치 검증으로 부르지 않는다.

이번 패킷의 자체 검사는 문서·DAG·scope guard·phase calculator·branch 보호 helper에 대한 검사다. 별도 tiny Numba probe의 1/2 thread 설정도 확인했지만 SOLWEIG 또는 사용자의 M1 benchmark는 아니다. 실제 모델·oracle·Claude provider 세션은 이 패킷 작성 과정에서 실행하지 않았다.
