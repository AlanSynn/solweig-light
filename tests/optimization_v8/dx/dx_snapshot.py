"""Public DX surface snapshot and drift comparator for the v8 packet.

N8-01 froze the main DX/API/install contract as JSON evidence
(``optimization_v8_native_default/evidence/dx_baseline/``).  This module is
the reusable half of that freeze: it can capture the public surface of a
source tree by AST inspection (no execution; used for the main reference
pin) or of an installed/importable package by runtime introspection (used
for the candidate here and for the installed-wheel gate in N8-23), and
compare the two under an explicit, self-verifying divergence allowlist.

Capture methods are distinguished in the records themselves:
``evidence_class="source_observation"`` (AST) versus
``evidence_class="runtime_introspection"``.  Only the runtime record
executes code, and only code reachable from the package under test; the
main reference is never imported into the candidate environment.

CLI (for regenerating the frozen snapshots)::

    python tests/optimization_v8/dx/dx_snapshot.py capture \
        --tree /path/to/tree --commit <sha> --out surface.json
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

SOURCE_OBSERVATION = "source_observation"
RUNTIME_INTROSPECTION = "runtime_introspection"

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "development/optimization_v8_native_default" / "evidence" / "dx_baseline"
MAIN_SURFACE_PATH = EVIDENCE_DIR / "main_surface.json"
BRANCH_SURFACE_PATH = EVIDENCE_DIR / "branch_surface.json"

# Core dependency substrings the contract forbids in the normal install.
FORBIDDEN_CORE_DEPENDENCY_SUBSTRINGS = (
    "torch", "cuda", "nvidia", "cupy", "jax", "tensorflow", "rocm", "vulkan",
)

# Canonical keys of one CLI option record; AST capture fills absent kwargs
# with the same defaults argparse exposes at runtime.
_CLI_OPTION_TEMPLATE: dict[str, Any] = {
    "default": None,
    "required": False,
    "type": None,
    "action": None,
    "help": None,
    "choices": None,
}


# --------------------------------------------------------------------------
# normalization helpers
# --------------------------------------------------------------------------

def _jsonify(value: Any) -> Any:
    """Convert to JSON-stable structures (tuples become lists)."""
    if isinstance(value, dict):
        return {str(key): _jsonify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _safe_eval(node: ast.AST, env: Mapping[str, Any]) -> Any:
    """Evaluate a literal/restricted expression without executing code.

    Supports constants, collections, arithmetic on constants, and calls to
    ``range``/``tuple``/``list``/``set``/``frozenset``/``dict`` with
    evaluable arguments.  Names resolve only against the provided module
    constant environment.  Anything else is unevaluable and is recorded as
    an ``<expr: ...>`` marker rather than guessed.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_safe_eval(item, env) for item in node.elts)
    if isinstance(node, ast.List):
        return [_safe_eval(item, env) for item in node.elts]
    if isinstance(node, ast.Set):
        return {_safe_eval(item, env) for item in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _safe_eval(key, env): _safe_eval(value, env)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _safe_eval(node.operand, env)
        if isinstance(value, (int, float)):
            return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
    ):
        left, right = _safe_eval(node.left, env), _safe_eval(node.right, env)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
                ast.FloorDiv: lambda: left // right,
                ast.Mod: lambda: left % right,
                ast.Pow: lambda: left ** right,
            }[type(node.op)]()
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        args = [_safe_eval(arg, env) for arg in node.args]
        kwargs = {kw.arg: _safe_eval(kw.value, env) for kw in node.keywords}
        if name == "range" and all(isinstance(a, int) for a in args):
            return list(range(*args))
        if name in {"tuple", "list", "set", "frozenset", "dict"}:
            materialize = {"tuple": tuple, "list": list, "set": set,
                           "frozenset": frozenset, "dict": dict}[name]
            return materialize(*args, **kwargs)
    return _unevaluable(node)


def _unevaluable(node: ast.AST) -> str:
    try:
        text = ast.unparse(node)
    except Exception:  # pragma: no cover - unparse is total for parsed trees
        text = ast.dump(node)
    return f"<expr: {text}>"


# --------------------------------------------------------------------------
# AST (source) capture
# --------------------------------------------------------------------------

def _module_constant_env(tree: ast.Module) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in tree.body:
        target = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target = node.target
            value_node = node.value
        if isinstance(target, ast.Name):
            value = _safe_eval(value_node, env)
            if not isinstance(value, str) or not value.startswith("<expr:"):
                env[target.id] = value
    return env


def _params_from_ast(node: ast.FunctionDef, env: dict[str, Any]) -> list[dict[str, Any]]:
    args = node.args
    params: list[dict[str, Any]] = []

    def add(a: ast.arg, default: ast.AST | None, kind: str) -> None:
        params.append({
            "name": a.arg,
            "kind": kind,
            "default": None if default is None else _jsonify(_safe_eval(default, env)),
        })

    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for arg, default in zip(positional, defaults):
        kind = "POSITIONAL_ONLY" if arg in args.posonlyargs else "POSITIONAL_OR_KEYWORD"
        add(arg, default, kind)
    if args.vararg is not None:
        add(args.vararg, None, "VAR_POSITIONAL")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        add(arg, default, "KEYWORD_ONLY")
    if args.kwarg is not None:
        add(args.kwarg, None, "VAR_KEYWORD")
    return params


def _top_level_functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _resolve_signature(
    name: str,
    functions: Mapping[str, ast.FunctionDef],
    aliases: Mapping[str, str],
    env: dict[str, Any],
    seen: set[str] | None = None,
) -> dict[str, Any] | None:
    seen = seen or set()
    if name in seen:
        return None
    seen.add(name)
    if name in functions:
        return {"params": _params_from_ast(functions[name], env)}
    if name in aliases:
        return _resolve_signature(aliases[name], functions, aliases, env, seen)
    return None


def _parse_file(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _dataclass_fields_from_ast(class_node: ast.ClassDef, env: dict[str, Any]) -> dict[str, Any]:
    """Field name -> default (``None`` when the field has no default).

    Runtime introspection cannot distinguish "no default" from "default is
    None"; both sides therefore normalize to ``None``.
    """
    fields: dict[str, Any] = {}
    for node in class_node.body:
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            continue
        default: Any = None
        if isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "field":
            for keyword in node.value.keywords:
                if keyword.arg == "default":
                    default = _safe_eval(keyword.value, env)
                elif keyword.arg == "default_factory":
                    default = _safe_eval(keyword.value, env)
        elif node.value is not None:
            default = _safe_eval(node.value, env)
        fields[node.target.id] = _jsonify(default)
    return fields


def _cli_from_ast(builder: ast.FunctionDef, env: dict[str, Any]) -> dict[str, Any]:
    options: dict[str, Any] = {}
    required: list[str] = []
    description = None
    version_string = None
    for node in ast.walk(builder):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr == "ArgumentParser":
            for keyword in node.keywords:
                if keyword.arg == "description":
                    description = _safe_eval(keyword.value, env)
        elif node.func.attr == "add_argument" and node.args:
            flag = _safe_eval(node.args[0], env)
            if not isinstance(flag, str):
                continue
            entry = dict(_CLI_OPTION_TEMPLATE)
            for keyword in node.keywords:
                name = keyword.arg
                if name == "default":
                    entry["default"] = _jsonify(_safe_eval(keyword.value, env))
                elif name == "required":
                    entry["required"] = bool(_safe_eval(keyword.value, env))
                elif name == "type":
                    entry["type"] = keyword.value.id if isinstance(keyword.value, ast.Name) \
                        else _unevaluable(keyword.value)
                elif name == "action":
                    entry["action"] = _safe_eval(keyword.value, env)
                elif name == "help":
                    entry["help"] = _safe_eval(keyword.value, env)
                elif name == "choices":
                    entry["choices"] = _jsonify(_safe_eval(keyword.value, env))
                elif name == "version":
                    version_string = _joined_str(keyword.value, env)
            if entry["required"]:
                required.append(flag)
            options[flag] = entry
    return {
        "description": description,
        "required": required,
        "options": options,
        "version_string": version_string,
    }


def _joined_str(node: ast.AST, env: dict[str, Any]) -> str:
    if not isinstance(node, ast.JoinedStr):
        evaluated = _safe_eval(node, env)
        return evaluated if isinstance(evaluated, str) else _unevaluable(node)
    parts: list[str] = []
    for value_node in node.values:
        if isinstance(value_node, ast.Constant):
            parts.append(str(value_node.value))
        elif isinstance(value_node, ast.FormattedValue) \
                and isinstance(value_node.value, ast.Name) \
                and value_node.value.id in env:
            parts.append(str(env[value_node.value.id]))
        else:
            return _unevaluable(node)
    return "".join(parts)


def _toml_project(pyproject: Path) -> dict[str, Any]:
    """Minimal pyproject ``[project]`` reader (stdlib ``tomllib``)."""
    import tomllib

    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    project = data["project"]
    package_data: list[str] = []
    for items in data.get("tool", {}).get("setuptools", {}).get("package-data", {}).values():
        package_data.extend(items)
    return {
        "name": project["name"],
        "version": project["version"],
        "requires_python": project.get("requires-python"),
        "dependencies": list(project.get("dependencies", [])),
        "optional_dependencies": {
            key: list(value) for key, value in project.get("optional-dependencies", {}).items()
        },
        "console_scripts": dict(project.get("scripts", {})),
        "package_data": package_data,
    }


def _env_vars_read_from_tree(src_root: Path) -> dict[str, list[str]]:
    """Map module-relative path -> sorted env var names read from the process."""
    found: dict[str, list[str]] = {}
    literal_names: dict[str, str] = {}
    for path in sorted(src_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str) \
                    and node.targets[0].id.startswith("SOLWEIG"):
                literal_names[node.targets[0].id] = node.value.value
    for path in sorted(src_root.rglob("*.py")):
        names: set[str] = set()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "getenv" and node.args:
                    value = _joined_str_or_name(node.args[0], literal_names)
                    if isinstance(value, str):
                        names.add(value)
                elif node.func.attr == "get" and isinstance(node.func.value, ast.Attribute) \
                        and node.func.value.attr == "environ" and node.args:
                    value = _joined_str_or_name(node.args[0], literal_names)
                    if isinstance(value, str):
                        names.add(value)
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) \
                    and node.value.attr == "environ":
                value = _joined_str_or_name(node.slice, literal_names)
                if isinstance(value, str):
                    names.add(value)
        if names:
            found[str(path.relative_to(src_root))] = sorted(names)
    return found


def _joined_str_or_name(node: ast.AST, literal_names: Mapping[str, str]) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in literal_names:
        return literal_names[node.id]
    return None


def capture_source_surface(tree: Path, commit: str | None = None) -> dict[str, Any]:
    """Capture the public DX surface of a source tree by AST inspection only.

    Nothing under ``tree`` is executed or imported.  Returns a JSON-ready
    record labelled ``source_observation``.
    """
    tree = Path(tree).resolve()
    src_root = tree / "src" / "solweig_light"
    pyproject = _toml_project(tree / "pyproject.toml")
    compat = _toml_project(tree / "compat" / "pyproject.toml")

    init_tree = _parse_file(src_root / "__init__.py")
    runtime_tree = _parse_file(src_root / "runtime.py")
    cli_tree = _parse_file(src_root / "cli.py")

    init_env = _module_constant_env(init_tree)
    runtime_env = _module_constant_env(runtime_tree)

    all_names = init_env.get("__all__") or []
    workflow_functions: dict[str, ast.FunctionDef] = {}
    aliases: dict[str, str] = {}
    for module_path in sorted(src_root.glob("*.py")):
        module_tree = _parse_file(module_path)
        for name, node in _top_level_functions(module_tree).items():
            workflow_functions.setdefault(name, node)
        for node in module_tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and isinstance(node.value, ast.Name):
                aliases[node.targets[0].id] = node.value.id

    workflows = {
        name: _resolve_signature(name, workflow_functions, aliases, init_env)
        for name in all_names
    }

    runtime_all = runtime_env.get("__all__") or []
    runtime_functions_all = _top_level_functions(runtime_tree)
    runtime_functions: dict[str, Any] = {}
    for name in runtime_all:
        signature = _resolve_signature(name, runtime_functions_all, aliases, runtime_env)
        if signature is not None:
            runtime_functions[name] = signature

    runtime_options: dict[str, Any] = {}
    dataclass_records: dict[str, Any] = {}
    for node in runtime_tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        is_dataclass = any(
            (dec.func.id if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
             else getattr(dec, "id", "")) == "dataclass"
            for dec in node.decorator_list
        )
        if not is_dataclass:
            continue
        if node.name == "RuntimeOptions":
            runtime_options = {"fields": _dataclass_fields_from_ast(node, runtime_env)}
        else:
            dataclass_records[node.name] = {
                "fields": _dataclass_fields_from_ast(node, runtime_env),
            }

    surface: dict[str, Any] = {
        "evidence_class": SOURCE_OBSERVATION,
        "capture_method": "python-ast-source-inspection (no execution)",
        "git_commit": commit,
        "tree_path": str(tree),
        "distribution": {
            "name": pyproject["name"],
            "version": pyproject["version"],
            "requires_python": pyproject["requires_python"],
            "console_scripts": pyproject["console_scripts"],
            "dependencies": pyproject["dependencies"],
            "optional_dependencies": pyproject["optional_dependencies"],
            "package_data": pyproject["package_data"],
        },
        "companion_distribution": {
            "name": compat["name"],
            "version": compat["version"],
            "dependencies": compat["dependencies"],
            "console_scripts": compat["console_scripts"],
        },
        "package": {
            "module": "solweig_light",
            "dunder_version": init_env.get("__version__"),
            "all": all_names,
            "workflows": workflows,
            "runtime_options": runtime_options,
            "runtime_all": runtime_all,
            "runtime_functions": runtime_functions,
            "dataclass_records": dataclass_records,
            "cli": {
                "entry": pyproject["console_scripts"].get("solweig-light"),
                **_cli_from_ast(_top_level_functions(cli_tree)["build_parser"], init_env),
            },
        },
        "env_vars_read": _env_vars_read_from_tree(src_root),
    }
    return _jsonify(surface)


# --------------------------------------------------------------------------
# runtime (installed/importable package) capture
# --------------------------------------------------------------------------

def capture_runtime_surface() -> dict[str, Any]:
    """Capture the public DX surface of the importable ``solweig_light``.

    Import-based introspection of whatever ``import solweig_light`` resolves
    to in the running interpreter.  Returns a record with the same schema as
    :func:`capture_source_surface`, labelled ``runtime_introspection``.
    """
    package = importlib.import_module("solweig_light")
    cli_module = importlib.import_module("solweig_light.cli")
    runtime_module = importlib.import_module("solweig_light.runtime")

    metadata = importlib.metadata.metadata("solweig-light")
    scripts = {
        ep.name: ep.value
        for ep in importlib.metadata.entry_points(group="console_scripts")
        if ep.value.startswith("solweig_light.")
    }

    def params_of(function: Any) -> dict[str, Any]:
        return {
            "params": [
                {
                    "name": parameter.name,
                    "kind": parameter.kind.name,
                    "default": None if parameter.default is inspect.Parameter.empty
                    else _jsonify(parameter.default),
                }
                for parameter in inspect.signature(function).parameters.values()
            ],
        }

    workflows = {name: params_of(getattr(package, name)) for name in package.__all__}

    runtime_all = list(getattr(runtime_module, "__all__", []))
    runtime_functions: dict[str, Any] = {}
    dataclass_records: dict[str, Any] = {}
    for name in runtime_all:
        attribute = getattr(runtime_module, name, None)
        if attribute is None:
            continue
        if inspect.isfunction(attribute):
            runtime_functions[name] = params_of(attribute)
        elif dataclasses.is_dataclass(attribute) \
                and attribute is not runtime_module.RuntimeOptions:
            dataclass_records[name] = {
                "fields": {
                    field.name: None if field.default is dataclasses.MISSING
                    else _jsonify(field.default)
                    for field in dataclasses.fields(attribute)
                },
            }

    runtime_options = {
        "fields": {
            field.name: None if field.default is dataclasses.MISSING
            else _jsonify(field.default)
            for field in dataclasses.fields(runtime_module.RuntimeOptions)
        },
    }

    options: dict[str, Any] = {}
    required: list[str] = []
    version_string = None
    parser = cli_module.build_parser()
    for action in parser._actions:  # noqa: SLF001 - argparse introspection
        if not action.option_strings:
            continue
        if isinstance(action, argparse._HelpAction):
            continue  # implicit -h; provided by argparse itself, not the contract
        flag = action.option_strings[0]
        entry = dict(_CLI_OPTION_TEMPLATE)
        if isinstance(action, argparse._VersionAction):
            version_string = action.version
            entry["action"] = "version"
        else:
            entry["type"] = getattr(action.type, "__name__", None)
            entry["action"] = None if action.__class__ is argparse._StoreAction \
                else action.__class__.__name__
            entry["help"] = action.help
            entry["choices"] = _jsonify(action.choices) if action.choices else None
        # argparse's SUPPRESS sentinel behaves as "no default" for the DX surface.
        default = None if action.default == argparse.SUPPRESS else action.default
        entry["default"] = _jsonify(default)
        entry["required"] = bool(action.required)
        if action.required:
            required.append(flag)
        options[flag] = entry

    try:
        compat_metadata = importlib.metadata.metadata("solweig-light-compat")
        companion: dict[str, Any] = {
            "name": compat_metadata["Name"],
            "version": compat_metadata["Version"],
            "dependencies": compat_metadata.get_all("Requires-Dist") or [],
            "console_scripts": {
                ep.name: ep.value
                for ep in importlib.metadata.entry_points(group="console_scripts")
                if ep.value.startswith("solweig_gpu.")
            },
        }
    except importlib.metadata.PackageNotFoundError:
        companion = {"name": "solweig-light-compat", "installed": False}

    return _jsonify({
        "evidence_class": RUNTIME_INTROSPECTION,
        "capture_method": "inspect.signature/dataclasses.fields/argparse/importlib.metadata",
        "package_path": getattr(package, "__file__", None),
        "distribution": {
            "name": metadata["Name"],
            "version": metadata["Version"],
            "requires_python": metadata.get("Requires-Python"),
            "console_scripts": scripts,
            "dependencies": metadata.get_all("Requires-Dist") or [],
        },
        "companion_distribution": companion,
        "package": {
            "module": "solweig_light",
            "dunder_version": package.__version__,
            "all": list(package.__all__),
            "workflows": workflows,
            "runtime_options": runtime_options,
            "runtime_all": runtime_all,
            "runtime_functions": runtime_functions,
            "dataclass_records": dataclass_records,
            "cli": {
                "entry": scripts.get("solweig-light"),
                "description": parser.description,
                "required": required,
                "options": options,
                "version_string": version_string,
            },
        },
    })


def capture_runtime_surface_subprocess(python: str | None = None) -> dict[str, Any]:
    """Capture the runtime surface in a fresh interpreter (wheel-gate ready).

    N8-23 can point ``python`` at a clean venv's interpreter; the child needs
    only this directory importable and never touches the parent's modules.
    """
    driver = (
        "import sys, json; sys.path.insert(0, %r); "
        "from dx_snapshot import capture_runtime_surface; "
        "sys.stdout.write(json.dumps(capture_runtime_surface()))"
        % str(Path(__file__).resolve().parent)
    )
    completed = subprocess.run(
        [python or sys.executable, "-c", driver],
        capture_output=True, text=True, check=True,
    )
    return json.loads(completed.stdout)


# --------------------------------------------------------------------------
# comparison
# --------------------------------------------------------------------------

def _asserted_leaves(surface: dict[str, Any]) -> dict[str, Any]:
    """Subset of a surface record the contract asserts must not drift."""
    package = surface["package"]
    asserted = {
        "distribution.name": surface["distribution"]["name"],
        "distribution.version": surface["distribution"]["version"],
        "distribution.requires_python": surface["distribution"]["requires_python"],
        "distribution.console_scripts": surface["distribution"]["console_scripts"],
        "package.dunder_version": package["dunder_version"],
        "package.all": sorted(package["all"]),
        "package.workflows": package["workflows"],
        "package.runtime_options.fields": package["runtime_options"]["fields"],
        "package.runtime_all": sorted(package["runtime_all"]),
        "package.runtime_functions": package["runtime_functions"],
        "package.dataclass_records": package["dataclass_records"],
        "package.cli.entry": package["cli"]["entry"],
        "package.cli.description": package["cli"]["description"],
        "package.cli.required": sorted(package["cli"]["required"]),
        "package.cli.options": package["cli"]["options"],
        "package.cli.version_string": package["cli"]["version_string"],
    }
    companion = surface.get("companion_distribution") or {}
    if companion.get("console_scripts") is not None:
        asserted["companion_distribution.console_scripts"] = companion["console_scripts"]
    return asserted


def surface_divergences(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    skip_paths: frozenset[str] = frozenset(),
) -> dict[str, dict[str, Any]]:
    """Return ``path -> {baseline, candidate}`` for asserted-leaf drift.

    ``skip_paths`` excludes environment-conditional paths (e.g. the
    companion distribution's entry points, which exist only when the
    opt-in companion package is installed in the probed environment).
    """
    base_flat = _asserted_leaves(baseline)
    cand_flat = _asserted_leaves(candidate)
    drift: dict[str, dict[str, Any]] = {}
    for path in sorted(set(base_flat) | set(cand_flat)):
        if path in skip_paths:
            continue
        if base_flat.get(path, "<missing>") != cand_flat.get(path, "<missing>"):
            drift[path] = {
                "baseline": base_flat.get(path, "<missing>"),
                "candidate": cand_flat.get(path, "<missing>"),
            }
    return drift


def check_divergences_allowed(
    drift: Mapping[str, Mapping[str, Any]],
    allowlist: Mapping[str, Mapping[str, Any]],
    baseline: dict[str, Any] | None = None,
    branch_surface: dict[str, Any] | None = None,
    skip_paths: frozenset[str] = frozenset(),
) -> list[str]:
    """Validate drift against the frozen allowlist; return failure strings.

    Every drift path must be allowlisted with an ``expected_candidate`` value
    matching the observed candidate, a non-empty ``reason``, and - when
    ``baseline``/``branch_surface`` are given - must correspond to a real
    main-vs-branch source divergence at the same path whose branch-side value
    equals ``expected_candidate``.  The allowlist therefore cannot excuse
    drift the branch source does not actually contain, and stale allowlist
    entries whose paths no longer drift are reported.
    """
    failures: list[str] = []
    source_drift = (
        surface_divergences(baseline, branch_surface, skip_paths=skip_paths)
        if baseline is not None and branch_surface is not None else None
    )
    for path in sorted(set(drift) | set(allowlist)):
        if path not in drift:
            failures.append(f"stale allowlist entry {path!r}: candidate no longer drifts")
            continue
        entry = allowlist.get(path)
        if entry is None:
            failures.append(
                f"UNDOCUMENTED DX DRIFT at {path}: baseline="
                f"{json.dumps(drift[path]['baseline'], sort_keys=True)} candidate="
                f"{json.dumps(drift[path]['candidate'], sort_keys=True)}"
            )
            continue
        if not entry.get("reason"):
            failures.append(f"allowlist entry {path!r} has no reason")
        expected = entry.get("expected_candidate", "<missing>")
        if drift[path]["candidate"] != expected:
            failures.append(
                f"DX drift at {path} exceeds allowlist: expected "
                f"{json.dumps(expected, sort_keys=True)}, found "
                f"{json.dumps(drift[path]['candidate'], sort_keys=True)}"
            )
        if source_drift is not None:
            if path not in source_drift:
                failures.append(
                    f"allowlist entry {path!r} is not a main-vs-branch source divergence"
                )
            elif source_drift[path]["candidate"] != expected:
                failures.append(
                    f"allowlist entry {path!r} does not match the branch source value "
                    f"{json.dumps(source_drift[path]['candidate'], sort_keys=True)}"
                )
    return failures


def check_forbidden_core_dependencies(candidate: dict[str, Any]) -> list[str]:
    """Fail if core Requires-Dist strings mention forbidden accelerators."""
    failures = []
    for requirement in candidate["distribution"]["dependencies"]:
        lowered = requirement.lower()
        for token in FORBIDDEN_CORE_DEPENDENCY_SUBSTRINGS:
            if token in lowered:
                failures.append(
                    f"core dependency {requirement!r} contains forbidden token {token!r}"
                )
    return failures


def load_surface(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture", help="capture a source-tree surface to JSON")
    capture.add_argument("--tree", required=True, type=Path)
    capture.add_argument("--commit")
    capture.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "capture":
        surface = capture_source_surface(args.tree, commit=args.commit)
        args.out.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
