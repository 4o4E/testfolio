# Spec Delta

## Purpose

让使用者能够从公开源码和版本镜像独立运行 Testfolio，通过自动检查确认版本可构建及启动，并确保发布内容不混入运行数据、凭据和本地实例资料。

## ADDED Requirements

### Requirement: 公开内容
项目 SHALL 公开通用源码、使用文档与许可证，不公开运行数据库、附件、认证材料、实例配置和本地验收记录。

#### Scenario: 启动发布镜像
- **WHEN** 使用者以新的持久目录启动镜像
- **THEN** 项目列表为空，镜像不带预设业务资料，查看与录入接口保持隔离

### Requirement: 自动检查
项目 SHALL 对 main 和拉取请求运行后端、前端、规范及实际容器启动检查。

#### Scenario: 版本验证失败
- **WHEN** 后端、前端、规范或镜像启动检查失败
- **THEN** 不创建对应 GitHub Release

### Requirement: 版本发布
项目 SHALL 为属于 main 的有效版本标签发布 amd64 和 arm64 镜像，验证实际发布产物后创建 Release；公开镜像支持匿名拉取。

#### Scenario: 发布正式版本
- **WHEN** 正式版本通过检查并完成镜像启动验证
- **THEN** 版本镜像及 Release 可访问，版本标签与产物对应，匿名用户可拉取公开镜像

#### Scenario: 发布预发布版本
- **WHEN** 维护者推送有效预发布标签
- **THEN** 产物标记为预发布且不替换 latest 正式版本
