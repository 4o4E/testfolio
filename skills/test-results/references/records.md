# 录入接口与记录格式

运行 `python3 <本skill目录>/scripts/client.py --help` 查看命令。服务网址来自私有客户端配置 `read_url` 和 `write_url`；配置文件默认位于 `~/.config/test-results/client.json`，也可通过 `--config` 或 `TEST_RESULTS_CONFIG` 指定，文件权限为 600。客户端使用 Python 标准库，无额外安装依赖。所有时间使用带时区的 ISO8601。

使用 `link --project <项目编号> --run <轮次编号> [--case <用例编号>]` 生成页面路径链接；项目、轮次和可选用例编号会进行 URL 编码，页面主机来自配置中的 `read_url`。

## 用例目录

`catalog --file catalog.json` 的正文：

```json
{
  "project": {"id":"project-id","title":"项目名称","description":"测试范围"},
  "cases": [{
    "id":"CASE-01","project_id":"project-id","title":"具体业务行为",
    "path":["业务模块","操作场景"],"requirement":"PRD要求和来源",
    "preconditions":["所需身份和测试资料"],
    "steps":[{"action":"执行具体操作","expected":"可以判定的预期结果"}],
    "priority":"P1","tags":["页面"],"source":"需求或规范路径"
  }]
}
```

用例更新保持未列出的用例，不会删除历史结果。priority 为 P0、P1、P2。

## 测试轮次

`start --file run.json` 的正文：

```json
{
  "id":"project-round-01","project_id":"project-id",
  "title":"本轮测试内容","environment":"实际目标环境名称",
  "kind":"browser","started_at":"2026-10-26T19:00:00+08:00",
  "versions":{"服务名":"实际版本"},"scope_case_ids":["CASE-01"],
  "summary":"本轮范围与准备情况","source":"实际运行记录路径"
}
```

kind 为 browser、blackbox、whitebox 或 import。scope_case_ids 使用已有真实用例编号，轮次开始后定义快照固定。版本从实际运行读取，不能用期望发布版本代替。

## 结果与证据

先执行 `artifact --file screenshot.png`，返回 artifact_id 和 media_type。结果中的附件使用返回编号；caption 说明画面能证明什么。报告附件使用实际 media_type；普通文本或 Markdown 也支持。附件通过系统复制保存，不依赖临时目录长期存在。

核对已有附件时使用 `download --artifact <编号> --output <当前工作区已登记临时目录中的新文件>`，然后读取报告或查看截图。输出文件已存在时会拒绝覆盖。

`result --run <轮次> --file result.json` 的正文：

```json
{
  "case_id":"CASE-01","status":"passed","actual":"实际观察到的完整结果",
  "steps":[{
    "action":"实际执行的操作","expected":"对应预期",
    "actual":"观察结果","status":"passed",
    "evidence":[{"artifact_id":"上传返回的编号","caption":"结果画面","media_type":"image/png"}]
  }],
  "evidence":[],"issues":[],
  "recorded_at":"2026-10-26T19:05:00+08:00","notes":"测试数据清理与限制"
}
```

status 为 passed、failed、blocked、not_run、skipped。问题使用 `issues:[{"title":"具体问题","url":"相关Issue链接"}]`。

需要标出按钮时，在图像 Evidence 上增加 `marks:[{"x":100,"y":200,"w":80,"h":40,"label":1}]`；需要局部显示时增加 `crop:{"x":80,"y":180,"w":600,"h":400}`。坐标对应原图像素；先读取原图确定位置。页面仍可打开完整原图。

同一轮同一用例重放完全相同的结果是幂等操作，内容不同返回409。完成轮次后不允许补写；创建新轮次复测，保留原来的实际结果。尚未提交结果的范围内用例显示未测试。
