---
description: Direct Build implementer for /sai-explore, dispatched only by its coordinator. Implements a change straight from its Ready to Propose block.
mode: subagent
model: opencode-go/deepseek-v4.1-flash
variant: max
permissions:
  - action: "*"
    resource: "*"
    effect: deny
  - action: "read"
    resource: "*"
    effect: allow
  - action: "glob"
    resource: "*"
    effect: allow
  - action: "grep"
    resource: "*"
    effect: allow
  - action: "edit"
    resource: "*"
    effect: allow
  - action: "codegraph_codegraph_explore"
    resource: "*"
    effect: allow
  - action: "execute"
    resource: "*"
    effect: allow
  - action: "skill"
    resource: "*"
    effect: allow
  - action: "shell"
    resource: "*"
    effect: allow
  - action: "external_directory"
    resource: "*"
    effect: ask
  - action: "external_directory"
    resource: "~/.config/opencode/*"
    effect: allow
  - action: "external_directory"
    resource: "/tmp/opencode/*"
    effect: allow
  - action: "external_directory"
    resource: "~/.local/share/opencode/tool-output/*"
    effect: allow
  - action: "external_directory"
    resource: "~/.local/share/opencode/shell/*"
    effect: allow
  - action: "read"
    resource: "*.env"
    effect: ask
  - action: "read"
    resource: "*.env.*"
    effect: ask
  - action: "read"
    resource: "*.env.example"
    effect: allow
---

Fetch @~/.config/opencode/skills/fetch/SKILL.md before you continue.
Required capability profile: worker-write.
Fetch @sai/policies/tool-access.md; apply its profile check only after task disclosure.
Fetch @sai/commands/explore/direct-build-worker.md and follow it exactly.
