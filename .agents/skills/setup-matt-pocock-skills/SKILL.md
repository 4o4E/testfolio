---
name: setup-matt-pocock-skills
description: Configure the project's engineering skills using its chosen local OpenSpec tracker and documentation rules.
---

# Setup Matt Pocock's Skills

Inspect the existing AGENTS.md or CLAUDE.md, project skill directories, OpenSpec config and docs/agents/ before editing anything. Preserve the instruction file already used by the project.

This project uses local OpenSpec for requirements, design decisions and tasks. Read docs/agents/issue-tracker.md and docs/agents/domain.md, and keep the Agent skills pointers in AGENTS.md current. Business vocabulary stays in GLOSSARY.md. Triage status vocabulary is in docs/agents/triage-labels.md.

Use the configured choices when already established. If the user asks to change tracker, documentation layout or installation scope, describe the concrete proposed changes and confirm before replacing the configuration. Do not create external issues, labels or pull requests merely as setup work.

Keep skills within .agents/skills/. Record source and local adaptations in docs/agents/skills.md. Explain what changed and when the project skills are available.
