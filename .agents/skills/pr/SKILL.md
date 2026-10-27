---
name: pr
description: Write a pull request body grounded in the requested behavior, actual evidence and merge risk when the user requests a PR.
metadata:
  credits:
    skill: show-me
    author: Dex Horthy
    organisation: Humanlayer
    url: https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md
---

# Pull Request Description

Read the user's request, actual diff and relevant OpenSpec proposal, specs and design. Creating or publishing a PR requires user authorization and a real configured remote.

Explain the change in the user's business language. Use only as much structure as needed:

- Requested behavior and affected responsibilities.
- Actual verification evidence: relevant screenshots, command output or test results, distinguishing execution from inference.
- Merge risk, data compatibility, dependencies and rollback where relevant.

Use the smallest useful Mermaid diagram for relationships that need a diagram. Use prose or a short list when that is clearer. Do not fabricate verification output or add development handoff notes to application UI.

Follow the configured tracker for issue references. A reviewed design or draft PR body does not authorize merging, deploying or changing external issue state.
