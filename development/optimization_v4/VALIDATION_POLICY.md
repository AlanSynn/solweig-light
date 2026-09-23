# Lean validation policy: protect semantics, avoid repeated expensive work

## Purpose

This policy replaces v3's proposed test frequency and full-batch repetition schedule at the user's request. It changes *when and how much repeated evidence is collected*, not what a numerical comparison means. Existing frozen tolerances, reference provenance and physical work remain unchanged. Prior experiments are never relabeled as if they used this policy.

Optimize total engineering cost as well as simulation time:

    total effort = useful implementation + selected validation + orchestration + hosted CI

Record actual local validation wall/CPU time, JIT/setup time, artifact I/O, full-batch attempts and hosted runner minutes when available. Unknown charged tokens/minutes are unknown, not zero. Concurrent wall times are not added as if they were serial elapsed time.

## Test ladder

### L0: a counterexample before a large fixture

Use tiny arrays/state machines, exact equality and negative controls for altered expressions, first-step logic, absorption, suffix proofs, signed zeros, raw payloads, nonfinite branches and fallback guards. Array/state sizes should be the minimum that exercises the invariant. These are falsification checks, not production numerical verification.

### L1: actual-kernel differential

Use untouched baseline functions from an isolated environment and the new functions on identical inputs. Default 16-128 pixels per side, including non-square and irregular tails. Preserve every relevant return, mutation, dtype and mask. Short 2-6-step forcing cases are allowed for branch-specific local checks. Do not reduce a function's patch count merely to report a faster kernel; test all 153 ordered patches wherever patch arithmetic is involved. Keep low-level patch-table options already supported by the contract covered selectively.

Long rays can be tested using explicit prepared schedules and small receiver sets *plus* an actual-kernel adversarial fixture. This does not verify the production scheduler by itself. Do not infer a finite-halo proof from a cropped scene; each fixture defines its own original domain. Use 256 only when necessary for a meaningful existing supported geometry case; record why.

### L2: real small chronological pipeline

One canonical 64-128-square scene with 24/48 chronological timesteps must exercise the numerical pipeline through TIFF outputs. Prefer an already verified reference fixture. Add small vegetation/water/wind/UHI/fallback cases only for affected dependencies, retaining all guards and output semantics. A full 24/48-step timeline on a small raster is inexpensive relative to a 1024 case and is not replaced by independent hours.

Compare metadata, masks, intermediate radiation at named boundaries and all carried state at every step. Exercise restart at selected boundaries. Use fixtures with the minimum actually supported dimensions; never pad/alter a failing reference only to hide failure. Once a coherent family patch and integration candidate pass, reuse evidence unless its dependency closure changes.

### L3: choose the portfolio on small data

Default sizes 128 and 256, with at most two competing variants per owned family. The central lab runs one baseline/candidate pair on each selected small fixture in alternating order across fixtures, or one AB/BA pair set for a close comparison. These are diagnostic screening trials, not published statistical speedups. Up to two additional pairs are available for a close decision, not mandatory for every candidate. Predeclare fixtures, cache state, order and decision criteria; retain all results.

Use 2-4 small logical tiles to expose persistent-worker reset, CPU/thread contention and memory admission. At most four chosen resource tuples are explored; no Cartesian product across every thread/worker/block/fixture combination. A 512-square diagnostic probe is exceptional and must state a specific cache, ray, allocation or concurrency hypothesis. It is not a recurring tier.

Instrument a representative small run once; uninstrumented timing is separate. Reuse its fixture/kernel input captures while their identity is valid. Aggregate counters rather than retaining per-pixel logs. Large-target headers/manifest inspection is allowed but not repeated target simulation.

### L4: final scale only

Only the final evidence owner, after selected family reviews and final source/wheel freeze, executes the primary actual 24 x 1024-square batch. Default candidate trials: **one**. This is a first complete scale check and target observation, not a confidence distribution. No separate mandatory 1024 warmup, no 1024 run per worker, family or commit, and no automatic secondary large regime.

Reuse retained matching numerical references. No new full baseline by default. A missing reference can justify one final frozen-baseline capture if recorded before candidate evaluation; otherwise disclose that full-scale numerical parity is unverified. An absolute measured runtime does not require rerunning original upstream. An upstream/default/tuned speedup claim does require matching evidence; if unavailable, make no such claim.

A second full candidate attempt is reserved for a demonstrated corrective patch after a retained failed/censored run. Source freeze and affected L0-L2 evidence must be renewed. A noise-related unchanged retry is not automatic. Further campaigns are outside this lean budget. Record unachieved targets rather than endlessly retrying.

## Selecting tests and reusing results

Select once per coherent behavior change using a conservative dependency map. Include source transitive imports/generated kernels, guard/fallback code, constants/math profile, signatures, test harness and comparison rules, fixture/reference bits, compiler/dependency versions, OS/architecture and relevant thread/block/layout/cache settings. Add input mutation policy and runtime resource/exception behavior where relevant.

An evidence key is a digest of that complete declared dependency identity. Store its selection and invalidation reason. A previous passing test with the same verified key may be reused with its original provenance. Documentation/status-only edits normally do not trigger numerical reruns. Packaging changes trigger installed import/API checks. A numerical change triggers its actual-kernel and downstream small-state/output checks. A shared math/runtime change has broad dependencies. If closure is uncertain, rerun the relevant small family/integration set; never rely only on a filename or Git diff without transitive analysis.

A reviewer consumes valid logs and hashes rather than rerunning every worker command. The integrator runs only new interactions, not each already verified experiment from scratch. Stable wheel/cache reuse is allowed only when identity matches; no stale installed package or JIT cache may masquerade as changed source. CI status on the current PR is still independently required if branch protection says so.

Maintain `templates/VALIDATION_LEDGER.json`: executed, reused, not_selected, deferred, blocked, failed, timeout, passed are distinct. Deselection is explicit scheduling, not an unconditional pytest skip inserted into a failing test. Do not delete failure fixtures or loosen gates.

## Cost controls

The JSON policy includes suggested per-command watchdog caps, not speed promises. Calibrate them on baseline **small** fixtures before selection. The default caps cover L0 60 s, L1 180 s, L2 300 s, L3 session 600 s; one cold JIT/setup event has its own recorded allowance. Include setup in first-use metrics; separating the allowance does not hide time. Fixed limits that cannot accommodate an essential check produce an explicit blocked/timeout outcome, not a pass or silent omission.

Stop a full primary attempt at the frozen resource/deadline rule; keep partial outputs separate from complete artifacts. Cancellation cleanup may exceed the model's 1800-second target, but that cannot turn a timeout into success. All runtime-required hashing/checkpoint/publication belongs to application timing. Independent post-run differential comparisons belong to the separately reported validation budget.

No background validation daemons, repeated environment creation, blanket `pytest` after each change, continuous benchmark loops or hosted-CI polling. No lower numerical precision or reduced final work to fit the budget.

## Claim and release boundaries

Passing all small tests establishes only the covered small domains. Large scaling remains unverified until L4. One complete L4 observation establishes only that run and its checked outputs, not reliability or a paired speedup distribution. Preserve all old scientific failure dispositions. Broad platform/original-upstream/large-shape release qualification can remain deferred without blocking delivery of an honestly scoped optimization branch for review. It cannot be labeled release-complete.
