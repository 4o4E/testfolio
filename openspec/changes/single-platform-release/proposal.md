# x64 版本发布

## Why
运行环境只需要 x64。发布镜像应明确提供 linux/amd64，并保留现有构建缓存和真实容器验证。

## What Changes
- 发布目标为 linux/amd64，使用原生执行环境构建。
- 更新当前规范、文档和版本说明，增加发布平台回归检查。

## Capabilities
### Modified Capabilities
- `publishing`：明确运行架构及前端生产文件的单次构建。

## Impact
修改发布配置和说明，不改变应用接口、依赖版本、数据库或本机运行服务。
