import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)
"""Wheel tagging rules (N8-20): checked on synthetic filenames and WHEEL
metadata text -- no real wheels, no network."""

import pytest

from wheel_tags import WheelTagError, check_wheel_tags, parse_wheel_filename

NATIVE_OK = [
    # C-ABI lib, no Python C API: generic py3 + real platform tag is legal
    "solweig_light-0.1.0.dev0-py3-none-macosx_26_0_arm64.whl",
    # interpreter-specific tag is also acceptable
    "solweig_light-0.1.0.dev0-cp311-cp311-macosx_26_0_arm64.whl",
    # future linux target, same rules
    "solweig_light-0.1.0.dev0-py3-none-manylinux_2_28_x86_64.whl",
]

NATIVE_BAD = [
    ("solweig_light-0.1.0.dev0-py3-none-any.whl",
     "platform-independent"),
    ("solweig_light-0.1.0.dev0-cp311-cp311-any.whl",
     "platform tag 'any'"),
    ("solweig_light-0.1.0.dev0-cp311-abi3-macosx_26_0_arm64.whl",
     "abi3"),
    ("solweig_light-0.1.0.dev0-py3-none-weirdos_9_x.y.whl",
     "unrecognized platform tag"),
]


@pytest.mark.parametrize("filename", NATIVE_OK)
def test_platform_specific_names_accepted(filename):
    tags = check_wheel_tags(filename, has_native_lib=True)
    assert tags["platform_tag"] != "any"


@pytest.mark.parametrize("filename,why", NATIVE_BAD)
def test_platform_rules_enforced(filename, why):
    with pytest.raises(WheelTagError, match=why):
        check_wheel_tags(filename, has_native_lib=True)


def test_pure_wheel_without_native_content_is_fine():
    tags = check_wheel_tags("solweig_light-0.1.0.dev0-py3-none-any.whl",
                            has_native_lib=False,
                            wheel_metadata="Root-Is-Purelib: true\n")
    assert tags["python_tag"] == "py3"
    assert tags["platform_tag"] == "any"


def test_native_wheel_with_purelib_metadata_rejected():
    with pytest.raises(WheelTagError, match="Root-Is-Purelib"):
        check_wheel_tags(
            "solweig_light-0.1.0.dev0-py3-none-macosx_26_0_arm64.whl",
            has_native_lib=True,
            wheel_metadata="Root-Is-Purelib: true\nTag: py3-none-any\n")


def test_native_wheel_metadata_missing_purelib_flag_rejected():
    with pytest.raises(WheelTagError, match="lacks Root-Is-Purelib"):
        check_wheel_tags(
            "solweig_light-0.1.0.dev0-py3-none-macosx_26_0_arm64.whl",
            has_native_lib=True,
            wheel_metadata="Tag: py3-none-macosx_26_0_arm64\n")


def test_native_wheel_with_false_purelib_flag_accepted():
    check_wheel_tags(
        "solweig_light-0.1.0.dev0-py3-none-macosx_26_0_arm64.whl",
        has_native_lib=True,
        wheel_metadata="Root-Is-Purelib: false\n"
                       "Tag: py3-none-macosx_26_0_arm64\n")


def test_invalid_wheel_filename_rejected():
    with pytest.raises(WheelTagError, match="not a valid wheel filename"):
        parse_wheel_filename("solweig_light-0.1.0.dev0.tar.gz")
    with pytest.raises(WheelTagError, match="not a valid wheel filename"):
        check_wheel_tags("garbage.whl", has_native_lib=True)
