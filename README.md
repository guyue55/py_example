# Python SDK 模板

> **Template notice:** 本仓库是轻量模板，占位包名为 `example`，不能原样上传 PyPI。
> 使用前先运行 `python scripts/rename_template.py <your_package_name>`，
> 再替换维护者、项目链接并完成验证。

保留 requests／setuptools，提供 HTTP 客户端、认证与异常示例，不是完整业务框架。
Python >=3.11；CI验证3.11–3.14，以及Linux、Windows、macOS。其他解释器未承诺通过。

## 安装与开发

```sh
python -m pip install .          # 仅运行依赖
python -m pip install -e '.[dev]' # 开发、构建与检查工具
python -m pytest -q
ruff check .
ruff format --check src tests scripts
mypy src
```

版本唯一来源是 `src/example/__init__.py` 的 `__version__`；发行物携带 `py.typed`。
构建后端下限77.0.3以支持SPDX许可。依赖范围由库声明，具体应用自行锁定。

## 从模板开始

```sh
python scripts/rename_template.py my_sdk --dry-run
python scripts/rename_template.py my_sdk
python -m pip install -e '.[dev]'
python -m pytest -q
```

改名后必须修改 pyproject.toml 的 authors、project.urls、描述和适合自己项目的版本号。
核对diff和暂存清单后提交，格式如 `chore(template): 完成模板改名`。

```sh
python scripts/verify_package.py --rename
python scripts/verify_package.py --rename --minimum
```

验证器在临时副本完成改名、构建、Twine检查、无Git的源码包最低后端重建，以及独立安装后的真实HTTP／类型消费测试；不修改调用者的包安装、全局设置或原项目。

## 客户端使用与行为边界

```python
from example import APIClient, BearerAuth

with APIClient("https://api.example.com", auth=BearerAuth("YOUR_TOKEN"), timeout=30) as client:
    response = client.get("/items", timeout=(3, 10))
    data = response.json()
```

- 默认只对GET/HEAD/OPTIONS的429和常见5xx进行有限重试，指数退避包含jitter。连接建立前失败可重试；读取失败不重放，因为服务端可能已执行操作。
- POST/PATCH/PUT/DELETE默认不进行状态码重试。服务端明确支持幂等键时，才使用如 `retry_methods={"GET", "POST"}` 显式开启；本库不生成或验证幂等键。
- 默认不跟随重定向，防止自定义API-Key头意外转发；3xx原样返回。调用方可显式传 `allow_redirects=True`，并自行核实目的地和认证策略。
- timeout遵循Requests的连接／读取语义，支持单请求覆盖，不是包含退避和Retry-After的总执行期限。
- 默认异常消息不复制响应正文或底层URL；response和异常cause仍可包含敏感信息，不应直接记录完整对象或traceback到公开日志。
- 正常关闭客户端会释放连接；流式响应由调用方负责关闭。客户端不提供异步、数据库、自动业务幂等或跨线程安全承诺。

## 发布

模板本身可发布GitHub源码版本，不能上传占位 `example` 包。
复制并改名后的项目须显式设置 `ENABLE_PYPI_PUBLISH=true`、配置PyPI Trusted Publisher及受保护GitHub环境，再从main手动选择已经验证的Tag发布。推送Tag不会自动上传。

见 [发布流程](docs/PUBLISHING.md)、[开发与维护](developer_guide.md)、[AI协作说明](AGENTS.md)、[0.4迁移](docs/MIGRATION_0_4.md)。MIT许可见 [LICENSE](LICENSE)。
