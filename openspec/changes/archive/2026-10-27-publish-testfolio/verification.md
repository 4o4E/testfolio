# 发布验证

日期：2026-10-27。

- [公开仓库](https://github.com/4o4E/testfolio)匿名访问正常；公开历史起点为独立初始提交，自有代码使用 MIT 许可证。
- [主线 CI](https://github.com/4o4E/testfolio/actions/runs/40448464733)通过：8 项实际 SQLite／HTTP 测试、前端 lint／构建、规范检查、真实容器启动及接口检查。
- [v0.1.0 发布 CI](https://github.com/4o4E/testfolio/actions/runs/40448621249)通过：标签来源检查、双架构构建、发布后按镜像 digest 的 HTTP 检查、Release 创建。
- [Release](https://github.com/4o4E/testfolio/releases/tag/v0.1.0)对应提交 `ac81f955618eadecc17d0bfb353dc0ae8bd6b6d9`。
- [公开镜像](https://github.com/4o4E/testfolio/pkgs/container/testfolio)提供 `v0.1.0`、`0.1.0`、`latest` 和 `sha-ac81f95` 标签，镜像清单包含 `linux/amd64`、`linux/arm64`。构建产生的额外证明清单不代表其他运行架构。
- 镜像索引 digest 为 `sha256:6447610bfe111835a5b3f9412581d2e464b7c43b3534b933c300ee53dc4e8b18`，与发布 CI 一致。
- 使用没有登录凭据的 Docker 配置读取镜像清单成功；使用 `skopeo copy --src-no-creds` 完整下载 amd64 镜像成功。
- HTTP 启动检查在 GitHub 的 amd64 执行环境完成：两个服务健康，页面可读，项目列表为空，查看端不提供写入路由，录入端拒绝无令牌写入。arm64 本次验证构建产物，未执行启动测试。
- 保持既有接口、配置目录和存储格式；发布内容不包含运行数据、附件或用户凭据。
