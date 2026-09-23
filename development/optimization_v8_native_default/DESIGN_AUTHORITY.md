# Fixed design decisions and delegated judgment

## What is fixed by this request

1. Continue the current named branch `perf/native-optimization`; reference pins do not authorize resets.
2. Preserve main-style public DX, seven workflows, existing defaults and CLI spellings, own-met TIFF path, compatibility-distribution separation and no Torch/CUDA dependency in the core.
3. Default native is a **qualified automatic execution policy**, not unconditional ISPC execution. Public arguments stay unchanged. Private runtime planning may change only with observational equivalence and matched resource limits.
4. Prefer removing repeated preparation and whole traversals over another compiler search. Existing native arithmetic, Numba AoSoA and baseline captures are assets, not proof that their wider integration is fast.
5. Compare A=current accepted Numba, B=best equivalent-layout Numba, C=new native. Never credit B's work removal to C's compiler.
6. Preserve the numerical contract, actual dtype graph, original ray support, 153 target patches and chronological state. Approximation, mixed-precision relaxation, different physical constants and output reductions are not authorized.
7. Package native binaries inside the same platform wheel. The automatic user route performs no compilation, remote download, toolchain discovery or source hashing per block. Native absence is not a core dependency failure.
8. Source/editable installations without binaries retain no-extra-toolchain fallback; disclose native availability by installation channel. Do not promise both compiler-free arbitrary source builds and newly generated machine code.
9. Freeze execution artifacts for a workflow. Different numerical engines and compiler/ABI/profile versions must participate in simulation/checkpoint provenance. Do not invalidate pure geometry unnecessarily, and do not remove existing dependency guards casually.
10. Native execution failures after launch must propagate. No hidden retry through Numba over partially written output. A supported fallback is a pre-launch eligibility decision, not an exception blanket.
11. CPU, memory, build and writer resources remain bounded despite unlimited model tokens. One thread-pool owner inside each region. Main runtime options and defaults are not inflated for wins.
12. Small real validation first; final large workload last. Do not repeat the prior seven-slot large campaign for each patch. Record all interrupted or censored runs.
13. No hosted CI triggering/push/main merge/release by this task. Local packaging verification is mandatory for local default-readiness; broader release qualification remains explicitly deferred where unavailable.
14. Judge meaningful speed at installed public entry and full region, not only reducer ms. Freeze PROMOTION_POLICY before seeing new variants.
15. High-level design lives here. GLM/Opus can refine proofs and implementation locally. No mandatory Astra consultation.

## What agents may decide without asking

Choose microblock/layout widths, native call ABI details, a single pool implementation, C ABI versus a thin extension if measured necessary, vector target set within supported CPUs, finite guard refinements, smaller adversarial reproductions, exact scheduling/fusion boundaries and task split. Reject a false or slow hypothesis. Repair ordinary implementation bugs and rerun affected small tests. Add source-bound evidence and reviewed commits.

Choose initial platform scope from actual available supported core environments; do not make up Linux or Windows qualification. Freeze the supported policy rows and benchmark controls. A platform can remain Numba-only while another becomes native-default-qualified.

## What requires an explicit exception, not silent action

Changing physical/scientific semantics, widening numeric tolerances, public API/default/schema changes, eliminating required CRC/content verification/checkpoints, backend self-download, external credentials/service access, privileged installations, destructive cleanup, publishing, or changing workload/gates after failure. Record `design_exception.json` and continue unrelated safe tasks. No need to pause the whole project because one backend lacks a compiler or one corpus is absent.

## Evidence classes

`source_observation`; `prior_reported_measurement`; `derived_from_reported_values`; `hypothetical`; `new_kernel_measurement`; `new_region_measurement`; `installed_pipeline_measurement`; `packet_tool_test`; `unavailable`; `failed`. These labels must not be promoted by renaming. Packet examples and helper self-tests never qualify a runtime backend.
