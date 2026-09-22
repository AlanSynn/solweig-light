# SOLWEIG-light: CPU 및 이식 가능한 가속 프레임워크 검토

검토일: 2026-09-21

대상 브랜치: `perf/cpu-optimization`

확인한 commit: `4689421c81a9dc9ad5e047bd7ff1dcdd704483b9`

## 1. 결론과 증거 범위

전체 runtime을 하나의 새 배열 라이브러리로 바꾸기보다는, Python API·GDAL I/O·cache·chronological state를 유지하고 비용이 큰 계산 구간만 교체하는 것이 우선이다.

- Python에서 MLX와 비슷한 지연 평가·JIT·융합을 원할 때: **Dr.Jit LLVM**을 우선 실험한다.
- CPU SIMD 활용을 명시적으로 통제하고 x86/ARM용 binary를 배포할 때: **ISPC 또는 Highway** 중 하나를 선택한다.
- 같은 kernel source로 여러 vendor의 CPU/GPU를 겨냥할 때: **PyOpenCL + PoCL CPU**를 기준으로 먼저 실험하고 GPU 결과는 별도로 측정한다.
- 규칙적인 image/stencil/pointwise stage의 재구성이 필요할 때: **Halide**가 다음 후보이다.
- MLX CPU는 실제 후보이지만, 전체 SOLWEIG 이식의 첫 선택은 아니다. 현재 CPU backend는 C++ loop를 생성·컴파일하는 경로가 있으며, Linux CPU 설치도 문서화되어 있다.

이 문서는 조사와 조건부 성능 분석이다. 현재 repo, original oracle, M1, MLX, Dr.Jit, ISPC, PoCL 등의 커널을 새로 실행하거나 benchmark하지 않았다. `analyze.py`와 tests는 산술 민감도 계산만 실행한다. 프레임워크별 speedup을 측정했다고 주장하지 않는다.

## 2. 현재 코드가 이미 해결한 것

현재 handover에 따르면 shared geometry recipe/key, demand-specific longwave/shortwave, prepared GVF와 typed block postprocess, phase-aware admission 및 geometry phase adapter는 이미 반영됐다. 이전의 중복 geometry나 전체 NumPy GVF 후처리를 새 최적화 대상으로 중복 계산하지 않는다.

반면 fused radiation은 기존 측정에서 불리했고, prepared visibility decoder도 네 비교 cell에서 21–24% 느려 기본 OFF다. 현재 accepted 경로를 기준으로 비교해야 하며, 더 큰 fused kernel이라는 이유만으로 기본 활성화하지 않는다.

v6 cold 개선은 약 6–16%의 개발용 관측이고 warm은 대체로 비슷했다. Host가 조용하지 않아 release-grade speedup으로 사용할 수 없다. 실제 24개 공간 타일 목표는 데이터 부재로 미검증이다. 과거 598.9초는 두 공간 장면에 각각 24개 시점을 실행한 기록이지, 공간 타일 24개의 처리시간이 아니다.

## 3. 다섯 종류의 이식성

1. Source portability: 같은 source가 x86/ARM 등에서 컴파일되는가.
2. Deployment portability: OS/ISA별 wheel·runtime·driver를 실제 제공할 수 있는가.
3. Device portability: CPU, CUDA, OpenCL, Metal 등 중 어떤 장치에 실행되는가.
4. Numerical portability: original dtype, SLEEF, rounding, signed zero, NaN 및 분기를 보존하는가.
5. Performance portability: 같은 알고리즘이 다른 cache/SIMD/thread 구조에서도 빠른가.

같은 Python API나 OpenCL source만으로 2–5가 보장되지는 않는다. CPU-only 결과와 GPU offload 결과는 별도의 제품 profile과 성능 표로 관리한다.

## 4. 후보군 비교

| 후보 | 실행 모델 및 플랫폼 방향 | 이 코드에 대한 판단 |
|---|---|---|
| Numba/LLVM 유지 | Python typed loop, native CPU | accepted reference와 fallback; 새 backend가 이 기준을 실제로 넘어야 한다. |
| Dr.Jit LLVM | Python/C++ traced per-element program, SIMD·thread pool, symbolic loops; CPU와 별도 CUDA/Metal backend | MLX-like Python 경험과 ray/ordered loop가 만나는 가장 관련성 높은 후보. |
| ISPC | SPMD를 CPU SIMD로 컴파일, x86/ARM, C ABI | longwave 두 ordered sweep과 pixel-parallel ray에 우선 실험할 CPU 후보. |
| Highway | C++ portable SIMD와 runtime ISA dispatch | 강한 CPU 통제; 수동 구현량이 늘며 ISPC와 둘 다 production에 넣을 필요는 없다. |
| Halide | algorithm/schedule 분리, CPU 및 CUDA/OpenCL/Metal 등 | 규칙적 raster 연산·stencil·중간 배열 최적화에 적합; ray recurrence는 추가 설계 필요. |
| MLX CPU | lazy arrays, compile, CPU C++ JIT; macOS Apple silicon 및 문서화된 Linux CPU | pointwise chain probe에는 적합. 전체 model과 I/O를 단순 치환하기에는 부적합. |
| PyOpenCL + PoCL | OpenCL kernel, LLVM 기반 portable CPU runtime | CPU-first OpenCL 비교에 적합; binding과 실제 device/runtime를 구분해야 한다. |
| SYCL / AdaptiveCpp | C++ single-source CPU/GPU | 장기적인 여러 vendor 확장 후보. toolchain·backend별 지원 수준과 packaging 비용이 크다. |
| Kokkos | C++ execution space/layout 추상화, Serial/OpenMP/Threads 및 GPU backend | 대규모 HPC 이식에 적합; 현재 Python 프로젝트의 작은 포팅에는 무거울 수 있다. |
| Taichi | Python imperative kernel DSL, CPU 및 여러 GPU backend | 작은 수치 kernel 작성은 편리; dtype, fast_math, global runtime, compiler 결과를 확인해야 한다. |
| DaCe | Python/NumPy에서 dataflow graph 및 native code 생성 | stage 전체 데이터 이동 최적화 연구에 유용; 전문적인 graph 변환·검증 비용. |
| JAX/XLA | traced array program, CPU/GPU | 순수 큰 배열 함수에는 강점. compiler algebraic simplification과 ordered recurrence의 exactness가 장애물. |
| Pythran | scientific Python subset의 AOT C++/SIMD | 작은 NumPy-heavy 함수의 낮은 경계 비용 후보; 이미 좋은 Numba loop보다 빠르다는 보장은 없다. |
| Cython + C/C++/OpenMP | typed loop와 native interface | 점진적인 native bridge와 제어에 적합; 사용만으로 fusion/SIMD가 생기지는 않는다. |
| ArrayFire | CPU/CUDA/OpenCL array backend | regular array expressions 후보; opaque reductions와 잦은 custom loop 경계가 부담. |
| Futhark | data-parallel language, multicore/OpenCL 등 | CPU/GPU compiler 연구 후보; 언어 재작성과 ordered reduction 제약으로 우선순위 낮음. |
| IREE | MLIR AOT compiler/runtime, CPU 및 GPU deployment | 장기적인 배포·compiled graph에 유용. 지금은 framework 개발 비용이 커질 수 있다. |
| TVM | tensor program compiler와 scheduling | custom tensor kernel은 가능하나 ray/strict-state 전체 모델 이식은 우선순위 낮음. |
| Julia KernelAbstractions | CPU/GPU kernel abstraction | Python 프로젝트에 Julia runtime·interop를 추가하는 비용을 정당화해야 한다. |
| Slang | CPU 및 여러 GPU target으로 shader code 생성 | portable GPU frontend 후보. CPU codegen 지원과 CPU 최고성능은 같은 말이 아니다. |

Backend 존재와 release wheel·OS 지원은 다르다. 특히 개발 branch의 새 Metal/Windows 기능을 배포된 안정 기능으로 간주하지 말고, 실제 시험할 version을 pin한다.

## 5. 왜 Dr.Jit, ISPC, OpenCL을 먼저 비교하는가

### 5.1 Dr.Jit LLVM

`@dr.syntax`/symbolic while loop는 개별 pixel마다 다른 반복 횟수를 표현할 수 있고 loop state를 CPU/GPU register에 유지하도록 컴파일한다. 이는 per-pixel ray와 patch recurrence에 자연스러운 형태다. 자동 미분은 필요하지 않으므로 non-AD LLVM types를 사용한다.

단, Python `for range(153)`를 그대로 trace하면 unrolling으로 graph와 compile cost가 커질 수 있다. 의도한 symbolic loop인지 확인한다. 거대한 kernel은 register pressure와 branch divergence 때문에 오히려 느려질 수 있다.

`JitFlag.FastMath`는 기본 flag set에 포함된다. 반드시 해제하고, 이후에도 compiled arithmetic, constants, min/max, dtype, FMA 및 math 함수가 기존 profile과 일치하는지 검증한다. FastMath=False 하나가 exactness 증명은 아니다.

### 5.2 ISPC 또는 Highway

하나의 SIMD lane이 하나의 pixel을 소유한다. patch/ray loop는 lane 내부에서 원래 순서를 유지하고, uniform patch 계수는 lane들 사이에 공유한다. NumPy의 이미 준비된 contiguous 배열을 C ABI로 전달할 수 있어 별도 GPU transfer가 필요 없다. Layout 재배치가 생긴다면 그 비용은 포함한다.

ISPC는 uniform/varying 구분을 language에서 제공한다. Highway는 SIMD intrinsic을 portable C++로 명시한다. 둘 중 빠른 개발 경로 하나를 선택한다. Compiler/version/flags를 pin하고 기존 explicit FMA만 보존한다. ISPC 표준 math의 version 변화로 bit pattern이 바뀔 수 있으므로 pinned SLEEF classification을 초기 시험 경계 밖에 둔다.

### 5.3 MLX CPU

공식 설치 문서는 Linux CPU extra를 제공한다. 현재 공개 main의 CPU compiler는 elementwise C++ loop를 생성하여 shared library로 컴파일·cache한다. 그러므로 Apple GPU 전용이라고 배제하는 것은 부정확하다.

그러나 NumPy를 MLX 이름으로 치환해도 original ray schedule, packed visibility, ordered sums, state ownership, checkpoint I/O가 자동으로 변환되지는 않는다. `mx.compile`이 합치는 것과 복사 비용·tracing·compiler 가용성을 포함해 pointwise stage에서만 먼저 확인한다. current main source와 installed release는 별도로 기록한다.

### 5.4 OpenCL/PoCL

PyOpenCL은 Python interface이고 CPU code generation·execution은 PoCL 등의 OpenCL implementation이 담당한다. CPU 장치를 명시적으로 선택하고 vendor, device, compiler, fp capability를 보고한다. GPU가 자동 선택된 측정은 CPU speedup이 아니다.

OpenCL C의 FP_CONTRACT 기본값은 ON이므로 arithmetic contraction을 명시적으로 통제해야 한다. relaxed math/native_*를 사용하지 않고, fp64와 denormal을 query하며, 현재 구현이 기대하는 min/max/NaN 의미를 재현한다. Apple의 system OpenCL은 deprecated다. macOS GPU의 장기 경로는 Metal을 별도 검토하고, PoCL CPU 지원은 실제 build로 확인한다.

## 6. 포팅할 첫 계산 구간

`radiation/cylinder_longwave.py::_longwave_primary`가 우선 후보다.

입력은 prepared visibility/mask, patch coefficients, Lup이다. 두 ordered patch sweep을 모두 유지하며 primary totals와 선택한 진단을 반환한다. 첫 sweep의 sky sum에 따라 두 번째 reflection sweep이 결정된다.

```
for independent pixel packet:
    accumulator[each pixel] = original typed zeros
    for patch in ORIGINAL_ORDER:
        perform ORIGINAL_TYPED_NODES per pixel
    prepare reflected contribution from completed first sweep
    for patch in ORIGINAL_ORDER:
        perform ORIGINAL_TYPED_NODES per pixel
    write owned outputs
```

첫 시험에서는 accepted decode 경로가 만든 동일 배열을 모든 backend에 준다. Decode와 math backend를 동시에 바꿔 원인 분석을 어렵게 하지 않는다. 필요하면 두 번째 시험에서 exact transposition/AoSoA/block packing을 추가한다.

대조군은 반드시 세 가지다.

- A: 현재 accepted Numba 경로.
- B: 새 memory layout/loop schedule만 적용한 Numba 경로.
- C: B와 같은 알고리즘·layout의 새 backend.

A→C만 비교하면 algorithm/layout의 개선을 framework 덕분이라고 잘못 해석할 수 있다. B가 C와 같거나 더 빠르면 새 dependency를 추가하지 않는 것이 정답이다.

다음 계산 구간은 새 profile을 기준으로 wall ray 또는 GVF gather 중 하나를 선택한다. Remaining NumPy pointwise chain이 큰 경우에만 Halide/MLX/Dr.Jit whole-stage fusion을 추가 조사한다.

## 7. SIMD가 항상 ray를 빠르게 하지는 않는다

같은 SIMD packet 안의 ray 길이가 L_i이고 lane 수가 w이면 대략적인 유효 lane 비율은

    eta = sum(L_i) / (w * max(L_i))

이다. 이것은 간단한 instruction-level 모델이며 memory/cache cost를 포함하지 않는다. Early exit 길이가 매우 다르면 넓은 SIMD가 빈 lane을 많이 수행한다. 같은 연산량·instruction cost라는 한정 아래

    s_simd ≈ (w_new * eta_new) / (w_old * eta_old)

를 비교할 수 있다. 기존 Numba가 이미 같은 SIMD 폭을 잘 사용하면 새 compiler의 이론적인 폭 이득은 거의 없다. Ray를 비슷한 길이로 묶는 경우에도 grouping/gather/scatter 비용과 exact per-pixel order를 포함해야 한다.

## 8. 조건부 speedup과 목표 처리량

같은 전체 batch 조건에서 새 backend가 바꾸는 disjoint time fraction을 f, 그 구간의 speedup을 s, 새 conversion/sync/JIT overhead를 baseline 시간으로 나눈 값을 delta라 한다.

    remaining_time_ratio = 1 - f + f/s + delta
    total_speedup = 1 / remaining_time_ratio

이는 scenario model이지 관측값이 아니다. f는 현재 accepted source의 실제 batch에서 측정해야 한다. 이전 v5 profile을 사용하지 않는다. 서로 겹치는 savings를 곱하지 않는다.

| f | s | delta | 전체 speedup | 가상의 기존 60분일 때 |
|---:|---:|---:|---:|---:|
| .2 | 2 | .03 | 1.075 | 55.8분 |
| .6 | 2 | .03 | 1.370 | 43.8분 |
| .6 | 3 | .03 | 1.587 | 37.8분 |
| .8 | 4 | .05 | 2.222 | 27.0분 |
| .6 | 8 | .08 | 1.802 | 33.3분 |
| .8 | 8 | .08 | 2.632 | 22.8분 |
| .6 | 1.1 | .05 | 1.005 | 59.7분 |

8배 kernel 사례는 GPU를 포함한 가상 sensitivity다. 어떤 framework에서도 실제 그 배수를 얻었다는 의미가 아니다.

전체 목표 speedup S에 필요한 kernel speedup은

    s >= f / (1/S - 1 + f - delta)

이며 denominator가 양수여야 한다. f=.6, delta=.03으로 전체 2배를 얻으려면 kernel은 약 8.57배여야 한다. 같은 범위로 전체 4배는 불가능하다. f=.8, delta=.05이면 전체 2배에 kernel 3.2배가 필요하다.

실제 원래 목표는 24 spatial tiles / 1800 seconds = 0.8 tiles/minute다. 현재 v6의 실제 24타일 baseline은 없으므로 이 문서에서 절대 달성시간을 예측하지 않는다.

CPU capacity, actual DRAM bandwidth, disk output 및 critical path가 각각 하한을 만든다. More workers, native SIMD와 GPU offload의 효과를 동일 자원에서 겹쳐 세지 않는다.

JIT build 비용 J와 타일당 이득 d, bridge overhead b의 손익분기점은 d>b일 때 K>J/(d-b)이다. Persistent workers와 compiled-cache reuse는 이를 낮출 수 있지만 cache/profile identity 검증을 유지한다.

## 9. 메모리와 GPU 보조 경로

1024², 153 patches 기준:

- float32 raster 한 장: 4MiB.
- visibility 3개 dense cube: 1836MiB.
- 같은 3개 채널이 모두 1-bit이면: 57.375MiB.
- 모두 2-bit이면: 114.75MiB.
- 10종 float32 출력 ×24시점: 타일당 960MiB payload.
- 24타일의 해당 출력 payload: 22.5GiB.

새 framework가 편리하다는 이유로 모든 visibility를 dense cube로 만들거나 모든 타일을 graph에 유지하면, 기존 메모리 최적화를 잃는다. Compact storage + bounded decode/compute block + timestep streaming을 유지한다.

Apple unified memory도 allocation, cache coherence, NumPy bridge와 GPU synchronization 비용을 없애지 않는다. GPU를 쓸 때는 가능한 stage를 device에서 연속 실행하고 최종 저장/체크포인트 경계에서만 host로 돌린다. 매 patch 또는 매 ray step마다 framework/device 경계를 넘기는 구조는 피한다.

하지만 초기에는 geometry와 scalar SLEEF 준비를 CPU에 남겨 exactness를 줄여 시험하는 것이 합리적이다. 이 경우 옮길 수 있는 f가 작아져 전체 speedup 상한도 낮아진다는 사실을 그대로 보고한다.

## 10. 작게 비교하고 최종에만 크게 검증한다

1. 현재 branch의 실제 HEAD, source/wheel/profile/dependency를 pin한다. 기존 rejected fusion/decoder OFF 상태도 기록한다.
2. 64–256² actual kernel/chronology에서 current residual을 확인하고 actual thread count를 기록한다.
3. longwave 한 구간에 A/B/C 대조를 만든다. initial independent tracks는 ISPC(또는Highway), Dr.Jit LLVM, PoCL CPU다. MLX/Halide는 pointwise residual이 충분할 때만 추가한다.
4. Matched inputs/layout, same CPU budget, no new contraction, full state/mask/metadata 검사를 통과한 후보만 stage와 small multi-tile timing으로 올린다.
5. Compilation/tracing, cold-first-use, warm kernel, adapter/transfer, I/O 포함 total을 분리 기록한다. Lazy/async API는 완료 synchronization을 timing에 포함한다.
6. 독립 작업은 병렬 agent에게 맡길 수 있으나, 수치 benchmark host는 한 owner가 독점한다. Runtime thread pools의 합과 memory queue를 제한한다.
7. 효과 없는 backend는 종료하고 Numba를 유지한다. 최종 combined source에서만 실제 24 spatial tile 목표를 한 번 검증한다. 데이터가 없으면 목표는 미검증이다.
8. 현재 `perf/cpu-optimization`에서 계속하며 자동 push/merge/CI broad matrix를 수행하지 않는다. 이 문서는 실제 실행 지시가 아니라 비교 설계다.

현재 cylinder demand가 module-global 상태인 점도 확인했다. 독립 tile simulation을 같은 Python process의 concurrent threads로 바꿀 경우 별도 격리/동시성 검증이 필요하다. Native kernel 내부의 thread 병렬성과 Python tile-call 병렬성은 구별한다.

## 11. 출처

### 프로젝트 소스 및 증거 (고정 commit)

- https://github.com/AlanSynn/solweig-light/tree/4689421c81a9dc9ad5e047bd7ff1dcdd704483b9
- https://github.com/AlanSynn/solweig-light/blob/4689421c81a9dc9ad5e047bd7ff1dcdd704483b9/optimization_v6_continue/evidence/handover/HANDOVER_C6-103.md
- https://github.com/AlanSynn/solweig-light/blob/4689421c81a9dc9ad5e047bd7ff1dcdd704483b9/src/solweig_light/radiation/cylinder_longwave.py
- https://github.com/AlanSynn/solweig-light/blob/4689421c81a9dc9ad5e047bd7ff1dcdd704483b9/src/solweig_light/radiation/engine.py

### 프레임워크 공식 문서 및 구현 (2026-09-21 열람, moving docs는 설치 version과 재확인)

- https://ml-explore.github.io/mlx/build/html/install.html
- https://ml-explore.github.io/mlx/build/html/usage/compile.html
- https://ml-explore.github.io/mlx/build/html/usage/precision.html
- https://github.com/ml-explore/mlx/blob/main/mlx/backend/cpu/compiled.cpp (observed blob f5b516e44b53648fa7b3224a1bd33c521861c54c)
- https://github.com/ml-explore/mlx/blob/main/mlx/backend/cpu/jit_compiler.cpp (observed blob 530637e551d437838f3c40d1f0e39f089807aecb)
- https://drjit.readthedocs.io/en/latest/cflow.html
- https://drjit.readthedocs.io/en/latest/optim.html
- https://drjit.readthedocs.io/en/latest/reference.html
- https://drjit.readthedocs.io/en/latest/interop.html
- https://drjit.readthedocs.io/en/latest/bench.html
- https://ispc.github.io/ispc.html
- https://github.com/google/highway
- https://halide-lang.org/
- https://halide-lang.org/docs/api/generated/Target.html
- https://portablecl.org/
- https://portablecl.org/docs/html/using.html
- https://documen.tician.de/pyopencl/
- https://registry.khronos.org/OpenCL/specs/unified/html/OpenCL_C.html
- https://developer.apple.com/opencl/
- https://github.com/AdaptiveCpp/AdaptiveCpp/blob/develop/doc/installing.md
- https://kokkos.org/kokkos-core-wiki/API/core/execution_spaces.html
- https://github.com/taichi-dev/taichi
- https://docs.taichi-lang.org/docs/global_settings
- https://github.com/spcl/dace
- https://docs.jax.dev/en/latest/installation.html
- https://docs.jax.dev/en/latest/faq.html
- https://pythran.readthedocs.io/en/latest/
- https://cython.readthedocs.io/en/latest/src/userguide/parallelism.html
- https://arrayfire.org/docs/index.htm
- https://futhark.readthedocs.io/en/latest/man/futhark.html
- https://iree.dev/
- https://tvm.apache.org/docs/arch/
- https://juliagpu.github.io/KernelAbstractions.jl/stable/
- https://shader-slang.org/
- https://numba.readthedocs.io/en/stable/user/performance-tips.html
