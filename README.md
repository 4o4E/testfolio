# Testfolio

Testfolio 是自托管的测试记录工具：它按项目保存用例目录、测试轮次、逐步实际结果、截图和报告。网页供团队只读查看；录入由带私有令牌的独立接口完成。Testfolio 不会替用户操作被测系统，也不授予被测系统的访问权限。

当前稳定版本为 `v0.1.1`，项目使用 MIT 许可证。源码位于[公开 GitHub 仓库](https://github.com/4o4E/testfolio)，容器镜像为 `ghcr.io/4o4e/testfolio`。

## 功能范围

- 按项目、用例目录和轮次组织记录。目录可以同时展开多个分支，并支持全部展开／收起；用例包含前置条件、操作步骤、预期、优先级和标签。
- 按轮次记录环境、被测版本、执行范围、每一步的实际观察和状态。状态分为通过、失败、受阻、未测试和跳过。
- 保存真实截图及其他受支持的附件。网页只展示已保存的记录，不会把缺少结果的用例显示为通过。
- 已结束轮次保留创建时的用例定义与结果；复测应新建轮次。
- 提供只读查看 API、私有写入 API、命令行录入工具以及批量 JSON 导入工具。

Testfolio 不负责执行被测业务流程、管理测试账号，也不提供多用户角色管理。写入令牌只授权 Testfolio 录入接口，不代表可以操作被测系统。

## 使用预构建镜像启动

需要 Docker Compose、Python 3.11 或更新版本，以及能拉取 GitHub Container Registry 镜像的网络连接。运行应用不需要安装 Node.js。

克隆项目并进入目录：

```bash
git clone https://github.com/4o4E/testfolio.git
cd testfolio
```

创建仅本机可读写的私有配置。地址应填写使用者实际能够访问的查看端与录入端地址；录入端口默认只绑定本机。

```bash
python3 scripts/setup_local.py \
  --read-url http://localhost:8080 \
  --write-url http://localhost:8081
```

脚本默认在 `~/.config/test-results/` 创建 `client.json` 和 `server.env`，目录权限为 `0700`，文件权限为 `0600`。令牌由脚本生成且不会打印。若部署在其他地址，传入实际地址；容器内的服务配置仍由 `server.env` 提供。

准备 Compose 所需环境变量。把以下路径改为本机专用目录；路径必须是主机上用于持久保存数据库及附件的位置。

```bash
export TEST_RESULTS_RESOURCE_DIR="$PWD/data"
export TEST_RESULTS_SERVER_ENV="$HOME/.config/test-results/server.env"
export TEST_RESULTS_READ_BIND="127.0.0.1"
```

`TEST_RESULTS_READ_BIND` 是查看页面和读取 API 的主机绑定地址。仅当确实需要让其他机器访问时，才改成适当的主机接口地址，并在网络边界配置访问控制。录入端口 `8081` 始终只绑定本机。

用公开镜像启动：

```bash
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml up -d --pull never --no-build
docker compose -f compose.example.yml ps
```

Compose 默认使用 `ghcr.io/4o4e/testfolio:v0.1.1`。查看页面打开 `http://localhost:8080`。检查两项健康接口：

```bash
curl --fail http://localhost:8080/health
curl --fail http://localhost:8081/health
```

空数据库启动后不会自动出现演示项目或虚构的测试结果。先安装并使用录入 skill，或按 [API.md](API.md) 与 [docs/recording.md](docs/recording.md) 录入真实目录和轮次，之后页面才会显示记录。

需要选择版本时，在启动前设置 `TESTFOLIO_VERSION`，例如 `v0.1.1`，然后重新拉取并启动：

```bash
export TESTFOLIO_VERSION=v0.1.1
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml up -d --pull never --no-build
```

升级前请按 [部署与备份说明](docs/deployment.md) 备份数据库和附件。升级步骤、回退注意事项和数据目录说明也见该文档。

## 安装录入 skill

仓库保留兼容目录 `skills/test-results/`。可以将其链接到支持 Agent Skills 的本机工具的个人 skill 目录；下面以采用 `~/.agents/skills/` 的工具为例：

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/skills/test-results" "$HOME/.agents/skills/test-results"
```

如果目标链接已存在，先检查它指向的目录，再按所用工具的说明更新安装，避免覆盖已有 skill。安装后重新加载工具，并确认它能识别 `test-results` skill。也可以按所用工具支持的 skill 安装方式安装仓库中的 `skills/test-results/`；具体发现机制由工具决定。

录入前确保运行 Agent 的环境能够访问 Testfolio 服务，并已生成私有客户端配置。不要将令牌写入提示词、命令行参数、截图或报告。完整的真实测试、截图和结果录入步骤见 [录入流程](docs/recording.md)。

## 命令行和 API

客户端默认读取 `~/.config/test-results/client.json`，也可通过 `TEST_RESULTS_CONFIG` 或 `--config` 指定其他配置文件。常用查询与录入命令如下：

```bash
python3 skills/test-results/scripts/client.py projects
python3 skills/test-results/scripts/client.py cases --project <项目编号>
python3 skills/test-results/scripts/client.py runs --project <项目编号>
python3 skills/test-results/scripts/client.py --help
```

批量导入入口为 `python -m scripts.import_results --file <JSON文件>`。附件路径相对于 JSON 文件所在目录。导入结构和接口字段见 [API.md](API.md)。

## 开发

开发环境需要 Python 3.11 或更新版本、Node.js 22 或更新版本。CI 对网页运行 lint 和类型检查；生产网页包仅在 Docker 构建时生成。Python 运行依赖和开发依赖分别由 `requirements.txt` 与 `requirements-dev.txt` 锁定，依赖声明位于 `requirements.in` 与 `requirements-dev.in`。更新依赖时应同时更新声明和锁文件；开发依赖受运行依赖锁文件约束，确保两组安装使用相同的运行库版本。锁文件由 uv 0.13.6 按 Python 3.11 和通用平台条件生成，应用仍通过 pip 安装依赖。

可运行以下仓库已有的检查：

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests
npm ci
npm run spec:validate
npm --prefix web ci
npm --prefix web run lint
npm --prefix web run typecheck
npm --prefix web test
```

Docker 构建固定 Node.js 与 Python 基础镜像的公开版本和 digest，运行镜像使用 `linux/amd64`（x64）。修改基础镜像版本或 digest 时，应先确认所选公开镜像支持该架构，再更新 Dockerfile。CI 与发布复用 GHCR 中的构建缓存；缓存标签只供构建使用，不能作为应用版本部署。CI 和标签发布约定见 [发布说明](docs/releases.md)。
