# v0.1.1 发布验证

日期：2026-10-27。

- [主线 CI](https://github.com/4o4E/testfolio/actions/runs/40467898019)及[发布 CI](https://github.com/4o4E/testfolio/actions/runs/40468045020)均通过，包含 10 项测试及发布镜像的真实 HTTP 启动检查。
- [v0.1.1 Release](https://github.com/4o4E/testfolio/releases/tag/v0.1.1)对应提交 `c60de05e600f03343d18abf82ee07dc8c7b7480f`。
- `ghcr.io/4o4e/testfolio:v0.1.1`、`0.1.1` 与 `latest` 指向同一摘要：`sha256:aaf75d098876d0ea2377cc8a8df939a0aa5a46e0f2022cd6a0f308c7239cca0d`。
- 匿名读取发布清单及配置，唯一运行架构为 `linux/amd64`。额外构建证明清单不计运行架构。
- 使用 `skopeo copy --src-no-creds` 完整匿名下载成功。
- 10 个运行文件系统层与已验证的构建缓存结果完全一致，实际发布复用依赖和网页构建结果。
- 本机运行服务和持久资料保持不变，接口及数据库格式无迁移。
