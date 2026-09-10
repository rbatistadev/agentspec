---
description: Create the next required artifact for an OpenSpec change
agent: agentspec-openspec-orchestrator
subagent: true
subtask: true
---

<!-- agentspec:managed -->

Handle the AgentSpec OpenSpec continue operation for change: $ARGUMENTS

Inspect current state first and create exactly one next artifact. Route tasks
only to the AgentSpec taskwriter and require its deterministic lint PASS.
