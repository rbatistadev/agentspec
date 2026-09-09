<p align="center">
  <h1 align="center">agentspec</h1>
  <p align="center"><em>Reusable agent harness instructions and integrations for OpenSpec-driven development.</em></p>
</p>

<p align="center">
  <a href="https://github.com/rbatistadev/agentspec/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/agentspec/"><img src="https://img.shields.io/pypi/v/agentspec.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/agentspec/"><img src="https://img.shields.io/pypi/pyversions/agentspec.svg" alt="Python versions"></a>
</p>

<p align="center">
  <strong>⚠️ Alpha — not production-ready.</strong><br>
  APIs and file formats may change without notice. Use with care.
</p>

---

## What is agentspec?

`agentspec` is a command-line tool that installs and maintains a standardized
agent harness on top of your existing [OpenSpec](https://github.com/Fission-AI/OpenSpec)
and [OpenCode](https://opencode.ai) setup. It gives every agent in your
development process a shared, deterministic set of instructions and
integration files, so the whole team (human and machine) follows the same
rules.

It does **not** replace OpenSpec or OpenCode — it sits alongside them and
manages the reusable configuration they consume.

## Features

- **Managed harness files** — installs and keeps up to date a global
  `AGENTS.md` section plus a set of OpenCode subagents, using non-destructive
  managed blocks that never overwrite your own content.
- **OpenSpec agent pipeline** — ships ready-made subagents for the
  recon → reason → architect → task-writer → auditor flow
  (`openspec-recon`, `openspec-reason`, `openspec-architect`,
  `openspec-taskwriter`, `openspec-auditor`).
- **`tasks.md` strict linter** — a deterministic structural linter for
  OpenSpec `tasks.md` execution packets, with human-readable or JSON output.
- **Environment diagnostics** — `doctor` checks that `openspec`, `opencode`,
  and `git` are present and reports the resolved configuration paths.
- **Safe by default** — `setup --dry-run` shows exactly what would change,
  and refuses to modify files that are not marked as owned by AgentSpec.

## Requirements

- Python **3.11** or later
- [OpenCode](https://opencode.ai) CLI
- [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI
- [Git](https://git-scm.com/)

## Installation

> Recommended: install in an isolated environment.

```bash
pip install agentspec
```

Or, for the latest development state:

```bash
git clone https://github.com/rbatistadev/agentspec.git
cd agentspec
pip install -e .
```

## Usage

```
agentspec <command>
```

### `agentspec doctor`

Check that the required tools are available and show the configuration
paths AgentSpec resolves on your machine.

```bash
agentspec doctor
```

### `agentspec setup`

Install or update the AgentSpec-managed harness files (the global `AGENTS.md`
block and the OpenCode subagents). Preview the changes first with `--dry-run`:

```bash
agentspec setup --dry-run
agentspec setup
```

### `agentspec openspec tasks lint`

Lint an OpenSpec `tasks.md` execution packet for structural correctness
against the `strict-v1` contract.

```bash
# By path
agentspec openspec tasks lint openspec/changes/my-change/tasks.md

# By change name (resolved from the repository root)
agentspec openspec tasks lint --change my-change

# Machine-readable output
agentspec openspec tasks lint --change my-change --json
```

The linter validates, among other things: required metadata
(`task-contract`, `planning-baseline`, `openspec-change`), mandatory task
sections, tracked checkboxes with deterministic verification commands,
dependency ordering and cycles, unresolved placeholders, and file/change path
consistency. Exit code `0` means pass, `1` means errors were found.

## How it works

`agentspec` resolves the machine-level configuration directories for OpenSpec
and OpenCode (honoring `XDG_CONFIG_HOME`, `APPDATA`, and
`OPENCODE_CONFIG_DIR`), then computes a plan of what should exist in the
OpenCode config directory:

- a managed section in the global `AGENTS.md`;
- one managed file per bundled subagent (each carrying an
  `<!-- agentspec:managed -->` marker).

Each managed file is only created or updated if it is either absent or already
owned by AgentSpec, so your own configuration is never clobbered.

## Project structure

```
src/agentspec/
  cli.py                 # CLI entry point
  commands/              # doctor, setup
  core/                  # path resolution, managed blocks, process helpers
  harness/openspec/      # tasks.md strict linter
  integrations/
    opencode/            # plan/apply logic + agent templates
    openspec/            # OpenSpec base configuration templates
tests/
  unit/                  # unittest-based unit tests
docs/
```

## Development

Run the tests:

```bash
python -m unittest discover -s tests
```

## Roadmap

`agentspec` is in **alpha**. Current focus:

- Stabilize the managed-file contract and the `strict-v1` tasks linter.
- Expand `openspec` integration (base configuration bootstrapping).
- Add coverage for the setup/apply flow.

## License

Apache License 2.0. See [LICENSE](LICENSE).
