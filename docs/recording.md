# 真实测试录入流程

此流程适用于通过 Testfolio 页面查看、通过客户端或 skill 录入记录的团队。开始前，确认用户指定的项目、环境、测试范围、版本和实际操作授权。Testfolio 的写入令牌只允许写入 Testfolio 记录，不代表对被测系统的操作授权。

## 安装与连接

安装仓库中的 `skills/test-results/` skill，并确认运行 Agent 的机器可以访问配置中的查看与录入服务。客户端默认读取 `~/.config/test-results/client.json`；可使用 `TEST_RESULTS_CONFIG` 环境变量或命令行 `--config` 指向其他私有配置文件。

先读取现有项目、用例和历史轮次：

```bash
python3 skills/test-results/scripts/client.py projects
python3 skills/test-results/scripts/client.py cases --project <项目编号>
python3 skills/test-results/scripts/client.py runs --project <项目编号>
```

根据实际项目维护用例目录。编号在项目内保持稳定；`catalog` 更新只影响明确提交的用例，未列出的用例会保留。不能把尚未执行的用例写成通过。

## 新建目录与轮次

通过 `catalog --file` 提交项目和用例定义 JSON。下方为**格式示例**，项目名、编号、描述和步骤都是用于说明字段的虚构内容，不代表真实项目或执行结果：

```json
{
  "project": {
    "id": "demo-project",
    "title": "格式示例项目",
    "description": "仅用于说明 JSON 字段"
  },
  "cases": [
    {
      "id": "demo-case-001",
      "project_id": "demo-project",
      "title": "格式示例用例",
      "path": ["示例目录"],
      "requirement": "此处填写实际需求",
      "preconditions": ["此处填写实际前置条件"],
      "steps": [
        {"action": "此处填写实际操作", "expected": "此处填写实际预期"}
      ],
      "priority": "P1",
      "tags": [],
      "source": "此处填写需求来源"
    }
  ]
}
```

将正文保存到本地 JSON 文件，例如 `catalog.json`，然后录入：

```bash
python3 skills/test-results/scripts/client.py catalog --file catalog.json
```

每次测试都新建轮次，明确环境、测试方式、实际服务版本、开始时间和范围。下面同样是**格式示例**，不是实际测试数据：

```json
{
  "id": "demo-run-001",
  "project_id": "demo-project",
  "title": "格式示例轮次",
  "environment": "此处填写实际环境",
  "kind": "browser",
  "started_at": "2026-01-01T00:00:00Z",
  "versions": {"service": "此处填写实际版本"},
  "scope_case_ids": ["demo-case-001"],
  "summary": "格式示例，不代表测试已执行",
  "source": "此处填写任务或需求来源"
}
```

保存为 `run.json` 后执行：

```bash
python3 skills/test-results/scripts/client.py start --file run.json
```

时间、版本、环境和用例范围应反映实际情况。不要复制示例值作为真实结果。

## 执行、截图和结果

按用例步骤在授权的目标环境中执行真实操作。记录实际观察，不要根据源码、预期或推测声称页面操作已经成功。浏览器测试保存能证明关键操作及结果的真实截图；接口测试记录实际请求和响应；白盒审查说明结论来自源码、日志还是数据库。必要时先对报告和截图中的个人信息、访问令牌等敏感内容脱敏。

每张截图或报告先上传并保存返回的附件编号：

```bash
python3 skills/test-results/scripts/client.py artifact --file ./evidence.png
```

将附件编号加入对应步骤或结果的 `evidence`。每项结果至少包含 `case_id`、状态、实际观察、步骤结果、证据数组、问题链接数组、记录时间和备注。`passed`、`failed` 必须写明实际观察；无法完成时使用 `blocked` 并解释原因；尚未尝试时使用 `not_run`；不适用时使用 `skipped` 并写明原因。每轮每个用例只能提交一次。

保存 Result JSON 后执行：

```bash
python3 skills/test-results/scripts/client.py result --run <轮次编号> --file result.json
```

完成用户授权范围内的资料清理后，用 `show` 复核轮次范围、结果数量、失败与未测试项及附件链接。随后结束轮次：

```bash
python3 skills/test-results/scripts/client.py show --run <轮次编号>
python3 skills/test-results/scripts/client.py finish \
  --run <轮次编号> \
  --state completed \
  --summary "此处填写实际完成情况"
```

如果工作无法继续，将状态设为 `interrupted` 并说明中断原因及已完成范围。`completed` 表示轮次工作已经结束，不表示所有用例均通过。需要复测时新建轮次，不改写已结束轮次。可使用 `link --project <项目编号> --run <轮次编号> [--case <用例编号>]` 生成查看链接。

## 批量导入

将 `catalog`、`artifacts` 与 `runs` 放入 bundle JSON。附件 `file` 路径相对于 bundle JSON 所在目录。每个轮次项包含 `run`、`results` 和 `finish`。下列仅展示结构，内容不是实际结果：

```json
{
  "catalog": {"project": {}, "cases": []},
  "artifacts": [{"id": "示例附件引用", "file": "evidence/example.png"}],
  "runs": [
    {"run": {}, "results": [], "finish": {"state": "completed", "summary": "格式示例"}}
  ]
}
```

通过 API 文档中描述的字段填充有效正文，然后运行：

```bash
python -m scripts.import_results --file /path/to/bundle.json
```

导入器会验证结构、附件及轮次冲突，再使用正常接口上传和录入。已结束轮次保持不变；运行中断后，使用相同 bundle 重试时会校验已有记录并继续未完成部分。内容冲突会停止，不会覆盖已有结果。导入过程只保存提供的记录，不会执行被测系统操作。
