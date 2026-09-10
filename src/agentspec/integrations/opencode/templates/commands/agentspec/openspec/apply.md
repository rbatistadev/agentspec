---
description: Audit and apply an OpenSpec change
agent: agentspec-openspec-orchestrator
subagent: true
subtask: true
---

<!-- agentspec:managed -->

Handle the AgentSpec OpenSpec apply operation for change: $ARGUMENTS

Do not implement unless a fresh AgentSpec audit returns exact status PASS.
After PASS, route through the installed OpenSpec apply-change workflow.
