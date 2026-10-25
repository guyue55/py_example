"""临时副本中验证改名、源码包重建及安装后的功能与类型，不修改原项目。"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement
from project_metadata import ROOT, metadata


def clean_environment():
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(name, None)
    env["PYTHONNOUSERSITE"] = "1"
    return env


def run(args, cwd):
    subprocess.run([str(a) for a in args], cwd=cwd, env=clean_environment(), check=True)


def copy_project(target):
    # 白名单复制可交付源码，排除本机WorkBuddy状态、环境与缓存；无需.git。
    for name in [
        "pyproject.toml",
        "MANIFEST.in",
        "README.md",
        "LICENSE",
        "AGENTS.md",
        "developer_guide.md",
        "CHANGELOG.md",
    ]:
        shutil.copy2(ROOT / name, target / name)
    for name in ["src", "tests", "scripts", "docs", ".github"]:
        if name == ".github" and not (ROOT / name).is_dir():
            continue
        shutil.copytree(
            ROOT / name,
            target / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
        )


def inspect_wheel(wheel, config, package, version):
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("wheel包含重复成员")
        info = next(n for n in names if n.endswith(".dist-info/METADATA"))
        meta = BytesParser().parsebytes(archive.read(info))
        if (
            meta["Name"].replace("_", "-") != config["project"]["name"].replace("_", "-")
            or meta["Version"] != version
        ):
            raise ValueError("发行物名称或版本不一致")
        project = config["project"]
        expected = {str(Requirement(d)) for d in project["dependencies"]}
        expected.update(
            str(Requirement(d + '; extra == "dev"'))
            for d in project["optional-dependencies"]["dev"]
        )
        if (
            meta["Requires-Python"] != project["requires-python"]
            or meta["License-Expression"] != project["license"]
            or {str(Requirement(d)) for d in meta.get_all("Requires-Dist", [])} != expected
        ):
            raise ValueError("发行物依赖、Python范围或许可不一致")
        if f"{package}/py.typed" not in names or not any(
            n.endswith("/licenses/LICENSE") for n in names
        ):
            raise ValueError("发行物缺少类型标记或许可")


def verify(root, minimum=False, artifacts=None):
    config, package, version = metadata(root)
    dist = artifacts if artifacts else root / "dist"
    if not artifacts:
        run([sys.executable, "-m", "build", "--outdir", dist], root)
    wheels, sources = list(dist.glob("*.whl")), list(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("验收目录必须恰好包含一个wheel和一个sdist")
    wheel, sdist = wheels[0], sources[0]
    inspect_wheel(wheel, config, package, version)
    run([sys.executable, "-m", "twine", "check", "--strict", wheel, sdist], root)
    rebuilt = root / "rebuilt"
    # 从tar输入独立解包，使用最低setuptools，不依赖Git或editable安装。
    import tarfile

    extracted = root / "unpacked"
    with tarfile.open(sdist) as archive:
        archive.extractall(extracted, filter="data")
    source = next(extracted.iterdir())
    constraint = root / "backend.txt"
    constraint.write_text("setuptools==77.0.3\n", encoding="utf-8")
    env = clean_environment()
    env["PIP_CONSTRAINT"] = str(constraint)
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(rebuilt)],
        cwd=source,
        env=env,
        check=True,
    )
    rebuilt_wheel = next(rebuilt.glob("*.whl"))
    inspect_wheel(rebuilt_wheel, config, package, version)
    with zipfile.ZipFile(wheel) as a, zipfile.ZipFile(rebuilt_wheel) as b:
        original = {n: a.read(n) for n in a.namelist() if n.startswith(package + "/")}
        repeated = {n: b.read(n) for n in b.namelist() if n.startswith(package + "/")}
        if original != repeated:
            raise ValueError("源码包重建的包源码不一致")
    for artifact in (wheel, rebuilt_wheel):
        with tempfile.TemporaryDirectory(prefix="sdk-consumer-") as folder:
            consumer = Path(folder)
            venv.EnvBuilder(with_pip=True).create(consumer / "env")
            python = consumer / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            requirements = ["pytest>=7", "mypy>=1,<2", "types-requests"]
            if minimum:
                requirements += ["requests==2.33.0", "urllib3==2.8.0"]
            run([python, "-m", "pip", "install", artifact, *requirements], consumer)
            code = f"""import importlib.metadata, importlib.resources, pathlib, sys
import {package} as sdk
assert sdk.__version__ == importlib.metadata.version({config["project"]["name"]!r}) == {version!r}
assert pathlib.Path(sdk.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())
assert importlib.resources.files(sdk).joinpath("py.typed").is_file()
with sdk.APIClient("https://example.invalid") as client:
    assert client.retry_methods == frozenset({{"GET", "HEAD", "OPTIONS"}})
"""
            run([python, "-I", "-c", code], consumer)
            (consumer / "tests").mkdir()
            for name in ["test_auth.py", "test_client.py", "test_http.py"]:
                shutil.copy2(root / "tests" / name, consumer / "tests" / name)
            run([python, "-m", "pytest", "--import-mode=importlib", "-q", "tests"], consumer)
            (consumer / "consumer.py").write_text(
                f"from {package} import APIClient\n"
                "with APIClient('https://example.invalid') as c:\n"
                "    r = c.get('/x')\n    reveal_type(r)\n",
                encoding="utf-8",
            )
            run([python, "-m", "mypy", "consumer.py", "--check-untyped-defs"], consumer)
            run([python, "-m", "pip", "check"], consumer)
    print("PACKAGE_VERIFIED", json.dumps({"name": package, "version": version, "minimum": minimum}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rename", action="store_true")
    parser.add_argument("--minimum", action="store_true")
    parser.add_argument("--artifacts", type=Path, help="验证实际待上传目录，不另行构建原wheel")
    args = parser.parse_args()
    if args.artifacts and args.rename:
        parser.error("实际发行物验收不能同时改名")
    artifacts = args.artifacts.resolve() if args.artifacts else None
    with tempfile.TemporaryDirectory(prefix="sdk-template-") as folder:
        root = Path(folder)
        copy_project(root)
        _, original_package, _ = metadata(root)
        if args.rename and original_package == "example":
            run([sys.executable, "scripts/rename_template.py", "my_sdk"], root)
        elif args.rename:
            print("RENAME_NOT_APPLICABLE", original_package, flush=True)
        venv.EnvBuilder(with_pip=True).create(root / "source-env")
        python = root / "source-env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([python, "-m", "pip", "install", "-e", ".[dev]"], root)
        # editable只存在于副本的独立环境；不改调用者环境的包安装。
        run([python, "-m", "pytest", "-q"], root)
        verify(root, args.minimum, artifacts)


if __name__ == "__main__":
    main()
