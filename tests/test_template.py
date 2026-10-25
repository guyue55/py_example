"""模板工具的负向验证；实际改名后的构建和消费由verify_package.py完成。"""

import importlib
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
check_release = importlib.import_module("check_release")
rename_template = importlib.import_module("rename_template")
metadata = importlib.import_module("project_metadata").metadata


@pytest.mark.parametrize("name", ["class", "for", "123bad", "bad-name", "../escape", "_hidden", ""])
def test_invalid_import_names(name):
    assert not rename_template.is_valid_package_name(name)


def test_rename_updates_dynamic_version_and_imports():
    assert rename_template.is_valid_package_name("sample_sdk")
    assert (
        rename_template.replace_pyproject_version_attr(
            'version = {attr = "example.__version__"}', "sample_sdk"
        )
        == 'version = {attr = "sample_sdk.__version__"}'
    )
    assert rename_template.rewrite_imports(
        "from example.client import APIClient", "sample_sdk"
    ) == ("from sample_sdk.client import APIClient")


def test_placeholder_cannot_publish():
    with pytest.raises(ValueError, match="占位模板"):
        check_release.validate({"project": {"name": "example"}}, "0.4.0", "v0.4.0")


def test_release_requires_real_metadata_and_exact_tag():
    config = {
        "project": {
            "name": "sample-sdk",
            "authors": [{"name": "maintainer"}],
            "urls": {"Homepage": "https://github.com/demo/sample-sdk"},
        }
    }
    check_release.validate(config, "0.4.0", "v0.4.0")
    with pytest.raises(ValueError):
        check_release.validate(config, "0.4.0", "v0.3.0")
    config["project"]["authors"] = [{"name": "Your Name"}]
    with pytest.raises(ValueError):
        check_release.validate(config, "0.4.0", "v0.4.0")


def test_version_is_static_single_source():
    _, package, version = metadata()
    assert version == importlib.import_module(package).__version__
    assert (SCRIPTS.parent / "src" / package / "py.typed").is_file()
