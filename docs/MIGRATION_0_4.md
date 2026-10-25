# 0.4迁移与范围

- 最低Python从3.9提升至3.11：3.9已在2025年、3.10已在2026年10月停止维护；新依赖基线Requests>=2.33和urllib3>=2.8包含旧版本安全修复。不忽略安全通告来维持旧解释器。
- 默认写操作状态码重试关闭；仅在服务端支持幂等键等保证时显式配置retry_methods。连接建立前失败仍可有限重试；读取错误不重放。
- 默认重定向关闭，返回3xx供应用判断。必要时显式allow_redirects=True并核实认证转发。
- jitter从文案承诺变成真实参数retry_jitter。timeout支持单次请求覆盖，但不是总deadline。
- 错误消息不再默认拼接远端正文；可在受控场景从exception.response访问详细内容，注意脱敏。
- Publish改为默认禁用的手动流程，Tag推送不再上传；变更授权流程见发布文档。

保留库导入及现有认证类、HTTP方法和上下文管理器；本版是0.x次版本变更，不应当作无行为差异补丁升级。

[Python维护状态](https://devguide.python.org/versions/)、[Requests安全](https://github.com/psf/requests/security/advisories)、[urllib3安全](https://github.com/urllib3/urllib3/security/advisories)。
