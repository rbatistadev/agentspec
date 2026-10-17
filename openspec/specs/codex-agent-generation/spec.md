# Codex Agent Generation Specification

## Purpose

Generates managed Codex custom agent definitions from AgentSpec's agent
templates while assigning each agent an explicit model and reasoning effort, so
Codex agents do not inherit the parent session's model and reasoning settings.

## Requirements

### Requirement: Explicit per-agent model and reasoning effort

Every generated managed Codex agent definition SHALL declare an explicit `model`
and an explicit `model_reasoning_effort`. The generator SHALL emit both fields
together for every managed agent so that no managed agent falls back to the
parent session's model or inherits a previously resolved reasoning effort.

#### Scenario: Every managed agent emits both fields

- **WHEN** the Codex agent generator renders the managed agent definitions
- **THEN** each generated agent TOML contains a `model` field and a
  `model_reasoning_effort` field

#### Scenario: Model and effort are emitted together

- **WHEN** any managed agent is rendered
- **THEN** its `model` and `model_reasoning_effort` are emitted in the same
  definition and are not emitted independently

### Requirement: Fixed per-agent mapping

The generator SHALL assign each managed agent the model and reasoning effort
from AgentSpec's fixed per-agent policy, not from the parent session. The
mapping SHALL be exactly:

| Agent | model | model_reasoning_effort |
|---|---|---|
| agentspec-openspec-orchestrator | gpt-5.6-luna | low |
| agentspec-openspec-recon | gpt-5.6-terra | low |
| agentspec-openspec-apply-worker | gpt-5.6-luna | low |
| agentspec-openspec-reason | gpt-5.6 | high |
| agentspec-openspec-auditor | gpt-5.6 | high |
| agentspec-openspec-taskwriter | gpt-5.6 | high |
| agentspec-openspec-architect | gpt-5.6 | high |

#### Scenario: Orchestrator, recon, and apply-worker use the low-cost model

- **WHEN** the generator renders `agentspec-openspec-orchestrator`,
  `agentspec-openspec-recon`, or `agentspec-openspec-apply-worker`
- **THEN** the emitted `model_reasoning_effort` is `low` and the emitted `model`
  matches the mapping above

#### Scenario: Reason, auditor, taskwriter, and architect use high effort

- **WHEN** the generator renders `agentspec-openspec-reason`,
  `agentspec-openspec-auditor`, `agentspec-openspec-taskwriter`, or
  `agentspec-openspec-architect`
- **THEN** the emitted `model_reasoning_effort` is `high` and the emitted `model`
  matches the mapping above

### Requirement: Reasoning effort domain

The generator SHALL restrict `model_reasoning_effort` to the values `low`,
`medium`, and `high`. Higher tiers such as `xhigh`, `max`, or `ultra` SHALL NOT
be emitted.

#### Scenario: Emitted effort is within the allowed domain

- **WHEN** any managed agent is rendered
- **THEN** its `model_reasoning_effort` value is one of `low`, `medium`, or
  `high`

### Requirement: Fail closed for unmapped agents

If a managed agent has no entry in the per-agent mapping, generation SHALL fail
with an error. The generator SHALL NOT emit a definition without model and
effort, and SHALL NOT silently omit the agent.

#### Scenario: Unknown agent aborts generation

- **WHEN** the generator is asked to render a managed agent that has no mapping
- **THEN** generation raises an error instead of emitting a partial or missing
  definition

### Requirement: Sandbox policy unchanged

The generator SHALL preserve the existing sandbox policy: `apply-worker` and
`taskwriter` emit no `sandbox_mode` field, and every other managed agent emits
`sandbox_mode = "read-only"`.

#### Scenario: Writable agents omit sandbox_mode

- **WHEN** `agentspec-openspec-apply-worker` or
  `agentspec-openspec-taskwriter` is rendered
- **THEN** the generated TOML does not contain a `sandbox_mode` field

#### Scenario: Other agents remain read-only

- **WHEN** any managed agent other than `apply-worker` and `taskwriter` is
  rendered
- **THEN** the generated TOML contains `sandbox_mode = "read-only"`

### Requirement: Existing Codex fields preserved

Generated agent definitions SHALL retain the `# agentspec:managed` ownership
marker and the existing `name`, `description`, and `developer_instructions`
fields alongside the new `model` and `model_reasoning_effort` fields.

#### Scenario: Managed marker and base fields remain

- **WHEN** any managed agent is rendered
- **THEN** the output contains the `# agentspec:managed` marker and parses to a
  definition with `name`, `description`, `model`, `model_reasoning_effort`, and
  `developer_instructions`

### Requirement: OpenCode generation unchanged

Configuring per-agent model and effort for Codex SHALL NOT change the OpenCode
agent frontmatter or leak Codex model/effort values into OpenCode output. The
OpenCode `model`, `mode`, and `permissions` frontmatter fields MUST remain
byte-identical to their current values, and NO Codex `model` or
`model_reasoning_effort` value SHALL appear in any rendered OpenCode agent.

The architect escalation-body rewrite (see "Model-neutral architect escalation
guidance") is excluded from this guarantee: the architect template body IS
intentionally changed, and because the OpenCode renderer copies the template
body verbatim, the rendered OpenCode architect body changes too. That change is
accepted and intended.

#### Scenario: OpenCode frontmatter stays byte-identical

- **WHEN** the OpenCode agent generator renders the managed agents after this
  change
- **THEN** each rendered OpenCode agent's `model`, `mode`, and `permissions`
  frontmatter fields are byte-identical to their pre-change values

#### Scenario: No Codex model or effort value leaks into OpenCode output

- **WHEN** the OpenCode agent generator renders the managed agents after this
  change
- **THEN** no rendered OpenCode agent contains a Codex `model` or
  `model_reasoning_effort` value

#### Scenario: Architect escalation-body rewrite is intended

- **WHEN** the `agentspec-openspec-architect` agent body is rendered after this
  change
- **THEN** the rendered body reflects the model-neutral escalation rewrite and
  MAY differ from its pre-change output; this is intended and excluded from the
  frontmatter byte-identity guarantee

### Requirement: Model-neutral architect escalation guidance

The architect agent instructions SHALL describe escalation model-neutrally and
SHALL NOT name a specific model, so the same template remains valid across
integrations.

#### Scenario: Architect instructions name no model

- **WHEN** the `agentspec-openspec-architect` agent body is inspected
- **THEN** its escalation guidance refers to the strongest available reasoning
  model at maximum effort and does not name a specific model identifier