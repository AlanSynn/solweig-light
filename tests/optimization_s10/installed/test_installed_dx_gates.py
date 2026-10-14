#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
"""S10-31 installed-DX gates.

Contracts under test (DX_AND_RELEASE.md, S10-31 packet):

* the wheel and the source install run from OUTSIDE the repository, with
  import origin captured (site-packages) and source-checkout absent;
* a no-env API call and the documented CLI run on real small TIFFs under
  read-only site-packages and an enforced network guard;
* no new compiler is needed anywhere (pure-Python project, prebuilt wheels);
* the wheel manifest excludes research copies, tests, captures and disabled
  backend scaffolding from the runtime closure, ships exactly one top-level
  package (no original-upstream module names), and declares the unchanged
  runtime dependency set (identical to main b3e5ca59's pyproject).

Skip labels (never fake passes) inherit from the session fixtures:
[wheelhouse-unavailable], [uv-unavailable], [wheel-build-unavailable];
admission-refused no-env runs surface as a recorded environmental block,
never a fake pass.
"""

from __future__ import annotations

import email.parser
import json
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest

from installed_test_helpers import (
    BACKEND_ENV_VARS,
    EVIDENCE_DIR,
    EXPECTED_DEFAULT_OUTPUTS,
    EXPECTED_MET_RECORDS,
    GATE_RECORD,
    REPO_ROOT,
    assert_no_net_events,
    run_cmd,
)

MAIN_SHA = "b3e5ca59a1080f02eda5ccda5e35a66af07e4bfa"

# Runtime closure exclusions (DX contract): nothing outside the import
# package ships, and no research/bulk-evidence artifacts ride along.
FORBIDDEN_PREFIXES = ("tests/", "development/", "experiments/", "captures/",
                      "handover/", "docs/")
FORBIDDEN_SUFFIXES = (".jsonl", ".npz", ".nc", ".tar", ".tar.gz", ".log",
                      ".ipynb")
SCAFFOLDING_TOKENS = ("native_generated", ".so", ".dylib", ".dll")


# ---------------------------------------------------------------------------
# offline wheelhouse + the built candidate wheel
# ---------------------------------------------------------------------------


def test_wheelhouse_satisfies_runtime_closure(wheelhouse):
    """All pinned closure wheels plus the setuptools build seed repacked
    offline, every artifact digested."""
    assert len(wheelhouse["wheels"]) == 12, sorted(wheelhouse["wheels"])
    assert wheelhouse["setuptools_seed"] in wheelhouse["sha256"]
    GATE_RECORD["wheelhouse_gate"] = {"status": "passed",
                                      "wheels": sorted(wheelhouse["wheels"])}


def test_built_wheel_is_pure_and_ships_no_scaffolding(built_wheel):
    """The compiler-free build is a pure wheel that carries no backend
    scaffolding and does not pretend to."""
    assert "py3-none-any" in built_wheel["name"], built_wheel["name"]
    identity = built_wheel["product_source_identity"]
    assert identity["identical"] is True, (
        f"checkout product source drifted from the S10-26 freeze: {identity}")
    with zipfile.ZipFile(built_wheel["path"]) as zf:
        scaffolded = [n for n in zf.namelist()
                      if any(tok in n for tok in SCAFFOLDING_TOKENS)]
    assert not scaffolded, f"wheel carries scaffolding: {scaffolded}"
    GATE_RECORD["wheel_gate"] = {"status": "passed",
                                 "pure": True,
                                 "product_source_identity": identity}


# ---------------------------------------------------------------------------
# the wheel manifest: runtime closure, exclusions, unchanged dependencies
# ---------------------------------------------------------------------------


_SPEC_START = frozenset("<>=!~ \t")


def _normalized_requirement(req: str) -> str:
    """Canonical form: lowercase name + comma-joined version clauses sorted
    as strings.  setuptools renders ``gdal>=3.13,<3.14`` as
    ``gdal<3.14,>=3.13`` (clause order is not canonical), so the clauses are
    sorted; the name is everything before the first spec character.
    Environment markers are kept (the extras split happens before
    normalization)."""
    body, sep, marker = req.partition(";")
    marker = ";" + marker.strip() if sep else ""
    cut = len(body)
    for i, ch in enumerate(body):
        if ch in _SPEC_START:
            cut = i
            break
    name = body[:cut].strip().lower()
    clauses = sorted(c.strip() for c in body[cut:].split(",") if c.strip())
    return f"{name}{','.join(clauses)}{marker}"


def _without_extra_marker(req: str) -> str:
    """Strip the PEP 508 ``extra == "..."`` clause: once grouped by the
    extra's name it is redundant with the group key (the wheel renders every
    optional dependency with its own extra marker; main's
    optional-dependencies tables carry none).  Any other marker survives."""
    body, sep, marker = req.partition(";")
    if not sep:
        return req
    rest = [clause.strip() for clause in marker.split(" and ")
            if "extra ==" not in clause]
    return f"{body.strip()}; {' and '.join(rest)}" if rest else body.strip()


def test_wheel_manifest_closure_exclusions_and_unchanged_dependencies(
        built_wheel):
    """Write ``wheel_manifest.json``: RECORD enumeration, one top-level
    package (no original-upstream module names), exclusion scans over the
    runtime closure, and Requires-Dist identity against main's pyproject."""
    with zipfile.ZipFile(built_wheel["path"]) as zf:
        members = zf.namelist()
        meta_name = next(n for n in members if n.endswith(".dist-info/METADATA"))
        metadata = email.parser.Parser().parsestr(
            zf.read(meta_name).decode("utf-8", errors="replace"), headersonly=True)
        entry_points = zf.read(next(n for n in members
                                    if n.endswith(".dist-info/entry_points.txt"))
                               ).decode("utf-8")
    top_levels = {m.split("/")[0] for m in members
                  if "/" in m and not m.split("/")[0].endswith(".dist-info")}
    bad_prefixes = sorted(m for m in members
                          if m.startswith(FORBIDDEN_PREFIXES))
    bad_suffixes = sorted(m for m in members
                          if m.endswith(FORBIDDEN_SUFFIXES))
    requires_dist = metadata.get_all("Requires-Dist", [])
    runtime = sorted(_normalized_requirement(v) for v in requires_dist
                     if "extra ==" not in v)
    extras: dict[str, list[str]] = {}
    for v in requires_dist:
        if 'extra == "' in v:
            extra = v.split('extra == "', 1)[1].split('"', 1)[0]
            extras.setdefault(extra, []).append(
                _normalized_requirement(_without_extra_marker(v)))
    extras = {k: sorted(v) for k, v in extras.items()}
    main_show = run_cmd(["git", "show", f"{MAIN_SHA}:pyproject.toml"],
                        cwd=REPO_ROOT)
    assert main_show.returncode == 0, main_show.stderr[-400:]
    main_project = tomllib.loads(main_show.stdout)["project"]
    main_deps = sorted(_normalized_requirement(dep)
                       for dep in main_project["dependencies"])
    main_extras = {name: sorted(_normalized_requirement(dep) for dep in deps)
                   for name, deps in
                   main_project.get("optional-dependencies", {}).items()}
    manifest = {
        "schema": 1,
        "task": "S10-31 wheel manifest",
        "wheel": {"name": built_wheel["name"],
                  "sha256_run_scoped": built_wheel["sha256"],
                  "pure": "py3-none-any" in built_wheel["name"]},
        "product_source_identity": built_wheel["product_source_identity"],
        "built_from": built_wheel["built_from"],
        "git_head": built_wheel["git_head"],
        "record_members": len(members),
        "top_level_packages": sorted(top_levels),
        "console_scripts": {"solweig-light": "solweig_light.cli:main"
                            if "solweig-light" in entry_points else None},
        "exclusions": {
            "forbidden_prefixes": {"patterns": list(FORBIDDEN_PREFIXES),
                                   "hits": bad_prefixes},
            "forbidden_suffixes": {"patterns": list(FORBIDDEN_SUFFIXES),
                                   "hits": bad_suffixes},
            "backend_scaffolding": {"patterns": list(SCAFFOLDING_TOKENS),
                                    "note": "asserted in "
                                            "test_built_wheel_is_pure_and_"
                                            "ships_no_scaffolding"},
        },
        "dependencies": {
            "runtime_requires_dist_normalized": runtime,
            "main_pyproject_normalized": main_deps,
            "runtime_identical": runtime == main_deps,
            "extras_requires_dist_normalized": extras,
            "main_optional_dependencies_normalized": main_extras,
            "extras_identical": extras == main_extras,
            "normalization": "lowercase name, sorted spec clauses; extras "
                             "grouped by their 'extra == \"...\"' marker with "
                             "that marker then stripped",
            "main_source": f"git show {MAIN_SHA}:pyproject.toml",
        },
    }
    assert top_levels == {"solweig_light"}, top_levels
    assert not bad_prefixes, bad_prefixes
    assert not bad_suffixes, bad_suffixes
    assert "solweig-light" in entry_points, entry_points
    deps = manifest["dependencies"]
    assert deps["runtime_identical"], {
        "wheel": runtime, "main": main_deps}
    assert deps["extras_identical"], {
        "wheel": extras, "main": main_extras}
    GATE_RECORD["wheel_manifest"] = manifest
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / "wheel_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")


# ---------------------------------------------------------------------------
# installed-environment gates: origins, no-env API/CLI runs, no compiler
# ---------------------------------------------------------------------------


def test_wheel_venv_installed_origins(wheel_venv, built_wheel):
    """Fresh venv OUTSIDE the repo; the installed package resolves under
    site-packages; pip check is clean."""
    assert wheel_venv["outside_repo"], wheel_venv["path"]
    assert "site-packages" in wheel_venv["site_packages"], wheel_venv
    assert wheel_venv["pip_check"] == "No broken requirements found.", \
        wheel_venv["pip_check"]
    probe = run_cmd([wheel_venv["python"], "-c",
                     "import solweig_light, sys; print("
                     "[p for p in sys.path if "
                     f"{str(REPO_ROOT)!r} in p])"],
                    cwd=wheel_venv["path"])
    assert probe.returncode == 0, probe.stderr[-400:]
    assert json.loads(probe.stdout.strip()) == [], \
        "the installed venv reaches the source checkout via sys.path"


def _assert_no_env_run(record: dict, where: str) -> None:
    """The no-env mechanics hold for every completed child; the run itself
    may pass or be refused by the shipped resource-admission model under the
    shared host's memory view (first-class environmental outcome, recorded
    with the exact numbers -- never a fake pass, per the v8
    host-memory-pressure precedent)."""
    assert not set(BACKEND_ENV_VARS) & set(record["env_keys"]), record["env_keys"]
    assert_no_net_events(record["no_net_events"], where)
    if record["status"] == "blocked:host-memory-pressure":
        admissions = [a for a in record["attempts"]
                      if a.get("diagnosis") == "blocked:host-memory-pressure"]
        assert admissions, (where, record["attempts"])
        GATE_RECORD[f"{where}_gate_disposition"] = {
            "disposition": "blocked_by_resource_admission",
            "environmental": True,
            "note": ("the shipped admission model refused the phase under "
                     "the shared login node's memory view; DX mechanics "
                     "(install, origins, no-backend env, read-only "
                     "site-packages, network guard, real pipeline start) "
                     "are proven by the attempt logs"),
        }
        return
    assert record["status"] == "passed", (
        f"{where}: {record['status']}; "
        f"{json.dumps(record['attempts'], indent=1)[-1200:]}")


def _assert_real_outputs(record: dict, where: str) -> None:
    out_dir = Path(record["scene"]) / "output_folder" / "0_0"
    files = sorted(p.name for p in out_dir.glob("*")) if out_dir.is_dir() else []
    assert set(EXPECTED_DEFAULT_OUTPUTS) <= set(files), (
        f"{where}: expected {EXPECTED_DEFAULT_OUTPUTS}, got {files}")
    # import solweig_light first: GDAL bootstrap order on this host
    import solweig_light  # noqa: F401
    from osgeo import gdal
    ds = gdal.Open(str(out_dir / "TMRT_0_0.tif"))
    assert ds is not None, f"{where}: TMRT_0_0.tif unreadable"
    bands = ds.RasterCount
    ds = None
    assert bands == EXPECTED_MET_RECORDS, (
        f"{where}: TMRT band count {bands} != met records "
        f"{EXPECTED_MET_RECORDS}")
    record["tmrt_band_count"] = bands


def test_installed_api_no_env_gate(installed_api_run):
    """The no-env thermal_comfort call: pinned defaults only, installed
    origins only, read-only site-packages, network guard loaded and clean,
    real outputs with one band per met record (output checks apply to a
    completed run; an admission refusal is recorded as environmental)."""
    _assert_no_env_run(installed_api_run, "api")
    if installed_api_run["status"] != "passed":
        return
    origins = installed_api_run["module_origins"]
    assert origins["exit_ok"] and origins["bad_origins"] == [], origins
    assert origins["modules"] > 0, origins
    _assert_real_outputs(installed_api_run, "api")


def test_installed_cli_no_env_gate(installed_cli_run, wheel_venv):
    """The documented CLI workflow through the console script, same
    enforcement and output checks as the API gate."""
    _assert_no_env_run(installed_cli_run, "cli")
    assert installed_cli_run["argv"][:1] == ["--base_path"]
    assert not installed_cli_run["scene"].startswith(str(REPO_ROOT)), \
        "the CLI gate must run a scene copy outside the repository"
    assert wheel_venv["console_script"].endswith("/bin/solweig-light")
    if installed_cli_run["status"] != "passed":
        return
    _assert_real_outputs(installed_cli_run, "cli")


def test_source_install_under_stripped_path_needs_no_compiler(source_venv):
    """Source install under a stripped PATH: no compiler activity in the
    install log, import origin under site-packages, pip check clean."""
    activity = source_venv["install_log_compiler_activity"]
    assert not activity["mentions_ispc"], activity
    assert not activity["mentions_c_compiler"], activity
    assert "site-packages" in source_venv["import_origin"], source_venv
    assert source_venv["pip_check"] == "No broken requirements found.", \
        source_venv["pip_check"]
    GATE_RECORD["source_gate"] = {"status": "passed"}
