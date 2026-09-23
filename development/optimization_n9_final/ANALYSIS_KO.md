# 마지막 재시도의 근거와 종료 판정

## 판단

한 번의 범위가 닫힌 재시도는 타당하다. 다만 목표는 더 이상 native 연구를 계속 유지하는 것이 아니다. 실제 설치·기본 사용에서 이기는 native를 선택하거나, 이기지 못하면 검증된 CPU 경로만 main에 전달할 상태로 정리하고 이번 최적화를 끝낸다. Git 원천은 perf/native-optimization, 대상은 main이다. 최종 SHA는 구현·검증 이후 결정되며 이 분석의 7abe526a를 자동 승인하지 않는다.

## N8 기록의 정확한 의미

선택 문서 `n8_32_selection_record.json`은 B와 C 모두 production block에서 기본 통합하지 않았다고 명시한다. `numba_improvement_only_native_goal_open`이라는 label은 B 개선이 기본 실행됐다는 증거가 아니다. 현재 기본값은 row A이며 selector의 일부 파일 읽기는 여전히 실행된다. 작업패킷 종료와 native 목표 달성을 구별해야 한다.

B=1024 결과는 다음 구간별 min-of-9의 합이다. 실제 연속 실행시간은 아니다.

| mix | A0p | B1 | C1 | 단위 |
|---|---:|---:|---:|---|
| binary | 3.3627 | 3.5468 | 3.4655 | ms, 구성요소 최소값 합 |
| mixed | 2.7487 | 3.0173 | 2.9668 | 동일 |
| raw | 0.5485 | 0.6943 | 0.7338 | 동일 |

`sum_j min_r t[j,r]`는 실제 `median_r T_composed[r]`가 아니다. 캐시·할당·재사용·thread 상태가 다르고 전체 classifier와 실제 region 연결이 빠져 있다. 이 때문에 N8의 보수적인 승격 거부는 유지하되, "통합한 native가 production에서 반드시 이 정도 느리다"는 강한 주장은 하지 않는다.

## 남은 비용

N8의 direct producer는 binary에서 C1 회계의 약 85%, mixed에서 약 83%다. 단순 mask pack 제거에 대한 기존 반사실 계산은 binary/raw 약 2~3% 개선, mixed 약 0.8% 손해에 그쳤다. 이것만으로 의미 있는 native 기본값을 지지하기 어렵다.

현재 producer는 mode로부터 가변 나눗셈·나머지 연산을 계산한다. 검증된 비음수 pixel i에 대해 다음은 정확하다.

- binary: `(data[i >> 3] >> (i & 7)) & 1`
- ternary: `(data[i >> 2] >> ((i & 3) << 1)) & 3`

patch에서 mode를 한 번 분기해 literal 연산으로 특화한다. raw의 바이트 해석과 효율적인 원래 반복 구조는 유지한다. code 3의 첫 오류, byte 경계, tail, signed-zero/NaN bit, mapped lifetime을 그대로 검증한다.

## 이 챗에서 실행한 제한된 실험

프로젝트 전체를 import하지 않고 producer의 core 연산을 전사한 generic 함수와 literal-mode 변환을 비교했다. Python 3.13.5 / NumPy 2.3.5 / Numba 0.65.1, Linux x86_64이며 프로젝트 M1 환경이 아니다.

원래 raw 반복 구조를 유지하는 두 번째 variant의 관측 ratio `generic / variant`:

| block | binary | mixed | raw |
|---|---:|---:|---:|
| 128 | 1.75 | 1.61 | 0.95 |
| 1024 | 1.63 | 1.36 | 1.03 |

raw는 개선을 주장할 수준이 아니고 128에서는 더 느렸다. 최초 variant의 더 큰 raw regression도 결과파일에 남겼다. 64가지 start/width/size 사례와 독립 예상 57,984개 uint32 값, 15개 reserved-code 오류 검사를 통과했지만, 실제 N8 패키지·오류 전체·M1·classifier·native·전체 pipeline의 통과를 의미하지 않는다. 평균·중앙값과 raw 반복값은 evidence에 있다. 이 결과는 구현 방향의 근거이지 기본 활성화 증거가 아니다.

## 필수 구조 수정

1. direct AoSoA mask 생성기를 실제 stream에 연결한다. 옛 pack 비용을 빼서 새 결과를 만들지 않는다.
2. coefficient/ABI/artifact/owner의 불변 검증을 invocation에서 한 번 수행한다. 사후 오류와 동적 bounds는 유지한다.
3. 전체 장면 AoSoA materialization을 없앤다. 현재 `_execute_row`는 `0,total`을 producer/classifier에 전달한다. 세 uint32와 두 bool의 payload만 1024²에서 2142 MiB, 2048²에서 8568 MiB다. 비활성 경로라 현재 사용자 실행이 이 메모리를 쓴다는 뜻은 아니지만, 승격하면 피할 수 없는 구조적 비용이다.
4. microblock 1024의 같은 payload는 2.092 MiB/slot이다. 4개 slot은 8.367 MiB다. required outputs와 다른 state, runtime을 포함한 총 RSS는 별도이며 이 숫자만으로 admission하지 않는다.
5. strongest Numba에도 같은 producer/mask/layout 개선을 적용한다. native만 공통 개선을 받아 이기는 불공정 비교를 막는다.

## 목표와 손익분기

전체 시간 비율 f를 차지하는 영역이 s배 빨라지고 overhead가 δ만큼 추가되면 전체 speedup은 `1/(1-f+f/s+δ)`다. 블록이 20% 빨라졌더라도 그 블록 경로가 전체의 20%라면 전체 개선은 약 3.4%일 뿐이다. N8 이후 실제 f는 새 continuous profile로 구해야 한다.

기존 구성 회계로 구하는 가정값: mask pack이 실제 사라지고 classifier 추가비용이 0이며 guard가 0.0122ms가 된다면 binary/mixed의 local 1.10x를 위해 producer가 각각 약 1.055x/1.100x 빨라져야 한다. 이것은 실현 가능성을 보는 산술이지 새 execution result가 아니다. 가드·classifier·task 비용이 달라지므로 연속 실행으로 검증한다.

## 끝내는 방법

새 GPU/프레임워크/수학식/format을 추가하지 않는다. tuning에서 가까운 producer 두 variant까지, 통합 후보 하나, 독립 검수와 원인에 따른 수정 한 묶음, 마지막 비교 한 번으로 닫는다. 측정 가능한 유효 비교가 실패하면 native는 이번 릴리스에서 종료한다. 환경 문제로 자격을 입증하지 못해도 대기·재시도를 무한히 이어가지 않는다.

native가 이기면 compiler-free no-env 설치까지 검증된 최소 실행 경로를 포함한다. 실패하면 검증된 CPU 개선은 살리고 N8의 비활성 자동선택·research runtime 의존성을 설치 경로에서 제거한다. 연구와 오류 재현은 history/비설치 영역에 보존한다. 기존 B7 expert 옵션을 보존하기로 한 계약도 별도로 검사한다.

최종 원천 SHA, target main SHA, merged-tree preview, 실제 활성 함수, included/excluded 파일과 이유, 원본 SOLWEIG-GPU 비교 여부, 24실타일 목표 상태를 기록한다. native 연구는 `not_selected_for_this_release` 또는 실제 qualified로 종료하며, 미검증 주장은 별도로 명시한다. 작업 종료를 native 성공으로 바꾸지 않는다.
