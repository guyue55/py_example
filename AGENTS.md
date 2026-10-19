# AGENTS.md

面向 AI 编程助手的本仓库上下文。人类维护者亦可参考。

## 项目概述

`py_example` 是一个 **Python SDK / HTTP 客户端模板**：基于 `requests` 封装了
认证（Bearer / Basic / ApiKey）、传输层重试（429 与 5xx 指数退避 + jitter）与
类型化异常。它**不是成品库**，而是供他人 fork 后改名的脚手架。

- 占位包名：`example`（发布前必须改名）。
- 构建后端：setuptools（PEP 621 元数据），非 Poetry。
- 目标 Python：`>=3.9`，CI 矩阵 3.9–3.13。
- 模板本身**不发布**到 PyPI；改名后才具备发布条件。

## 目录结构

```
src/example/        包源码（client / auth / exceptions）
tests/              测试（用真实本地 HTTP server，非外部依赖桩）
scripts/rename_template.py   一键改名 example → 真名
docs/PUBLISHING.md  发布到 PyPI（Trusted Publishing）指南
developer_guide.md  开发指南
```

## 常用命令

```bash
pip install -e ".[dev]"     # 安装包 + 开发依赖（pytest/ruff/mypy/types-requests）
pytest                       # 跑测试
ruff check .                 # lint
ruff format .                # 格式化
mypy src                     # 类型检查
python -m build              # 构建 sdist + wheel
python scripts/rename_template.py <新包名>   # 改名（支持 --dry-run）
pre-commit run --all-files   # 本地跑全部 pre-commit 钩子（CI 同款）
```

## 代码风格

- Lint/格式化：ruff（行宽 100，`target-version = py39`）。
- 导入排序：isort（ruff 内置，`select = ["E","F","I","W"]`）。
- **刻意不强制 UP（pyupgrade）规则**，保持对 3.9 的低门槛；pre-commit 另有独立
  `pyupgrade --py39-plus` 钩子做安全现代化。
- 类型：mypy 约束 `<2`（兼容 3.9），未对全部函数强制 `disallow_untyped_defs`。
- 库日志：每个模块用 `logging.getLogger(__name__)`，包在 `__init__` 挂
  `NullHandler`，不要给库加 root handler。

## 版本管理（单一事实源）

- **唯一手写版本**：`src/example/__init__.py` 的 `__version__`。
- `pyproject.toml` 通过 `dynamic = ["version"]` + `tool.setuptools.dynamic`
  从 `__version__` 自动派生，**不要再在 pyproject 里写静态 version**。
- 改名脚本不触碰版本（与包名无关）。

## Git 约定

- 提交格式：`类型(范围): 中文描述`（Conventional Commits 中文变体）。
  例：`feat(client): 增加超时参数`、`docs(publish): 补充 Trusted Publisher 说明`。
- 分支：`main` / `master` 受 CI 保护；功能走分支 + PR。

## 发布（Trusted Publishing，默认惰性）

- 发布流程见 `docs/PUBLISHING.md`。`.github/workflows/publish.yml` 在推送
  `v*.*.*` 标签时，通过 OIDC（无需 token）自动发布到 PyPI。
- 发布前必须：① 用 `rename_template.py` 改名；② 在 PyPI 配置同名
  Trusted Publisher（environment 名 `pypi`）；③ 在 PyPI 上确认包名未被占用。
- **不可逆**：正式发布前务必先在 TestPyPI 跑通一次。

## 边界（不要随意改动）

- 不要切换 HTTP 库到 `httpx`（模板以 `requests` 为最小依赖示范）。
- 不要引入 Copier / cookiecutter 等额外脚手架（保持零模板引擎依赖）。
- 不要改动 `requires-python` 下限，除非明确需要。
- 不要删除 `NullHandler` 或 `__all__`，它们是库的基本契约。
