# 发布与回滚

## 模板与实际库的区别

`guyue55/py_example`是模板，保留占位包名example，只准备／发布GitHub源码版本。其Publish工作流显式拒绝在原仓库上传，也不会因Tag推送运行。

使用模板的实际库先改名并替换authors／project.urls，再走下列步骤。不要原样上传example包或保留占位维护者。

## 本地准备

1. 修改src下唯一__version__，更新CHANGELOG和发布说明；版本Tag必须与之完全一致。
2. 安装开发依赖，执行开发指南中的格式／类型／源码测试。
3. 执行 `python scripts/verify_package.py --rename` 和 `--minimum`，验证模板改名链路；实际库也可运行不带--rename的验证器。
4. 在最终main提交上构建 `python -m build`；运行 `python -m twine check --strict dist/*`。Twine主要检查说明文档渲染，不是完整安全或功能认证。
5. 检查许可证、元数据、源码、测试、来源SHA和摘要。不得把本机环境、WorkBuddy状态或凭证打包。
6. main完整CI通过后，创建指向同一提交的附注Tag。已发布Tag或同名资产不得移动／覆盖，修复另发版本。

## 复制后启用PyPI

- PyPI/TestPyPI各自配置Trusted Publisher：owner、repository、workflow文件publish.yml，以及环境名pypi或testpypi。
- GitHub仓库创建对应环境，设置审批人和允许main的分支规则；配置仓库变量ENABLE_PYPI_PUBLISH=true。
- 在main的Publish工作流手动填写Tag和目标（默认testpypi）。Tag必须存在、属于main历史、版本与非占位元数据一致。
- preflight固定提交 → 复用完整CI → 独立构建验包 → 制品传递 → 环境审批 → 上传。只有最后上传任务具备id-token:write；上传任务不检出源码、不执行构建。
- 正式上传前核验目标、名称与授权。TestPyPI检查流程不等于正式索引依赖解析已通过；上传后匿名下载／安装复验。

PyPI没有在上述GitHub Publisher配置中提供任意Tag通配输入；Tag限制由GitHub工作流和环境落实。不要笼统认为私有仓库必须使用长期token；按实际OIDC支持与权限核验。

默认不使用长期token，也不建议将token写入.pypirc示例。可信发布仅验证身份，不证明代码或构建物安全。

## 失败与回滚

CI或验包失败停止发布；上传状态未知先查询索引，不盲目重复写入。已上传版本不可原地修复；必要时撤回可发现性并发布修正版，记录影响，不保证删除第三方下载副本。

参考：[PyPA打包](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)、[PyPI配置](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)、[PyPI安全模型](https://docs.pypi.org/trusted-publishers/security-model/)。
