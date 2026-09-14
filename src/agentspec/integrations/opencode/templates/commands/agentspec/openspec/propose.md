---
description: Propose a new OpenSpec change with strict tasks
agent: agentspec-openspec-orchestrator
subagent: true
subtask: true
---

<!-- agentspec:managed -->

Handle the AgentSpec OpenSpec propose operation for change: $ARGUMENTS

Run the fixed route exactly once, in order:

1. Scaffold the change with `openspec new change "$ARGUMENTS"`.
2. Create proposal, specs, and design, delegating to reasoning and
   architecture as needed.
3. Compile `tasks.md` ONLY through `agentspec-openspec-taskwriter`. The
   stock minimal task template is forbidden.
4. Audit the change through `agentspec-openspec-auditor`.
5. Finish by running `agentspec openspec validate --change "$ARGUMENTS" --json`
   and report success only on PASS.
