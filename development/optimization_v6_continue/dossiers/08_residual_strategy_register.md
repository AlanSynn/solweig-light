# D08: extended residual candidates, with activation and rejection rules

The earlier 48 candidates plus 8 quarantined families remain under reference/. This current shortlist adds source-specific details and prevents repeating work already completed. New work is activated by a remaining measured service demand, not by the availability of unlimited model tokens.

| ID | Candidate | Exactness / activation requirement | Main cost model / stop condition |
|---|---|---|---|
| C01 | Common numerical geometry key | D02, complete producer identity/equivalence | Delete one G, not all cold E/I. |
| C02 | Split export and numerical provenance | Complete dependencies retained, versioned schema | Avoid false numerical cache misses; do not trust old payloads. |
| C03 | Native geometry phase precompute | D04 sorted public effects/barrier | KG/Wg + serial export remains. |
| C04 | Parallel staged export + ordered commit | D04 failure frontier, bounded disk | Only if E dominates and disks tolerate concurrency. |
| C05 | Stage memory admission | Raw fallback/native/parent overlap accounted | Capacity may unlock W; RSS not a universal bound. |
| R01 | Anisotropic Lside demanded nodes | D03 errors/warnings preserved | Remove dead weights, four multiplies remain. |
| R02 | Cylinder longwave projection | Main 0..9 state independent of cardinal | Both primary sweeps remain; no isotropic replacement. |
| R03 | Cylinder shortwave scratch | Seven final fields unchanged | 20 to 4 local columns, not 5x full stage. |
| R04 | Exact coefficient finite-state tables | Original intermediate dtypes, separate additions | CP setup + NP lookups; poor if lookup dominates. |
| R05 | Exact tan32(asvf) tile lifetime | Owned immutable and same profile domain | +4N bytes; reject if admission penalty exceeds saved math. |
| R06 | Scalar coefficient preparation | Preserve scalar-origin promotion | Small O(P*T) overhead removal, not dominant by default. |
| R07 | Exact ASVF/signature interning | Complete input bit equality, U census | UPT evaluations + NPT scatter; reject U~N. |
| R08 | Certified classifier interval | Bound actual implemented float function | Compare + uncertain fraction q*old; no unproved monotonic threshold. |
| R09 | Compiled ordered aniLum | Same diffsh independent/public fallbacks | Reduce patch extraction/temporaries; no pre-summed weights. |
| D01 | Prepared multi-channel decoder | D06 immutable owner/range/error order | Reduce entry/descriptor calls, not guaranteed decoder arithmetic. |
| D02 | Microtile/transposition/batch decode | Retained reducer and payload bits | Locality vs workspace; do not revive P01 unchanged. |
| G01 | Actual GVF expression hoist | D05 first/later water + alias domain | 18 repetitions to 1/2; not whole-stage 18x. |
| G02 | Typed block postprocess | D05 exact denominators/casts/order | Eliminate helper/temporary overhead. |
| G03 | Gather + postprocess local storage | Diagnostic reference retained | 16 receiver planes need not leave a block/registers. |
| G04 | Static nosh/cardinal fields | Full invariant dependency graph | +20N bytes; build + read < repeated cost. |
| G05 | Prefix and repeated-add replay | Canonical masks, exact edge history, bounded sums | Original wall terms continue after ground blocker. |
| G06 | Exact emission material/thermal classes | Equal full source-state tuple, not just material ID | U expression evaluations + N scatter; avoid float reassociation. |
| S01 | One-pass stored export verification | D07 full CRC/schema/values/error precedence | Delete repeated decompression/reencoding, not checks. |
| S02 | Lazy required wind coefficients | Validate all required files/shapes first; exact selected bin | Keep only required/current planes; schema errors still observed. |
| S03 | Reuse timezone/small forcing setup | Complete location/date/UTC/profile keys | Never assume same tile center or identical solar hours. |
| S04 | Workspace-backed pointwise finish | Original masks/ownership/typed operations | Fuse temporary creation, not WBGT model/polynomial. |
| S05 | UTCI exact DAG partial evaluation | Original polynomial order, scalar forcing | Horner already failed; no coefficient refitting. |
| S06 | JIT/warm resources for phase workers | Separate cache identity, actual thread caps | Share imports/JIT per worker, no unbounded scene retention. |
| S07 | Ray suffix certificate and existing parallel dispatch | Current R01 already present; wall vs sky proof separate | Count remaining eligible samples; no arbitrary maximum distance. |
| S08 | Native visibility block-local mode | Raw bits fallback, versioned native format | Reduces exceptional patch raw blowup only if observed. |
| S09 | Compact exact payload/signature dedup | Exact byte equality + owner lifetime | Low duplication makes hashing/scatter a regression. |
| S10 | Deterministic longest-work-first internal queue | Public order/failure contract retained | Reduces batch tail, not total numerical work. |
| S11 | Stable snapshot hashing reuse | Complete immutable snapshot semantics | Do NOT replace repeated externally mutable InputGuard with mtime. |
| S12 | Reuse identical durable checkpoint payload | Current S07 already changed digests; don't redo it | Read/hash/CRC/recovery guarantee remains; lower priority unless I/O residual. |
| S13 | Cold wall/aspect residual compilation/layout | Preserve filters, tie order/borders | Only if walls still consume measurable cold service. |

## Deliberately excluded from automatic implementation

No reduced sky/ray/model resolution, skipped night/state transitions, vegetation simplification, FFT/prefix-sum reassociation, low-rank factorization, surrogate or interpolated lookup, unproved no-vegetation wrapper substitution, default-math-profile change, altitude renormalization, unchecked finite-domain theorem, checkpoint interval change, disabled validation or new GPU/offload claim. These need separate user scope even when attractive over real arithmetic.

Do not silently turn `sun_term + shade_term` into one term when their scalar inputs happen to match: equality/NaN masks and intermediate rounding may differ. Do not skip a zero coefficient contribution before proving signed-zero and 0*Inf/NaN behavior. Do not parallelize hours because the state transition looks affine; machine recurrence order is part of the contract.

## Selection score

Rank candidates by expected removed bottleneck service divided by implementation+proof+validation critical-path effort. Correct for admitted input coverage, added build/read cost, memory-induced worker reduction and interactions. If two variants remove the same operations, recompute a combined demand graph instead of multiplying their speedups. Select one or two concrete variants per family for initial timing; unlimited inference may reject many alternatives on paper without expensive numerical executions.
