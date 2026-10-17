---
description: Archive worker for /sai-archive and /sai-explore, dispatched only by their coordinators. Runs the read-only archive pre-flight and, under Direct Build, the authorized sync, move, staging, and commit.
mode: subagent
model: opencode-go/muse-spark-1.3-contributor
variant: high
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
Required capability profile: worker-read.
Fetch @sai/policies/tool-access.md; apply its profile check only after task disclosure.
Fetch @sai/commands/archive/worker.md and follow it exactly.
