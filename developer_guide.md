# 1. 开发指南

## 1.1 环境设置

1. 克隆仓库：
```bash
git clone https://github.com/guyue55/py_example.git
cd py_example
```

2. 安装开发依赖（含测试与 lint 工具）：
```bash
pip install -e ".[dev]"
```

## 2.2 运行测试

```bash
pytest
```

## 2.2.1 代码风格检查

```bash
ruff check .
```

## 2.3 代码贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交变更
4. 运行测试确保通过
5. 提交 Pull Request

# 3. 发布流程

## 3.1 版本管理

- 遵循语义化版本规范
- 在 `pyproject.toml` 的 `[project]` 中更新 `version`
- 同步更新 `src/example/__init__.py` 中的 `__version__`
- 添加版本更新日志

## 3.2 打包和发布

> 推荐方式：Trusted Publishing（OIDC），无需在仓库中保存 API token。
> 完整流程见 [docs/PUBLISHING.md](docs/PUBLISHING.md)，GitHub Actions 已提供
> `.github/workflows/publish.yml`（推送 `v*` 标签即自动发布）。

本地自检步骤：

先安装依赖
```bash
python -m pip install --upgrade build twine
```

1. 构建分发包：
```bash
python -m build
```

2. 检查包是否符合PyPI的要求
```bash
python -m twine check dist/*
```

3. 打版本标签并推送（触发自动发布）：
```bash
git tag v0.2.0
git push origin v0.2.0
```


**注意事项**

- **模板本身不发布**：本仓库包名为占位符 `example`，请先用
  `scripts/rename_template.py` 改名后再发布。
- **API token（可选）**：若不使用 Trusted Publishing，上传到 **PyPI** 需要
  API token，没有的话先去网站注册账号再生成（https://pypi.org/）。
- **避免每次都要输入 token**：设置 `$HOME/.pypirc`
    ```
    [pypi]
    username = __token__
    password = pypi-xxxxxx
    ```