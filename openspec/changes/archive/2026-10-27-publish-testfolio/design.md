# Design

## Decisions
- 发布身份为 Testfolio、4o4E/testfolio、ghcr.io/4o4e/testfolio，首版 v0.1.0，许可证 MIT。
- 公开 main 从当前通用源码建立独立初始提交；本地历史及运行资料不推送。后续开发沿用这份公开历史。
- 复用现有 Dockerfile 与 Compose，通过 GitHub Actions 的仓库令牌发布镜像，不引入外部部署服务或用户业务凭据。
- 标签提交必须属于 main；Python、前端及规范通过后构建 amd64／arm64，以实际发布 digest 检查空数据库启动和读写隔离，成功后创建 Release。
- GHCR 可见性单独确认，以匿名拉取证明公开。版本使用明确标签，预发布不替换 latest。
- 保留现有 test-results 配置和 skill 路径，项目名称不触发用户数据或凭据迁移。
