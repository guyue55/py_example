# 开发与维护

Python>=3.11，使用受支持解释器的最新补丁版本。保留requests/setuptools和轻量SDK边界，不引入业务、服务端或模板引擎。

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check src tests scripts
mypy src
python -m pytest -q
python scripts/verify_package.py
python scripts/verify_package.py --rename
python scripts/verify_package.py --rename --minimum
```

源码单元测试可用Mock定位错误；tests/test_http.py用独立本地端口验证真实重试次数、写入保护、超时与重定向。不要用静态适配器配置断言替代传输行为验证。

verify_package.py的editable安装仅存在于临时副本的source-env；wheel消费者另建环境，且不复制src和pyproject，避免源码遮蔽发行包。原始与重建wheel均测试；源码包用最低后端77.0.3、无Git构建。最低直接依赖固定为Requests2.33.0／urllib3 2.8.0；传递依赖正常解析，不声称所有历史最低组合均测试。

只手动修改src/example/__init__.py中的__version__。改名器同步动态属性和导入路径；提交前审阅显式暂存清单，使用type(scope): 中文说明，不混入本机状态。main走PR，最终main CI与候选提交须一致。

发布与回滚的唯一流程入口：[PUBLISHING.md](docs/PUBLISHING.md)。不在本指南复制另一套token或自动Tag发布方案。
