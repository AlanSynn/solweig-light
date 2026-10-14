# S10-14: adversarial input/profile fixtures

Date: 2026-10-14. Branch `perf/s10-semantic-systems`. Deliverable per the
packet DAG: `tests/optimization_s10/fixtures/` +
`fixture_manifest.json` (registry-generated, drift-pinned by
`test_manifest_matches_registry`).

## Fixture set (9 registered)

| id | axis | oracle |
|----|------|--------|
| lcyl_category_invariance | Tgwall typed wrappers, f32/f64 | reference + ndarray-set bit identity |
| dpc_category_invariance | Tgwall typed wrappers (dpc) | reference + ndarray-set bit identity |
| lcyl_nonfinite_u_route | NaN/+Inf/−Inf into Tgwall/Ta/Lup on the admitted U route | mask equality + frozen budgets |
| lcyl_signed_zero | −0.0 vs +0.0 Tgwall | signbit vectors + difference masks |
| lcyl_input_purity_and_alias | caller-buffer mutation; shadow-matrices bound to one shared buffer | input purity + alias-visibility identity |
| gvf_tg_lcgrid_alias | Tg aliasing lc_grid (C6-30 exclusion) | delegation counters + bitwise vs original body under the identical aliased binding |
| gvf_mutation_epoch | in-place Tg/lc_grid mutation between calls | bitwise vs fresh calls per value |
| gvf_nonfinite_tg | NaN/+Inf payloads over the f64 production Tg profile, water path active | bitwise uint64 views incl. payloads |
| anilum_nonfinite_payloads | raw NaN/−0/Inf uint32 payloads | covered by `semantic/test_r03_anilum_packed.py` (recorded, not duplicated) |

Disclosure (VALIDATION_POLICY boundary): seeded-rng synthetic inputs;
expected traces only from the original serial source or stated invariance
identities; no candidate-generated expectations; no numerical mocks;
evidence class `standalone_semantic_probe`.

## Semantic finding recorded by the fixtures

**The admitted singleton bit-identity set is the ndarray wrappers only.**
With identical base arguments, numpy scalar, 0-d, (1,) and (1,1) Tgwall all
give bit-identical primary outputs — but a **Python float** Tgwall (also
admitted, also in budget vs the reference) is ~1 ulp apart from that set on
five of six Lcyl fields. This is the SEMANTIC_CONTRACT caveat "singleton
identity is not scalar execution equivalence" observed at the admitted
boundary; the fixtures pin the partition instead of overclaiming. The
production pipeline constructs Tgwall as ndarray, so no shipped behavior
changes.

The GVF alias fixture also fixed a fixture-level trap worth naming:
snapshotting a scene dict (the shared test helper) silently copies away an
alias, so an alias-exclusion guard can never fire. The fixture aliases the
buffers in the call arguments and lets the oracle reproduce the identical
aliased binding — alias visibility, not content equality.

## Verification

- `tests/optimization_s10/fixtures`: 18/18 (9 registry/parametrized cases).
- Full `tests/optimization_s10`: 58/58 in suite order (no cross-suite
  pollution; route counters read as deltas only).
- Not run here: L2 TIFF goldens — no product code changed in this task.
