# Native default promotion, fixed before new candidate results

## Three separate decisions

1. **Arithmetic admitted:** this implementation is equivalent in a declared domain.
2. **Worth using:** complete region and installed execution improve over both current A and strongest equivalent-layout B under matched budgets.
3. **Default deployable:** ordinary wheel install/call needs no new user action and native execution really occurs.

All three are needed. Old microbenchmarks, theoretical speedups or a successful Numba fallback cannot substitute for any one.

## Baselines

A0 is frozen current accepted Numba at the task's starting source. C0 is old opt-in ISPC, retained as diagnostic regression evidence. B1 is the best newly optimized Numba with the same producer/layout/region as C1. M0 main is frozen DX baseline and separate optional performance comparison. Upstream SOLWEIG-GPU is a separate model/performance oracle. Do not rename A0 as upstream.

## Proposed quantitative gates to freeze at N8-03

These are engineering acceptance thresholds, not observed results. Freeze exactly or justify amendments using baseline noise/cost characterization BEFORE evaluating new candidates, recording a new protocol version. After candidate failures, do not loosen gates.

- Exact supported-domain numerical/metadata/state, full API/DX and memory gates are mandatory.
- Use three alternating paired observations per final selected small held-out cell, not an exhaustive grid. Primary evaluation has at least four predeclared workload/configuration cells covering dense and vegetation scenes plus ordinary defaults and production H/B; use tuning cases only to choose variants.
- Installed auto default must yield geometric mean `A0_time / auto_time >= 1.10` across the declared primary native-eligible cells.
- Each primary cell used in the auto-native allow-list must have paired median `A0_time / auto_time >= 1.05`; every such cell must have paired median `B1_time / auto_time >= 1.05` at the installed region/pipeline boundary. Native-specific value cannot be credited solely to B1's layout.
- No more than 3% paired median regression in a predeclared protected default/fallback cell. A new degraded or noisy cell is removed from auto eligibility only with explicit guard coverage and prior workload-domain policy, not erased from reports. Never shrink the target workload definition to hide a failure.
- Meaningful native coverage: required output has been computed by actual native region on >=80% of PREDECLARED eligible pixel-patch work in a primary cell; overall absolute coverage and fallback workload are reported. Counters must verify actual C execution, not initialization. A mask cache or mixed region needs a defined non-double-counted work unit.
- First-use native library initialization performs no build/download. Cold full-entry guard must not materially regress beyond the predeclared 3% paired bound where valid paired data exists; unresolved host noise means insufficient evidence, not passed.
- A noisy host, memory-pressure interruption, unmatched layout/profile/resource, missing completed pair or synthetic-only default extrapolation invalidates promotion evidence for the affected cell. Preserve censored runs and investigate via small repro before at most one permitted rerun.

These small-sample gates establish local scoped evidence, not a p95 service-level guarantee. A large claimed speedup requires enough evidence for that claim; the design aim of 20-23 minutes is not measured here.

## Default and resource cells

At least one cell executes an ordinary main-compatible call without changing RuntimeOptions or backend env, including default block=128 (verify current main exact defaults). Other cells explicitly pin memory and H/B to matched production budgets, including B=1024 and H=4 if supported. Native planning must fit existing defaults, not change them. If only tuned expert cells win, report native opt-in success and default objective incomplete.

## Certificates

After review and tests, record exact OS/ISA/artifact/compiler/math versions, input/demand/scalar domain, resource limits, covered cells, evidence hashes, actual native coverage, pairs, errors and exclusions in a private policy certificate. It is package-owned and non-executable data. Include rejected/unknown rows as Numba-only. Runtime probes establish capability, not performance certification by themselves.

The packet `tools/promotion_gate.py` validates record shape and policy arithmetic only. It cannot verify a claimed execution or reviewer signature, and it cannot approve production. A separate human/agent independent reviewer must verify raw files and provenance. Packet unit tests use fabricated examples solely to test the tool, never runtime evidence.

## Outcome labels

- `native_development_only`: concrete implementation exists, no default acceptance.
- `numba_improvement_only_native_goal_open`: B wins, integrate it transparently and report native shortfall.
- `local_installed_default_qualified`: required local cells pass and actual default wheel uses native.
- `platform_default_qualified`: named platform's supported deployment scope has been executed and reviewed.
- `actual_target_unverified`: target corpus/reference/time evidence absent; compatible with a local improvement result.
- `actual_24_tile_target_demonstrated_once`: only the exact target workload/resources/reference coverage completed under the frozen time boundary.
- `release_qualified`: broader existing release gates genuinely complete; this packet does not assume that.

Do not turn an unsuccessful task into success by changing the meaning of native, installed default, platform-independent or actual target.
