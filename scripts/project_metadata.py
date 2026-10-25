"""读取模板或改名后项目的静态元数据；不导入包或执行版本代码。"""

import ast
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def metadata(root=ROOT):
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    attr = config["tool"]["setuptools"]["dynamic"]["version"]["attr"]
    package, symbol = attr.rsplit(".", 1)
    if not re.fullmatch(r"[a-z][a-z0-9_]*", package) or symbol != "__version__":
        raise ValueError("动态版本路径必须指向顶层包的__version__")
    module = ast.parse((root / "src" / package / "__init__.py").read_text(encoding="utf-8"))
    versions = [
        node.value.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and any(isinstance(t, ast.Name) and t.id == symbol for t in node.targets)
    ]
    if len(versions) != 1 or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", versions[0]):
        raise ValueError("需要唯一且静态的稳定版本")
    return config, package, versions[0]
