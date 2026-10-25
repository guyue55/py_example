# 更新日志 (Changelog)

本项目所有重要变更均记录于此文件。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.0] - 待发布

### 修复与安全默认
- 改名后User-Agent测试不再硬编码旧包名；拒绝Python关键字和路径式包名，AI入口及动态版本引用同步。
- 默认关闭写操作状态码重试与自动重定向；读取错误不重放，写入重试须显式允许并由调用方保证幂等。
- 真正启用jitter，修复单请求timeout冲突和调用方headers被修改；错误消息不默认回显远端正文。
- 基于维护和安全状态将Python下限提升至3.11，Requests>=2.33、urllib3>=2.8；setuptools最低77.0.3匹配SPDX许可写法。

### 工程与验证
- 添加类型标记、本地真实HTTP回归、模板工具和占位发布保护测试。
- CI扩展解释器及Windows/macOS，增加改名、wheel消费、类型消费、最低依赖和无Git源码包重建验证。
- 发布改为显式启用、手动选择Tag，质量门禁、构建与OIDC上传分离；修正授权文档。

## [0.3.0] - 2026-10-19

### 新增 (Added)
- 新增 `AGENTS.md`，为 AI 编程助手提供跨工具项目上下文（目录结构、常用命令、代码风格、版本管理与发布边界）。
- `src/example/__init__.py` 挂 `NullHandler` 并显式声明 `__all__`，规范库日志行为与公共 API 边界。

### 变更 (Changed)
- 版本管理改为单一事实源：`pyproject.toml` 使用 `dynamic = ["version"]` 从 `__init__.__version__` 自动派生，不再双处手写同步。
- CI（`ci.yml`）增加最小权限 `contents: read` 与 `timeout-minutes`，action 升级至 `checkout@v6`/`setup-python@v6`，runner 钉 `ubuntu-24.04`。
- 发布工作流（`publish.yml`）tag 收紧为 `v*.*.*` 并增加 `environment: pypi`；OIDC 发布显式声明 `id-token: write`。
- `.pre-commit-config.yaml` 扩充 `pre-commit-hooks`（end-of-file-fixer / trailing-whitespace / check-yaml / debug-statements），`ruff-pre-commit` 升级至 v0.17.1。
- `User-Agent` 改为运行时取顶层包名，改名后自动适配（`_PACKAGE_NAME = __name__.split(".")[0]`）。

### 修复 (Fixed)
- 修复 `scripts/rename_template.py` 改名时未同步 `version = {attr = "<名>.__version__"}` 的隐患，避免改名后构建报 `ModuleNotFoundError`。
- 校正 `AGENTS.md` 中两处与实现脱节的描述（pyupgrade 钩子、改名与版本的关系）。

## [0.2.0] - 2026-10-19

### 新增 (Added)
- 新增基于 `urllib3.Retry` 的重试机制，覆盖 `429`/`5xx`/连接超时，自带指数退避与随机抖动（jitter）。
- 新增 `APIClient` 上下文管理器协议（`__enter__`/`__exit__`）与显式 `close()` 方法，避免连接泄漏。
- 新增 GitHub Actions CI 工作流：Python 3.9–3.13 矩阵执行 `ruff` 检查与 `pytest` 测试。
- 新增 `.pre-commit-config.yaml`，集成 `ruff` 检查与格式化钩子。
- 新增 `tests/test_auth.py`，覆盖 Bearer/Basic 认证头与 `ApiKeyAuth` 的 header/query 两种注入方式。
- 新增针对重试适配器配置、上下文管理器关闭、错误响应状态码保留的测试用例。

### 变更 (Changed)
- 打包配置由 `setup.py` 迁移至 `pyproject.toml`（PEP 621）。
- 目录结构迁移至 `src/` 布局，包名统一为占位符 `example`（修复此前命名四处不一致）。
- 声明运行依赖 `requests>=2.28`（此前缺失，导致安装后运行报错）。
- `requires-python` 由 `>=3.6` 提升至 `>=3.9`（3.6/3.7 已停止维护）。
- `User-Agent` 改为动态读取 `__version__`，消除此前写死的 `sdk_utils/1.0` 与实际版本不符的问题。
- 更新 `README.md` 与 `developer_guide.md`（模板改名说明、构建改用 `python -m build`、测试改用 `pytest`）。

### 修复 (Fixed)
- 修复 `ApiKeyAuth` 的 query 分支：原实现依赖 `PreparedRequest.params`（不存在），密钥实际不会携带；改为使用 `request.prepare_url()` 真实追加到 URL。
- 修复 `BasicAuth` 实现：原实现在 prepare 阶段设置 `request.auth` 无效，Authorization 头不会编码；改为继承 `requests.HTTPBasicAuth`。
- 修复 `APIError` 在错误响应（非 2xx）下丢失 `status_code` 的问题：原判断 `if response` 受 `requests.Response.__bool__` 影响（错误码响应为 falsy），改为 `if response is not None`。

## [0.1.0] - 2026-10-01

### 初始版本 (Initial)
- 提供基于 `requests.Session` 的 `APIClient` 封装（GET/POST/PUT/PATCH/DELETE）。
- 提供 `BearerAuth`、`BasicAuth`、`ApiKeyAuth` 三种认证适配类。
- 提供异常体系：`APIError` 基类及 `AuthenticationError`、`RateLimitError`、`ValidationError`、`ResourceNotFoundError`。

[0.3.0]: https://github.com/guyue55/py_example/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/guyue55/py_example/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/guyue55/py_example/releases/tag/v0.1.0
