# 发布到 PyPI（Trusted Publishing）

本模板本身以占位包名 `example` 存在，**不应直接发布**。当你已用
`scripts/rename_template.py` 改名成自己的包名后，即可按本文档发布到 PyPI。

推荐使用 **Trusted Publishing（OIDC）**，无需在仓库中存放任何 API token。

## 流程概览

1. 改名并完善元数据（`authors`、`project.urls`、描述）。
2. 本地构建并检查：`python -m build` + `python -m twine check dist/*`。
3. 先在 **TestPyPI** 验证一次。
4. 打版本标签 `vX.Y.Z`，推送标签触发 GitHub Actions 自动发布到正式 PyPI。

## 1. 本地构建与自检

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

`twine check` 会校验 `long_description`（README）、元数据与 wheel 结构。

## 2. 配置 Trusted Publisher（一次性）

在 PyPI（以及可选的 TestPyPI）后台为你的包名添加 **Trusted Publisher**：

- **PyPI**：Account → Publishing（或某包的管理页）→ Add a new pending
  publisher。
- 填写：
  - **PyPI project name**：你的真实包名（与 `pyproject.toml` 的 `name` 一致）。
  - **Owner / Repository**：你的 GitHub 仓库（如 `guyue55/py_example`）。
  - **Workflow name**：`publish.yml`。
  - **Environment name**：留空或填 `pypi`（与 `publish.yml` 中 `environment` 对应）。
  - **Tag / branch**：建议用 tag 模式，例如 `v*`。

> 无需生成、无需在仓库里保存 PyPI token——OIDC 会在工作流运行时自动签发临时凭证。

## 3. 发布（从 tag 触发）

本仓库已提供 `.github/workflows/publish.yml`：当推送 `v*` 标签时，自动构建
并通过 `pypa/gh-action-pypi-publish` 发布。

```bash
git tag v0.1.0
git push origin v0.1.0
```

- 发布正式 PyPI：默认行为。
- 发布到 TestPyPI 验证：在 `publish.yml` 中取消注释 `repository-url` 那一行，
  并先在 TestPyPI 配置同名 Trusted Publisher，然后打一个测试标签即可。

## 4. 版本号与 CHANGELOG

- 每次发布前同步更新 `pyproject.toml` 的 `version` 与 `src/<你的包>/__init__.py`
  的 `__version__`（本模板已用相同值）。
- 在 `CHANGELOG.md` 记录本次变更（Keep a Changelog 格式）。

## 注意事项

- 包名在 PyPI 上全局唯一，改名时请先确认未被占用。
- Trusted Publishing 要求仓库为**公开**或已正确授权；私有仓库请改用 token 方式。
- 发布是不可逆操作；正式发布前务必先在 TestPyPI 跑通一次。
