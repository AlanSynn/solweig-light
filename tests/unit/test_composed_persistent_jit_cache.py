"""Numerical source upgrades invalidate the reviewed compiled call chains.

These tests deliberately change numerical constants only in owned package
copies. A warm cache must execute those changed semantics exactly like a
fresh cache, even when the imported source keeps its old size and mtime.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import shutil

import pytest

from test_exact_persistent_jit_cache import (
    assert_loaded, assert_saved, cache_names, copy_active_source, run_probe,
)


PROBE = Path(__file__).resolve().parents[1] / "helpers/composed_persistent_jit_cache_probe.py"
CASES = {
    "lw": ("_native_dispatch/lw_b_control.py", "lw_primary_b_serial",
           b"np.float32(.5)", b"np.float32(.4)", 1,
           "_native_dispatch/lw_batch.py", ("_batch", "_batch_serial")),
    "sw": ("_native_dispatch/direct_aosoa.py", "_produce_patchmajor",
           b"0x3f800000", b"0x3f000000", 6,
           "_native_dispatch/sw_batch.py", ("_batch", "_batch_serial")),
    "gvf": ("radiation/gvf_postprocess.py", "_postprocess_pixel",
            b"half = np.float32(0.5)", b"half = np.float32(0.6)", 1,
            "radiation/gvf_batch.py", ("_run",)),
    "svf": ("geometry/svf.py", "_accumulate_patch_f32",
            b"range(3)", b"range(2)", 1, None, ("_accumulate_patch_f32",)),
    "visibility": ("geometry/visibility_compiled.py", "_decode",
                   b"0x3f800000", b"0x3f000000", 1, None, ("_decode", "_decode_diff")),
}


def mutate_function(path, name, old, new, count, *, same_stamp):
    before = path.stat()
    content = path.read_bytes()
    lines = content.splitlines(keepends=True)
    node = next(node for node in ast.parse(content).body
                if isinstance(node, ast.FunctionDef) and node.name == name)
    body = b"".join(lines[node.lineno - 1:node.end_lineno])
    assert len(old) == len(new) and body.count(old) == count
    body = body.replace(old, new)
    changed = b"".join(lines[:node.lineno - 1]) + body + b"".join(lines[node.end_lineno:])
    if not same_stamp:
        # Ordinary upgrades also change Numba's defining-module source stamp.
        changed += b"\n# cache upgrade test\n"
    path.write_bytes(changed)
    if same_stamp:
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = path.stat()
        assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)


@pytest.mark.parametrize("mode", ("lw", "sw", "gvf"))
@pytest.mark.parametrize("same_stamp", (False, True), ids=("ordinary", "same-size-and-mtime"))
def test_imported_numerical_upgrade_matches_fresh_cache(tmp_path, mode, same_stamp):
    check_numerical_upgrade(tmp_path, mode, same_stamp=same_stamp)


def test_svf_numerical_upgrade_rejects_same_stamp_cache(tmp_path):
    check_numerical_upgrade(tmp_path, "svf", same_stamp=True)


def test_visibility_decode_and_lazy_diff_upgrade_reject_same_stamp_cache(tmp_path):
    check_numerical_upgrade(tmp_path, "visibility", same_stamp=True)


def check_numerical_upgrade(tmp_path, mode, *, same_stamp):
    source = copy_active_source(tmp_path / "owned-source")
    package = source / "solweig_light"
    shared_cache = tmp_path / "shared-cache"
    original, _ = run_probe(source, shared_cache, tmp_path / "original", mode,
                            debug=True, probe=PROBE)
    unchanged, warm_debug = run_probe(source, shared_cache, tmp_path / "unchanged", mode,
                                      debug=True, probe=PROBE)
    assert unchanged == original
    relative, function, old, new, count, caller, outer_names = CASES[mode]
    for name in outer_names:
        assert_loaded(warm_debug, name)
    caller_bytes = (package / caller).read_bytes() if caller is not None else None
    old_files = set(cache_names(shared_cache))
    mutate_function(package / relative, function, old, new, count, same_stamp=same_stamp)
    if caller is not None:
        assert (package / caller).read_bytes() == caller_bytes
    changed, debug = run_probe(source, shared_cache, tmp_path / "changed-warm", mode,
                               debug=True, probe=PROBE)
    # A different install path has the same content namespace. Its independent
    # cache is the fresh numerical oracle, with no access to the old binaries.
    relocated = tmp_path / "relocated-source"
    shutil.copytree(source, relocated)
    fresh, _ = run_probe(relocated, tmp_path / "independent-cache", tmp_path / "fresh", mode,
                         debug=True, probe=PROBE)
    assert changed == fresh
    assert changed["outputs"] != original["outputs"], "mutation must change this fixture's result"
    if mode == "visibility":
        for route in ("direct", "diffuse"):
            assert changed["outputs"][route] != original["outputs"][route]
    changed_names = {
        name: qualname for name, qualname in changed["cache_qualnames"].items()
        if qualname != original["cache_qualnames"][name]
    }
    assert changed_names
    for name in outer_names:
        assert any(key.endswith("." + name) for key in changed_names)
    new_files = set(cache_names(shared_cache)) - old_files
    for name, qualname in changed_names.items():
        assert any(qualname in filename for filename in new_files)
        assert_saved(debug, qualname)
        # A second signature may reopen the newly written index in this
        # process. It is the obsolete namespace that must never be loaded.
        obsolete = original["cache_qualnames"][name]
        assert not re.search(rf"loaded from '.*{re.escape(obsolete)}-", debug)
