# Local OpenSpec Tracker

Read `docs/agents/issue-tracker.md`. This project's local work lives under openspec/changes/; the current behavior lives under openspec/specs/.

Publishing a spec updates a change's proposal.md, specs/ and design.md. Publishing tickets updates numbered task checkboxes in its tasks.md, preserving real blocking dependencies and acceptance conditions. For a task too large to explain inline, link a detail file within that change.

Fetching a ticket means reading its change, task and linked context. Claims and triage state stay with the change. Completion is represented by the task checkbox. For large planning work, keep the decision map in the same change and point tasks at it.

A completed implementation is validated, synchronized to current specifications and archived through OpenSpec. Do not create external tracker items without explicit user authorization.
