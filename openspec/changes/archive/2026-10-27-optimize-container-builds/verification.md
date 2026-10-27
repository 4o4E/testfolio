# 构建验证

日期：2026-10-27。验证提交：`8567819dee9e32c78512beaf0b1488a086aa51f5`。

- 本机 Python 3.11 环境的 9 项真实测试通过，包含既有 SQLite／HTTP 集成检查及 PR 缓存写权限回归检查；完整安装依赖兼容性检查通过。
- 前端 lint、typecheck 和 OpenSpec 严格检查通过；Compose 配置解析确认默认明确版本、missing 策略和本机录入端口。
- GPT-6 Luna 独立审查并复审构建、权限及文档；公开源码树检查无私有资料。
- [冷缓存 CI](https://github.com/4o4E/testfolio/actions/runs/40451345526/attempts/1)成功：构建及容器检查任务 69 秒，成功导出 GHCR 检查缓存。
- [热缓存 CI](https://github.com/4o4E/testfolio/actions/runs/40451345526/attempts/2)成功：同一提交在新的 GitHub 执行机器上运行，构建及容器检查任务 25 秒；npm 安装、Python 依赖安装及前端生产打包均命中缓存。
- 两轮运行镜像的 10 个文件系统层摘要完全相同。该耗时是这两次执行的实际观察，不是所有构建的时间保证。
- 两轮均实际启动镜像，确认查看页、空项目列表、健康接口及读写权限隔离正常。
- 匿名读取 `ghcr.io/4o4e/testfolio:buildcache-ci` 成功，确认 PR 可读取公开缓存。缓存格式为 BuildKit cacheconfig，不是运行镜像。
- 本次没有创建版本标签或执行新的双架构发布；`buildcache-release` 将由下一次版本发布产生。本次真实容器验证在 amd64 执行，双架构发布配置经静态审查。
- 应用接口、存储格式及现有实例不变，没有修改主机 Docker 代理配置。
