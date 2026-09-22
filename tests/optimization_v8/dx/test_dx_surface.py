"""N8-01 executable DX gates: the candidate must match the frozen main contract.

The frozen contract lives in
``optimization_v8_native_default/evidence/dx_baseline/main_surface.json``
(source observation of main pin ``14e888760727583ef782a4dc0e7a5c7c6e6ff9d1``,
captured by AST inspection without execution).  The candidate surface is
captured at runtime from whatever ``import solweig_light`` resolves to.

Package-origin parametrization (reused by N8-23 against an installed wheel):

* ``SOLWEIG_DX_PACKAGE_ORIGIN`` unset or ``inprocess`` - probe the running
  interpreter's ``solweig_light`` (the editable v8 worktree today);
* ``subprocess:<python>`` - probe a fresh interpreter (e.g. a clean venv
  with an installed wheel); the main reference is never imported there.

Any asserted-surface drift must either be listed in
``EXPECTED_BRANCH_DIVERGENCES`` below (with the exact expected branch value
and a reason, cross-checked against the frozen branch source snapshot) or
the tests fail.  Today that allowlist is empty: the v7 native-backend work
diverged only inside private modules and runtime scheduling behavior, which
is documented in ``evidence/dx_baseline/dx_divergences.md`` and invisible at
the signature/defaults/entry-point level.
"""

from __future__ import annotations

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from dx_snapshot import (  # noqa: E402
    BRANCH_SURFACE_PATH,
    MAIN_SURFACE_PATH,
    check_divergences_allowed,
    check_forbidden_core_dependencies,
    capture_runtime_surface,
    capture_runtime_surface_subprocess,
    load_surface,
    surface_divergences,
)

# Documented, accepted main-vs-branch public-surface divergences.
# Schema: {"<dotted.path>": {"expected_candidate": <value>, "reason": "<...>",
#                            "recorded_in": "evidence/dx_baseline/dx_divergences.md#..."}}
EXPECTED_BRANCH_DIVERGENCES: dict[str, dict[str, object]] = {}

# Paths asserted only when the probed environment can see them.
ENVIRONMENT_CONDITIONAL_PATHS = frozenset({"companion_distribution.console_scripts"})


def candidate_surface() -> dict:
    origin = os.environ.get("SOLWEIG_DX_PACKAGE_ORIGIN", "inprocess")
    if origin in ("", "inprocess"):
        return capture_runtime_surface()
    if origin.startswith("subprocess:"):
        return capture_runtime_surface_subprocess(origin.split(":", 1)[1])
    raise ValueError(f"unknown SOLWEIG_DX_PACKAGE_ORIGIN: {origin!r}")


def drift_failures(drift: dict) -> list[str]:
    return check_divergences_allowed(
        drift,
        EXPECTED_BRANCH_DIVERGENCES,
        baseline=load_surface(MAIN_SURFACE_PATH),
        branch_surface=load_surface(BRANCH_SURFACE_PATH),
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )


def test_candidate_runtime_surface_matches_frozen_main_contract():
    """Gate: installed/importable candidate equals the frozen main DX surface."""
    candidate = candidate_surface()
    drift = surface_divergences(
        load_surface(MAIN_SURFACE_PATH), candidate,
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )
    failures = drift_failures(drift)
    failures.extend(check_forbidden_core_dependencies(candidate))
    assert not failures, "candidate DX surface drifted from the frozen main contract:\n" + "\n".join(failures)


def test_frozen_branch_source_divergences_are_allowlisted():
    """Every main-vs-branch source divergence must be explicitly allowlisted."""
    drift = surface_divergences(
        load_surface(MAIN_SURFACE_PATH),
        load_surface(BRANCH_SURFACE_PATH),
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )
    failures = check_divergences_allowed(
        drift, EXPECTED_BRANCH_DIVERGENCES,
        baseline=load_surface(MAIN_SURFACE_PATH),
        branch_surface=load_surface(BRANCH_SURFACE_PATH),
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )
    assert not failures, "frozen branch surface carries undocumented drift:\n" + "\n".join(failures)


def test_block_pixels_default_is_frozen():
    """The main block-size default is captured and unchanged at runtime."""
    frozen = load_surface(MAIN_SURFACE_PATH)
    frozen_fields = frozen["package"]["runtime_options"]["fields"]
    runtime = import_runtime_module()
    options = runtime.RuntimeOptions()
    assert options.block_pixels == frozen_fields["block_pixels"]
    # Same default where the estimate API re-states it independently.
    for function_name in ("estimate_memory", "estimate_tile_memory"):
        frozen_params = frozen["package"]["runtime_functions"][function_name]["params"]
        block_default = next(
            param["default"] for param in frozen_params if param["name"] == "block_pixels"
        )
        assert block_default == frozen_fields["block_pixels"], function_name
    assert options.block_pixels == 128


def import_runtime_module():
    import importlib

    return importlib.import_module("solweig_light.runtime")


def test_comparator_detects_default_drift():
    """Teeth proof: mutating a captured default must fail the comparator."""
    candidate = candidate_surface()
    mutated = copy.deepcopy(candidate)
    fields = mutated["package"]["runtime_options"]["fields"]
    fields["block_pixels"] = fields["block_pixels"] + 1
    drift = surface_divergences(
        load_surface(MAIN_SURFACE_PATH), mutated,
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )
    failures = drift_failures(drift)
    assert failures, "comparator accepted a mutated default; it has no teeth"
    assert any("runtime_options" in failure for failure in failures)


def test_comparator_detects_cli_flag_drift():
    """Teeth proof: removing a CLI flag must fail the comparator."""
    candidate = candidate_surface()
    mutated = copy.deepcopy(candidate)
    options = mutated["package"]["cli"]["options"]
    removed = options.pop("--tile_size")
    assert removed is not None
    drift = surface_divergences(
        load_surface(MAIN_SURFACE_PATH), mutated,
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )
    failures = drift_failures(drift)
    assert failures, "comparator accepted a removed CLI flag; it has no teeth"
    assert any("cli.options" in failure for failure in failures)


def test_undeclared_divergence_is_rejected_without_allowlist_entry():
    """Teeth proof: drift absent from the allowlist is always undocumented."""
    candidate = candidate_surface()
    mutated = copy.deepcopy(candidate)
    mutated["package"]["dunder_version"] = "9.9.9"
    drift = surface_divergences(
        load_surface(MAIN_SURFACE_PATH), mutated,
        skip_paths=ENVIRONMENT_CONDITIONAL_PATHS,
    )
    failures = drift_failures(drift)
    assert failures and any("UNDOCUMENTED" in failure for failure in failures)


def test_frozen_snapshots_are_labelled_source_observations():
    """The main/branch records must stay source observations, never runtime."""
    for path in (MAIN_SURFACE_PATH, BRANCH_SURFACE_PATH):
        surface = load_surface(path)
        assert surface["evidence_class"] == "source_observation", path
        assert surface["capture_method"].startswith("python-ast"), path
        assert surface["git_commit"], path
        assert surface["package"]["workflows"], path


if __name__ == "__main__":  # pragma: no cover - direct execution convenience
    raise SystemExit(pytest.main([__file__, "-q"]))
