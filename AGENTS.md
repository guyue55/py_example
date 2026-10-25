# AGENTS.md

面向 AI 编程助手的本仓库上下文。人类维护者亦可参考。

## 项目概述

`py_example` 是一个 **Python SDK / HTTP 客户端模板**：基于 `requests` 封装了
认证（Bearer / Basic / ApiKey）、受控只读重试（429 与 5xx 指数退避 + jitter）与
类型化异常。它**不是成品库**，而是供他人 fork 后改名的脚手架。

- 占位包名：`example`（发布前必须改名）。
- 构建后端：setuptools（PEP 621 元数据），非 Poetry。
- 目标 Python：`>=3.11`，CI 矩阵 3.11–3.14。
- 模板本身**不发布**到 PyPI；改名后才具备发布条件。

## 目录结构

```
src/example/        包源码（client / auth / exceptions）
tests/              单元Mock + 真实本地HTTP + 模板工具测试（证据分开）
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
python scripts/verify_package.py --rename
python scripts/verify_package.py --rename --minimum
```

## 代码风格

- Lint/格式化：ruff（行宽 100，`target-version = py311`）。
- 导入排序：isort（ruff 内置，`select = ["E","F","I","W"]`）。
- **刻意不强制 UP（pyupgrade）规则**，避免批量改写无关代码；当前 pre-commit **不引入**
  `pyupgrade` 钩子，避免 PEP 585（`dict[...]` 替代 `Dict[...]` 等）自动改写突破该边界。
- 类型：mypy 约束 `<2`，未对全部函数强制 `disallow_untyped_defs`。
- 库日志：每个模块用 `logging.getLogger(__name__)`，包在 `__init__` 挂
  `NullHandler`，不要给库加 root handler。

## 版本管理（单一事实源）

- **唯一手写版本**：`src/example/__init__.py` 的 `__version__`。
- `pyproject.toml` 通过 `dynamic = ["version"]` + `tool.setuptools.dynamic`
  从 `__version__` 自动派生，**不要再在 pyproject 里写静态 version**。
- 改名时 `scripts/rename_template.py` 会同步更新 `pyproject.toml` 里 dynamic 版本的
  `attr` 引用（`example.__version__` → `<新名>.__version__`），以保证构建仍可用；
  版本*数值*始终只由 `__init__.__version__` 决定。

## Git 约定

- 提交格式：`类型(范围): 中文描述`（Conventional Commits 中文变体）。
  例：`feat(client): 增加超时参数`、`docs(publish): 补充 Trusted Publisher 说明`。
- 分支：`main` / `master` 受 CI 保护；功能走分支 + PR。

## 发布（默认关闭）

唯一流程入口为 docs/PUBLISHING.md；原模板仓库不能上传占位包。复制并改名、替换元数据、显式启用仓库变量并配置受保护环境后，只能从main手动选择已验证Tag上传。构建与OIDC上传分离，不给测试或构建任务id-token权限。Tag推送不会触发上传。

准备发布不等于正式发布，不打Tag、不上传索引，除非用户明确授权。已发布Tag不移动、资产不覆盖。源码与wheel/源码包重建、模板改名、安装后的真实HTTP和类型消费都必须验证。

## 边界（不要随意改动）

- 不要切换 HTTP 库到 `httpx`（模板以 `requests` 为最小依赖示范）。
- 不要引入 Copier / cookiecutter 等额外脚手架（保持零模板引擎依赖）。
- Python>=3.11是0.4维护基线；调整须说明支持状态和依赖安全依据，不为测试通过忽略漏洞。
- 不要删除 `NullHandler` 或 `__all__`，它们是库的基本契约。
