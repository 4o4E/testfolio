# 公开发布 Testfolio

## Why
Testfolio 需要成为可以独立安装、维护和发布的通用测试记录工具。使用者应能从公开仓库取得源码、运行已发布镜像，并通过文档和自动检查了解安装方式及版本行为。

## What Changes
- 使用 Testfolio 名称、MIT 许可证及通用安装／录入／升级文档。
- 公开源码只包含平台代码与通用资料，运行数据、认证、实例配置及本地验收归档不发布。
- CI 验证 Python、前端、规范与空数据镜像；版本标签发布双架构镜像及 GitHub Release。

## Capabilities
### New Capabilities
- `publishing`：公开源码、自动检查和版本产物发布。

## Impact
增加文档、许可证与发布自动化，保留既有接口及存储格式。容器不包含用户数据或运行凭据。
