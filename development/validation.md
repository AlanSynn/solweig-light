# Validation

Choose checks around the behavior being changed. The
[numerical contract](../docs/compatibility.md#numerical-contract) defines
acceptance rules, while [provenance](../docs/provenance.md) explains the
reference environments and limits of existing evidence.

## Choose relevant checks

| Changed behavior | Useful starting points |
| --- | --- |
| Public arguments, CLI and compatibility forwarding | [API](../tests/unit/test_public_api.py), [CLI](../tests/unit/test_cli.py), [compatibility](../tests/unit/test_compatibility.py) |
| Geometry, radiation and numerical dispatch | [Geometry references](../tests/differential/test_geometry_reference.py), [radiation references](../tests/differential/test_radiation_reference.py), and the affected family in [differential tests](../tests/differential/) |
| Complete own-met execution and carried state | [Runtime pipeline](../tests/integration/test_runtime_pipeline.py), [pipeline references](../tests/differential/test_pipeline_reference.py), [state resume](../tests/differential/test_state_resume.py) |
| Cache, persistence and resource ownership | [Geometry cache](../tests/unit/test_geometry_cache.py), [persistence](../tests/unit/test_persistence.py), [runtime](../tests/unit/test_runtime.py) |
| Independent scientific expectations | [Official UTCI](../tests/scientific/test_utci_independent.py), [UMEP ground view](../tests/scientific/test_umep_ground_view_independent.py), [UMEP delay](../tests/scientific/test_umep_delay_independent.py), and [analytic checks](../tests/scientific/) |

Start with the affected tests, then exercise the surrounding workflow when a
change crosses its boundaries. A numerical leaf comparison cannot establish
checkpoint or TIFF behavior. Complete output agreement can also conceal an
intermediate difference, so inspect affected radiation fields, temperature
and delay state as well as final comfort outputs.

For concurrency or persistence changes, select cases that exercise ownership,
block/thread/worker settings, cold and warm caches, corruption and interruption.
The [runtime documentation](../docs/runtime.md) describes the behavior those
checks must preserve.

## Understand the reference

The [frozen field rules](../tests/reference/contracts/comparison_v1.json) are
the numerical acceptance authority. The
[public API snapshot](../tests/reference/contracts/public_api.json) records
the public surface. Keep their meaning separate from an individual test run.

[Reference fixtures](../tests/reference/) retain upstream outcomes with their
source and collection manifests. Generate upstream expectations in an isolated
reference environment; candidate code must never produce its own upstream
golden. Preserve the distinction between original CPU, original CUDA,
explicitly patched upstream and candidate results described in
[provenance](../docs/provenance.md#evidence-classes).

Independent checks use the pinned [UMEP sources](../tests/reference/umep/)
and [official UTCI source](../tests/reference/utci_official/). Their source
bytes, hashes and notices are part of the reference. Manifest paths and
acquisition statuses describe the captured material and may predate its
current location or later test execution.

The [scientific exception policy](../tests/reference/contracts/scientific_exceptions.json)
records a limited disposition for named inherited failures. Their assertions
and failed outcomes remain meaningful; a changed or worsened result requires
investigation. See the [model ledger](../docs/model_deviations.md) for scope
and interpretation.

## Investigate a difference

Locate the first differing intermediate or state transition. Compare shape,
dtype, finite/NaN/infinity masks and categorical values before interpreting
numeric error. Check scalar promotion, operation order, strict classification
boundaries and the state carried from the previous timestep. Reproduce the
relevant execution and cache settings before changing an assertion.

The [exact trace helper](tools/capture_exact_pipeline.py) can record numerical,
checkpoint and optional writer boundaries using a separately supplied
compatible `prepared_job` driver. Its default driver path refers to archived
tooling. The trace hashes every captured value and adds instrumentation cost;
use it for correctness diagnosis. Its helper contracts are exercised by
[trace tests](../tests/unit/test_exact_pipeline_trace.py).

Exact candidate-to-candidate agreement establishes preservation for the
compared sources and workload. Upstream compatibility and independent physical
checks remain separate questions. Report the cases exercised and unresolved
differences with the change; avoid treating a finite fixture set as a proof
for every input or platform.
