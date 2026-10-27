---
name: domain-modeling
description: Sharpen the project's domain glossary and record confirmed design decisions in OpenSpec when terminology or architecture is being discussed.
---

# Domain Modeling

Read `docs/agents/domain.md`, `GLOSSARY.md`, and the relevant OpenSpec specifications and change design before changing domain language or decisions.

Challenge an overloaded term against its current definition. Use a concrete business scenario and inspect the actual code when a statement conflicts with existing behavior. Ask only about decisions that cannot be established from evidence.

After the user confirms a term's meaning, update GLOSSARY.md using [GLOSSARY-FORMAT.md](GLOSSARY-FORMAT.md). Keep the glossary about business meaning, not implementation.

Record confirmed architectural choices in the corresponding OpenSpec change's design.md, explaining the choice, rationale, meaningful alternatives and constraints. Use [DECISION-FORMAT.md](DECISION-FORMAT.md). Behavior contracts belong in that change's specs and execution work belongs in tasks.md.

Avoid documenting obvious reversible implementation details as architecture decisions. Preserve historical decisions in archived changes and surface a conflict before changing one.
