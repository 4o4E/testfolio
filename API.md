# Testfolio API

Testfolio 使用两个独立入口：查看服务的 `/api` 提供只读数据和页面；录入服务的 `/write` 接受需要私有令牌的写入请求。默认容器端口分别为 `8080` 与 `8081`。主机端口 `8081` 只绑定本机。

所有写入请求都需要请求头：

```http
Authorization: Bearer <TEST_RESULTS_WRITE_TOKEN>
```

令牌由 `scripts/setup_local.py` 生成，保存在私有配置中。不要将其放入 URL、命令行参数、项目记录或附件。

## 对象

`Project` 包含 `id`、`title` 和 `description`。`Case` 包含 `id`、`project_id`、`title`、目录数组 `path`、`requirement`、`preconditions`、步骤数组 `steps`、优先级 `P0|P1|P2`、`tags` 和 `source`。每个步骤包含 `action` 与 `expected`。

`Run` 包含 `id`、`project_id`、`title`、`environment`、测试方式 `kind: browser|blackbox|whitebox|import`、ISO 8601 时间 `started_at`、版本字典 `versions`、用例编号数组 `scope_case_ids`、`summary` 与 `source`。开始轮次时会保存范围内的用例定义快照。

`Result` 包含 `case_id`、状态 `passed|failed|blocked|not_run|skipped`、`actual`、逐步结果 `steps`、整体 `evidence`、问题链接 `issues`、ISO 8601 时间 `recorded_at` 与 `notes`。逐步结果包含 `action`、`expected`、`actual`、`status` 和 `evidence`。通过与失败结果必须记录实际观察。每轮每个用例只能提交一次；内容相同的重放返回既有结果，内容冲突返回 HTTP 409。复测请创建新轮次。

证据 `Evidence` 包含 `artifact_id`、`caption`，可选 `media_type`、`marks` 和 `crop`。媒体类型默认 `image/png`；标注和裁切坐标以原始图片像素计。附件上传支持 PNG、JPEG、WebP、PDF、纯文本、Markdown 与 JSON，单个上传上限为 32 MiB。

## 读取接口

| 方法与路径 | 返回内容 |
| --- | --- |
| `GET /health` | `{ "status": "ok" }` |
| `GET /api/projects` | 项目数组，包含 `id,title,description,case_count` |
| `GET /api/projects/{project_id}/cases` | 项目用例数组 |
| `GET /api/projects/{project_id}/runs` | 轮次数组，含 `state,finished_at,counts` |
| `GET /api/runs/{run_id}` | `{run,cases:[{case,result}],counts}` |
| `GET /api/projects/{project_id}/cases/{case_id}` | `{case,history:[{run,result}]}`，历史按开始时间倒序 |
| `GET /artifacts/{artifact_id}` | 受管附件 |

`counts` 包含 `passed`、`failed`、`blocked`、`not_run`、`skipped` 与 `total`。轮次范围内尚未提交结果的用例计为 `not_run`。

## 写入接口

| 方法与路径 | 正文与行为 |
| --- | --- |
| `PUT /write/catalog` | `{project,cases}`。更新指定项目和用例，未列出的现有用例保留；返回 `{project_id,case_count}`。 |
| `POST /write/runs` | Run 对象。创建轮次并返回 `state=running` 的轮次；重复编号会被拒绝。 |
| `POST /write/runs/{run_id}/results` | Result 对象。用例必须属于轮次范围，所引用附件必须已上传。 |
| `POST /write/runs/{run_id}/finish` | `{state:"completed"|"interrupted",summary}`。结束轮次；结束后不能补写结果。 |
| `POST /write/artifacts` | multipart 表单字段 `file`。返回 `{artifact_id,filename,media_type,url}`。 |

## 批量导入

可使用仓库内的导入命令：

```bash
python -m scripts.import_results --file /path/to/bundle.json
```

也可以用 `--config /path/to/client.json` 指定私有客户端配置；否则读取 `~/.config/test-results/client.json`。工具先验证输入结构、附件文件和轮次状态，再通过正常写入接口导入，不直接修改 SQLite，也不执行被测系统操作。

JSON 根对象必须包含 `catalog`、`artifacts` 和 `runs`：

- `catalog` 与 `PUT /write/catalog` 的正文相同。
- `artifacts` 是 `{id,file}` 数组。`file` 必须是相对于 bundle 文件所在目录的相对路径，文件必须位于该目录内。结果中的 `artifact_id` 可引用这里的 `id`，也可引用已保存在 Testfolio 中的附件编号。
- `runs` 是 `{run,results,finish}` 数组，分别对应创建轮次、结果数组和结束轮次的正文。

轮次编号在整个服务中唯一，建议包含项目编号。已结束轮次不会被修改；运行中的同编号轮次只有在轮次定义、用例定义及已有结果一致时才会继续。发生冲突时工具停止并拒绝覆盖。有关可复制的通用格式示例见 [录入流程](docs/recording.md)。

SQLite 文件位于 `TEST_RESULTS_DATA_DIR/test-results.sqlite3`，附件文件位于 `TEST_RESULTS_ARTIFACT_DIR`。Compose 示例将这两个目录映射到持久资源路径下的 `sqlite/` 和 `artifacts/`。单容器包含两个独立 FastAPI 应用：查看服务提供只读 API 和页面，录入服务提供写入 API 与健康接口。
