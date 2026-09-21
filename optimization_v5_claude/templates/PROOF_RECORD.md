# Transformation certificate: TASK_ID / STRATEGY_IDS

## Identity
Baseline/candidate commits, dirty-tree hash, source/wheel/profile/dependency and fixture identities. Actual target architecture, rounding mode and native backend.

## Observables
Public returns, requested artifacts and metadata, every carried state, future-neighbor inputs, required mutation/validation/error effects, optional trace outputs.

## Fast domain and guard
State complete input/range/dtype/layout/ownership conditions. Explain why the guard establishes them and its cost. Finite inputs do not automatically imply finite intermediates.

## Typed derivation
Original recurrence/expression DAG; replacement; original intermediate dtypes and rounding; preserved FMA nodes; operation and patch/ray orders. Explain every removed or reused operation.

## State, bounds and exceptions
Induction invariant, first-step/reset conditions, boundary/persistent-sample behavior, all nonfinite/signed-zero cases, index/count bounds. Identify unsupported cases and the unchanged fallback.

## Ownership and cache
Read/write lifetimes, stage barriers, alias behavior, mapped-owner locks, complete cache keys, invalidation and serialization version.

## Falsification
Counterexamples attempted, actual-kernel fixtures, output/state comparisons, compiler/assembly checks and negative-control workload. Distinguish abstract tests from original-kernel and pipeline verification.

## Cost model
Work/bytes/launches removed, added preparation/guard/storage, crossover condition and interaction with other optimizations. Do not present sample-count ratios as stage speedups.

## Executed evidence
Exact commands, outcomes, hashes, failures and retained logs. Missing/unavailable/not-run entries remain explicit. Frozen gates are not changed after failure.

## Independent review and disposition
Reviewer identity, issues, resolution, admitted domain, benchmark result, promotion/rejection/blocker. An implementer cannot approve their own proof.
