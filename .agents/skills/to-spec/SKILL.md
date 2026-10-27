---
name: to-spec
description: Turn the current conversation and inspected implementation into an OpenSpec proposal, behavior scenarios and design decisions.
---

# To Spec

Read docs/agents/issue-tracker.md, the relevant current OpenSpec specifications and the discussed implementation. Synthesize the user's actual request rather than starting a new interview.

Write the problem, intended user behavior and exclusions into the relevant change proposal. Define testable requirements and scenarios under that change's specs/. Put confirmed technical choices and trade-offs in design.md; leave unresolved decisions explicitly open.

Use existing public interfaces as verification surfaces. State what will be exercised and the expected observable results. Do not invent broad requirements or include implementation details in the behavior contract.

Publishing means saving these files to the project's local OpenSpec change. Preserve existing artifacts and task relationships. Report the artifact paths and remaining genuine decisions; creating a proposal does not itself authorize implementation or external tracker writes.
