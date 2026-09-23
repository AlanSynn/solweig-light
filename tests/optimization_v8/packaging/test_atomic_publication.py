import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)
"""Atomic publication (N8-20): no half-published directory on induced
failure; generations are immutable; corrupted artifacts are detected."""

import copy
import hashlib
import json

import pytest

import build_native


def _producers_ok():
    return {
        "manifest.json": lambda: b'{"manifest_version": 1}\n',
        "lib.dylib": lambda: b"\xcf\xfa\xed\xfe payload",
    }


def test_publish_is_complete_and_leaves_no_temp_dirs(tmp_path):
    target = build_native.atomic_publish(tmp_path, "lw-test-gen",
                                         _producers_ok())
    assert (target / "manifest.json").read_bytes() == \
        b'{"manifest_version": 1}\n'
    assert (target / "lib.dylib").is_file()
    assert [p.name for p in tmp_path.iterdir()] == ["lw-test-gen"], \
        "temp publication dir leaked"


def _exploding_producers():
    def boom():
        raise OSError("simulated mid-publication failure")
    return {"manifest.json": lambda: b"ok", "lib.dylib": boom}


def test_no_half_published_dir_on_induced_failure(tmp_path):
    with pytest.raises(OSError, match="simulated mid-publication failure"):
        build_native.atomic_publish(tmp_path, "lw-broken-gen",
                                    _exploding_producers())
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == [], f"staging polluted after failure: {names}"
    assert not (tmp_path / "lw-broken-gen").exists()


def test_generations_are_immutable(tmp_path):
    build_native.atomic_publish(tmp_path, "lw-fixed", {"a": lambda: b"one"})
    original = (tmp_path / "lw-fixed" / "a").read_bytes()
    with pytest.raises(build_native.GenerationExists):
        build_native.atomic_publish(tmp_path, "lw-fixed",
                                    {"a": lambda: b"two"})
    assert (tmp_path / "lw-fixed" / "a").read_bytes() == original


def test_publish_refuses_path_escape(tmp_path):
    with pytest.raises(build_native.BuildError, match="non-contained"):
        build_native.atomic_publish(tmp_path, "lw-esc", {"sub/x": lambda: b""})


def test_corrupt_kernel_build_fails_clean(driver_proc, tmp_path):
    """A kernel that cannot compile must fail loudly AND leave the staging
    area without a generation or temp directory."""
    try:
        build_native.discover_ispc(None)
    except build_native.ToolUnavailable:
        pytest.skip("[ispc-unavailable]")
    bad_kernel = tmp_path / "not_a_kernel.ispc"
    bad_kernel.write_text("this is not ispc source $$\x01\n")
    staging = tmp_path / "stage"
    proc = driver_proc(["build", "--kernel", str(bad_kernel),
                        "--staging", str(staging)])
    assert proc.returncode == 4, proc.stderr
    assert "BUILD FAILED" in proc.stderr
    assert not staging.exists() or list(staging.iterdir()) == [], \
        f"failed build polluted staging: {list(staging.iterdir())}"


def _fake_generation(tmp_path, staged_generation, *, rehash, truncate):
    """Clone the proof generation with a tampered artifact.

    rehash=True records the TAMPERED content hash (manifest consistent,
    image invalid); rehash=False keeps the original hash (content visibly
    modified). Returns the dir for verify_generation to reject."""
    manifest = json.loads((staged_generation / "manifest.json").read_text())
    artifact_entry = manifest["artifacts"][0]
    real = (staged_generation / artifact_entry["path"]).read_bytes()
    tampered = real[:len(real) // 2] if truncate else real + b"x"
    entry = copy.deepcopy(artifact_entry)
    entry["bytes"] = len(tampered)
    entry["sha256"] = (hashlib.sha256(tampered).hexdigest() if rehash
                       else artifact_entry["sha256"])
    manifest["artifacts"] = [entry]
    gen_name = build_native.generation_name(manifest)
    gen_dir = tmp_path / gen_name
    gen_dir.mkdir()
    (gen_dir / "manifest.json").write_text(json.dumps(manifest))
    for entry_ in manifest["generated_sources"]:
        (gen_dir / entry_["path"]).write_bytes(
            (staged_generation / entry_["path"]).read_bytes())
    (gen_dir / artifact_entry["path"]).write_bytes(tampered)
    return gen_dir


def test_verify_rejects_hash_mismatch(tmp_path, staged_generation):
    gen_dir = _fake_generation(tmp_path, staged_generation, rehash=False,
                               truncate=True)
    with pytest.raises(build_native.VerifyFailure, match="hash mismatch"):
        build_native.verify_generation(gen_dir)


def test_verify_rejects_corrupt_image_even_with_matching_hash(
        tmp_path, staged_generation):
    # content hash matches the manifest, but the dylib was truncated in
    # place: not a valid Mach-O image -> corrupt-artifact, loud failure
    gen_dir = _fake_generation(tmp_path, staged_generation,
                               rehash=True, truncate=True)
    with pytest.raises(build_native.VerifyFailure,
                       match="truncated or corrupt"):
        build_native.verify_generation(gen_dir)


def test_verify_rejects_wrong_generation_name(tmp_path, staged_generation):
    gen_dir = _fake_generation(tmp_path, staged_generation, rehash=False,
                               truncate=False)
    renamed = gen_dir.parent / "lw-forged-name"
    gen_dir.rename(renamed)
    with pytest.raises(build_native.VerifyFailure,
                       match="generation name mismatch"):
        build_native.verify_generation(renamed)
