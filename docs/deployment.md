# 部署、升级与备份

## 初次启动

Testfolio 通过单个容器运行两个服务：查看页面和只读 API 使用容器端口 `8080`，私有录入 API 使用 `8081`。Compose 示例将录入端口固定绑定至主机本机；查看端口默认绑定 `127.0.0.1`。

克隆公开仓库并生成私有配置：

```bash
git clone https://github.com/4o4E/testfolio.git
cd testfolio
python3 scripts/setup_local.py \
  --read-url http://localhost:8080 \
  --write-url http://localhost:8081
```

脚本默认将配置写入 `~/.config/test-results/`。`client.json` 保存查看网址、录入网址和随机生成的写入令牌；`server.env` 仅提供容器启动所需令牌。目录权限为 `0700`，配置文件权限为 `0600`。重复运行会保留既有令牌；可以通过 `--config-dir <目录>` 选择其他私有配置目录。

设置持久数据目录、服务配置文件路径和查看端绑定地址：

```bash
export TEST_RESULTS_RESOURCE_DIR="$PWD/data"
export TEST_RESULTS_SERVER_ENV="$HOME/.config/test-results/server.env"
export TEST_RESULTS_READ_BIND="127.0.0.1"
```

这里的 `TEST_RESULTS_RESOURCE_DIR` 必须是专用于 Testfolio 的主机持久目录。Compose 将其下 `sqlite/` 映射到容器 `/data/sqlite`，将 `artifacts/` 映射到 `/data/artifacts`。`TEST_RESULTS_SERVER_ENV` 必须指向生成的 `server.env` 完整路径。`TEST_RESULTS_READ_BIND` 控制主机查看端口绑定地址；让其他机器访问前，应先配置合适的网络访问限制。录入端口仍仅绑定本机。

下载并启动公开预构建镜像：

```bash
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml up -d --pull never --no-build
docker compose -f compose.example.yml ps
```

默认镜像版本为 `ghcr.io/4o4e/testfolio:v0.1.1`。部署在本机时，访问 `http://localhost:8080`。可以请求 `/health` 确认两个服务均可响应：

```bash
curl --fail http://localhost:8080/health
curl --fail http://localhost:8081/health
```

首次启动使用空数据库，不会自动创建项目、用例或示例结果。完成配置后，按 [录入流程](recording.md) 添加真实记录。

## 升级和回退

升级前先备份 SQLite 数据库及附件，阅读新版本发布说明，再选择一个明确的正式版本标签。将 `TESTFOLIO_VERSION` 设为该标签，先显式拉取版本，再使用已拉取的镜像启动：

```bash
export TESTFOLIO_VERSION=v0.1.1
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml up -d --pull never --no-build
docker compose -f compose.example.yml ps
```

启动后检查查看和录入服务健康接口，并打开页面确认记录可读。不要使用浮动的 `latest` 标签来代替明确版本。

回退时将 `TESTFOLIO_VERSION` 改为先前保留的正式版本，再以 `up -d --pull never --no-build` 启动；只有本机尚无该版本时才需要先下载。若新版本已经改变数据库格式，旧镜像可能无法读取升级后的数据库；应同时恢复升级前成套保存的数据库和附件。Testfolio 不会自动回滚数据格式。

普通重启使用 `docker compose -f compose.example.yml restart`，或使用 `docker compose -f compose.example.yml up -d --pull never --no-build`。日常重启不会检查远程镜像。Compose 示例采用 `pull_policy: missing`，常规 `up` 仅在本机缺少指定镜像时才尝试拉取；显式升级仍应先运行 `pull`，再以 `--pull never --no-build` 启动，确保切换的是已选定的正式版本。

本机磁盘空间不足时，只清理已经确认不再使用的确切旧版本镜像。保留当前运行版本和一个可回退版本；不要执行会清理所有未使用镜像的全局清理命令。

## 备份与恢复

SQLite 数据库文件为 `<资源目录>/sqlite/test-results.sqlite3`，附件保存在 `<资源目录>/artifacts/`。备份必须同时包含数据库和附件，并保留二者的相对目录结构。只备份数据库会导致图片和报告缺失；只复制 SQLite 主文件也可能遗漏写入中的事务数据。

可以通过 SQLite backup API 生成一致的数据库副本，并将附件复制到同一备份集。备份工具必须使用实际的 TEST_RESULTS_RESOURCE_DIR，源数据库以只读方式打开，不能在路径填写错误时新建一个空数据库作为备份。备份文件保存在持久资源目录以外。

手动备份时，先停止服务，再将数据库目录和附件一起复制到同一个新的备份目录；复制完成后重新启动：

```bash
docker compose -f compose.example.yml stop
cp -a "$TEST_RESULTS_RESOURCE_DIR/sqlite" /path/to/backup/
cp -a "$TEST_RESULTS_RESOURCE_DIR/artifacts" /path/to/backup/
docker compose -f compose.example.yml start
```

恢复时停止服务，将备份中的 `sqlite/` 与 `artifacts/` 放回同一资源目录，再启动并检查健康接口及记录。确保数据库和附件来自同一备份时间点。

## 网络边界

查看端口包含测试数据，应限制为预期用户可访问。写入端口只绑定主机本机；远程运行 CLI 或 Agent 时，应使用受控隧道或在同一主机执行，并让客户端配置中的写入地址与实际连接方式一致。不要将写入令牌交给网页访问者。

如果 Docker 拉取镜像需要经过代理，应在 Docker daemon 的网络配置中设置代理。只设置当前终端的代理环境变量，不能保证 Docker daemon 拉取镜像时使用该代理。修改主机全局 daemon 配置需要按主机管理流程另行授权。

## 构建环境

Docker 构建使用固定的 Node.js 与 Python 基础镜像公开版本及多架构 digest。基础镜像升级时，应核实新版本确实提供 `linux/amd64` 和 `linux/arm64`，然后更新相应 digest，并在 CI 与发布构建中验证两个目标架构。前端构建阶段在构建机平台运行，避免为目标架构模拟执行 Node.js 工具。

Python 依赖由 `requirements.in` 和 `requirements-dev.in` 声明。使用 uv 0.13.6 按以下命令生成锁文件：

```bash
uv pip compile requirements.in --universal --python-version 3.11 --output-file requirements.txt --no-header
uv pip compile requirements-dev.in --universal --python-version 3.11 --output-file requirements-dev.txt --no-header
```

更新依赖时手工修改声明并重新生成两个锁文件；`requirements-dev.in` 通过约束 `requirements.txt` 中的版本，确保开发依赖与运行依赖一致。Docker 与 CI 仍使用 pip 安装锁文件，不需要在应用运行环境安装 uv。
