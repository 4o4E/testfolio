# 版本、CI 与发布

## 版本和镜像

公开源码仓库为 [4o4E/testfolio](https://github.com/4o4E/testfolio)，公开容器镜像为 `ghcr.io/4o4e/testfolio`。正式版本使用 `v` 前缀标签，例如 `v0.1.0`。Compose 默认使用 `v0.1.0`，部署时可以用 `TESTFOLIO_VERSION` 选择其他明确版本。

发布维护者推送有效的 `v*` 语义化版本标签后，CI 工作流运行 Python 测试、前端 lint 与构建，以及 OpenSpec 校验。标签提交必须是 `main` 的祖先。上述任务和发布标签检查通过后，工作流构建并发布包含 `linux/amd64` 与 `linux/arm64` 的 GHCR 多架构镜像。每个正式版本同时发布带 `v` 和不带 `v` 的镜像标签，例如 `v0.1.0` 与 `0.1.0`；工作流通过发布镜像的 digest 执行 HTTP 启动检查，验证的是本次实际发布的镜像。检查成功后，工作流创建对应的 GitHub Release。预发布版本不会更新 `latest`，并标记为预发布；正式版本更新 `latest`。Release 说明由 GitHub 生成，发布维护者应核对其中的版本变更和兼容性信息。

GitHub Container Registry 的镜像包需要单独设为公开。推送成功本身不证明匿名用户可以拉取。维护者应在发布后退出已认证的 Docker 会话或使用未登录环境，匿名执行 `docker pull ghcr.io/4o4e/testfolio:<镜像标签>`，并确认镜像可拉取、目标架构可用。

## 发布前核对

发布维护者应确认：

- 版本变更与 `CHANGELOG.md` 相符，标签名称与版本一致。
- CI 对该标签触发，并且所有必需检查和发布镜像的 HTTP smoke 检查通过。
- GHCR 发布产物同时包含 `linux/amd64` 与 `linux/arm64`。
- GitHub Release 对应同一标签，说明内容已发布。
- GHCR 包的可见性为公开；未登录状态下的匿名拉取验证成功。
- `compose.example.yml` 默认版本能够从 GHCR 拉取，且与文档中的稳定版本一致。

CI 检查细节和实际触发配置以仓库 `.github/workflows/` 中的工作流文件为准。不要仅根据标签存在或带有登录状态的拉取结果认定发布完成。

## 构建缓存

CI 与正式发布构建均从现有镜像包读取 `buildcache-ci` 和 `buildcache-release` 两个 BuildKit 缓存标签。仅可信 `main` 分支推送将更新 `buildcache-ci`；版本标签发布将更新 `buildcache-release`。拉取请求只能读取缓存，不会写入缓存标签。首次构建或依赖、基础镜像更新导致缓存失效时，构建可能需要下载依赖并重新生成镜像层。

缓存标签不是应用版本，不包含可用于部署的正式镜像标签。部署只使用明确的正式版本标签，例如 `v0.1.0`；不得将 `buildcache-ci` 或 `buildcache-release` 设置为 `TESTFOLIO_VERSION`。

Dockerfile 固定 Node.js 与 Python 基础镜像的公开版本和多架构 digest。维护者升级时，应先确认所选公开版本具有 `linux/amd64` 与 `linux/arm64` 镜像，再更新 Dockerfile 中的 digest，并通过 CI 和发布构建确认两个架构均可构建。前端 CI 只运行 lint 与类型检查，生产网页包由 Docker 构建生成。

Python 依赖声明和完整锁文件的更新方式见[构建环境](deployment.md#构建环境)。安装仍使用 pip；升级依赖后检查锁文件变更，并通过 Python 测试和镜像构建验证。

## 开发验证

本地主要检查命令见 [README.md](../README.md#开发)。发布工作流会执行仓库中配置的自动化检查；具体 Python、前端、规范校验及镜像构建任务以工作流定义为准。版本标签应在拟发布的提交上创建，避免在检查未通过时发布镜像或 Release。

## 消费预构建镜像

匿名拉取某一版本：

```bash
docker pull ghcr.io/4o4e/testfolio:v0.1.0
```

在 Compose 部署中固定版本：

```bash
export TESTFOLIO_VERSION=v0.1.0
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml up -d --pull never --no-build
```

部署与数据保护步骤见 [部署说明](deployment.md)。
