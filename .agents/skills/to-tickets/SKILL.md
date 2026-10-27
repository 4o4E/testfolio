---
name: to-tickets
description: Break an approved OpenSpec change into verifiable vertical tasks with explicit blocking dependencies.
---

# To Tickets

Read docs/agents/issue-tracker.md, the current change's proposal, specs and design, and the relevant implementation. Use the established glossary vocabulary.

Break the agreed behavior into narrow end-to-end tasks. Each task must produce an independently observable outcome, include the layers actually needed, and state how to verify it. Do not add schema, interface or refactoring work that the outcome does not require.

Identify real blocking dependencies and opportunities for independent work. Mechanical changes that cannot be safely split should remain one bounded task with an integration check.

Present any breakdown that materially changes scope or acceptance for confirmation. Do not repeat settled product questions merely to create an interview.

Publish approved tasks as stable numbered checkboxes in the change's tasks.md. Include blocking task identifiers and acceptance conditions with each task, or link necessary detail within the same change. Update existing tasks rather than making a competing plan. Do not create external tickets without explicit authorization.
