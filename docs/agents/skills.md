# 项目工程技能

Matt Pocock 工程类技能及 grilling、writing-for-agents、wait-what 来自 https://github.com/mattpocock/skills ，固定来源提交为 5beb35b040e3de97e54fa9e386d7e42d15c295c2，使用 skill-installer 安装至本项目 .agents/skills/。来源许可证保存在同目录的 MATT-POCOCK-LICENSE。

本项目适配：领域建模及设计审查统一读取 OpenSpec 规范和相关变更设计；设计记录使用 Decisions。事项与任务使用本地 OpenSpec，具体见 issue-tracker.md。目录图使用 Mermaid。上游更新时保留这些项目规则及用户授权边界，检查差异后更新，不覆盖本地适配。

OpenSpec CLI 是根 package.json 中的开发依赖，使用 npm run spec；项目工具初始化只生成当前仓库的 openspec/ 和 .agents/skills/openspec-*，没有安装全局工具或修改其他项目。配置与校验使用项目内版本。

Codex 元数据使用支持的字段：上游需要手动调用的技能通过 agents/openai.yaml 中的 allow_implicit_invocation: false 保持此行为。OpenSpec 技能依赖本项目 CLI，命令中的 openspec 通过 npm run spec -- 调用。

OpenSpec 负责规范与变更生命周期；Matt 的技能提供讨论、建模、测试、诊断和审查方法。需要调用技能而当前工具没有专用 Skill 入口时，读取项目内相应 SKILL.md 及其要求的引用文件，按指令执行。技能不扩大用户给定的修改、外部写入或测试权限。
