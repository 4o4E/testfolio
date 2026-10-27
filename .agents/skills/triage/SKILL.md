---
name: triage
description: Evaluate reported bugs and feature requests against actual behavior and record a clear next state in the project's OpenSpec tracker.
---

# Triage

Read docs/agents/issue-tracker.md, docs/agents/triage-labels.md and the relevant current specifications and change design. For a user-provided external issue or PR, read its full content and requested scope; external writes still require user authorization.

Distinguish bug and enhancement, and use one state: needs-triage, needs-info, ready-for-agent, ready-for-human, or wontfix. Preserve resolved facts and unanswered material questions when resuming.

1. Inspect the actual implementation and prior OpenSpec decisions. Search for an existing implementation before treating a request as new work.
2. For a bug, reproduce the reported behavior through the real public interface. Report evidence or the specific missing information; do not turn an assumption into a verified finding.
3. Explain the concrete business scenario and recommended state. Ask only for missing decisions that affect the outcome; do not re-ask facts available in code or documentation.
4. If clarification is needed, use grilling and domain-modeling. Record user-confirmed vocabulary in GLOSSARY.md and decisions in the change design.
5. Save the outcome in the configured local change. ready-for-agent needs a clear scope, acceptance conditions, dependencies and relevant evidence; needs-info needs actionable questions; ready-for-human explains the required manual action.
6. If the user rejects an enhancement, capture its scope and rationale using [OUT-OF-SCOPE.md](OUT-OF-SCOPE.md). Already implemented behavior is not a rejected feature.

A user-requested state change does not authorize code changes or external messages. For an explicitly authorized external triage comment, identify AI authorship and preserve the verified evidence and unresolved questions.
