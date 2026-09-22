"""Manifest schema validation (N8-20): every required field present,
hashes verify, generation name is content-derived, validator rejects
mutations."""

import copy
import hashlib
import json

import build_native


def test_staged_manifest_passes_validation(staged_generation):
    manifest = json.loads((staged_generation / "manifest.json").read_text())
    assert build_native.validate_manifest(manifest) == []
    # full content verification (hashes, generation name, audit) also passes
    assert build_native.verify_generation(staged_generation) == manifest


def test_documented_top_level_fields_present(staged_generation):
    manifest = json.loads((staged_generation / "manifest.json").read_text())
    for key in ("manifest_version", "build_mode", "package", "abi",
                "kernel", "generated_sources", "toolchain", "build",
                "math_profile", "scalar_profiles", "platform", "artifacts",
                "fma_audit"):
        assert key in manifest, f"manifest lacks documented field {key}"
    assert manifest["build_mode"] == "native-release"
    assert manifest["abi"]["abi_version"] == build_native.ABI_VERSION
    assert manifest["build"]["target"] == "neon-i32x8"
    assert "--opt=disable-fma" in manifest["build"]["ispc_flags"]
    assert manifest["math_profile"]["fma_contraction"] == "disabled"
    assert set(manifest["scalar_profiles"]) >= {"f32", "f64"}
    assert manifest["platform"]["arch"] == "arm64"
    assert manifest["fma_audit"]["passed"] is True


def test_artifact_and_generated_hashes_verify(staged_generation):
    manifest = json.loads((staged_generation / "manifest.json").read_text())
    for entry in manifest["artifacts"] + manifest["generated_sources"]:
        data = (staged_generation / entry["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], \
            f"{entry['path']} does not match its manifest hash"
        assert (staged_generation / entry["path"]).stat().st_size == \
            entry.get("bytes", len(data)) or "bytes" not in entry


def test_generation_name_is_content_derived(staged_generation):
    manifest = json.loads((staged_generation / "manifest.json").read_text())
    assert build_native.generation_name(manifest) == staged_generation.name
    # any content change (except volatile stamps) changes the name
    mutated = copy.deepcopy(manifest)
    mutated["build"]["target"] = "neon-i32x4"
    assert build_native.generation_name(mutated) != staged_generation.name
    stamped = copy.deepcopy(manifest)
    stamped["created_utc"] = "2000-01-01T00:00:00Z"
    assert build_native.generation_name(stamped) == staged_generation.name


def _mutations(manifest):
    def m(fn):
        out = copy.deepcopy(manifest)
        fn(out)
        return out
    return [
        ("drop abi", lambda d: d.pop("abi")),
        ("wrong abi version",
         lambda d: d["abi"].__setitem__("abi_version", 99)),
        ("artifact hash not sha256",
         lambda d: d["artifacts"][0].__setitem__("sha256", "0" * 63 + "g")),
        ("generated-source hash not sha256",
         lambda d: d["generated_sources"][0].__setitem__("sha256", "xyz")),
        ("artifact entry incomplete",
         lambda d: d["artifacts"][0].pop("bytes")),
        ("kernel hash not sha256",
         lambda d: d["kernel"].__setitem__("sha256", "deadbeef")),
        ("fma audit not passed",
         lambda d: d["fma_audit"].__setitem__("passed", False)),
        ("no artifacts in native release",
         lambda d: d.__setitem__("artifacts", [])),
        ("missing toolchain", lambda d: d.__setitem__("toolchain", None)),
        ("missing platform.os", lambda d: d["platform"].pop("os")),
        ("missing math profile id",
         lambda d: d["math_profile"].pop("id")),
    ]


def test_validator_rejects_mutated_manifests(staged_generation):
    manifest = json.loads((staged_generation / "manifest.json").read_text())
    for label, mutate in _mutations(manifest):
        broken = copy.deepcopy(manifest)
        mutate(broken)
        problems = build_native.validate_manifest(broken)
        assert problems, f"validator accepted a manifest with {label}"


def test_source_mode_manifest_validates(tmp_path):
    result = build_native.source_fallback_manifest(
        tmp_path, None, "lw")
    manifest = result["manifest"]
    assert manifest["build_mode"] == "source-no-native"
    assert manifest["artifacts"] == []
    assert manifest["toolchain"] is None
    assert build_native.validate_manifest(manifest) == []
    assert build_native.verify_generation(result["generation_dir"])
