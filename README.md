# ai-architecture-enforcer

A Claude Code plugin that keeps AI coding agents from quietly drifting away from your
project's architecture. You describe your layers and rules once in a small config file;
the plugin enforces them automatically while Claude works, and gives it tools to check
compliance on demand.

## What it does

- **Per-project rules, not hardcoded ones.** Define your own layers, import boundaries,
  file-size limit, and whether circular imports are allowed, in `.architecture.json` at
  your project root. No config file → the plugin does nothing (safe by default).
- **Enforced live, not just on request.** A `PostToolUse` hook checks every file Claude
  edits or writes against your rules and feeds violations back to Claude immediately, so
  it can self-correct instead of you finding out in review.
- **Rules are visible from the first turn.** A `SessionStart` hook summarizes the active
  rules into context automatically.
- **On-demand full scans and setup.** Two skills: `arch-init` to scaffold a config from
  your existing folder layout, and `arch-check` to run a full repo scan and report every
  violation.
- **Deep review for diffs.** An `architecture-reviewer` subagent for reviewing a set of
  changes specifically for architecture compliance (separate from general code review).

Checks performed: max lines per file, forbidden imports across layer boundaries, and
circular import chains. The import scanner understands JS/TS (`import`, `require`) and
Python (`import`, `from ... import`) syntax via regex — it's a fast heuristic linter, not
a full compiler, by design.

## Install

```
/plugin marketplace add jamesjin7088/ai-architecture-enforcer
/plugin install ai-architecture-enforcer@ai-architecture-enforcer
```

## Set up rules for your project

Inside a Claude Code session in your project:

```
Run arch-init
```

This inspects your folder structure, proposes a `.architecture.json` (see
`config/architecture.example.json` for the shape), and asks you to confirm it before
writing anything.

## Config reference

```jsonc
{
  "maxLinesPerFile": 300,
  "excludePaths": ["node_modules", "dist", "build", ".git", "vendor"],
  "checkCircularDeps": true,
  "layers": [
    {
      "name": "domain",
      "paths": ["src/domain/**"],
      "forbiddenImports": ["src/infra/**", "src/adapters/**"]
    }
  ]
}
```

- `layers[].paths` — glob patterns identifying which files belong to this layer.
- `layers[].forbiddenImports` — glob patterns this layer's files must never import from.
  A layer with no entry here has no import restrictions.
- `maxLinesPerFile` — set to `null` to disable the file-size check entirely.
- `excludePaths` are merged with a built-in default list (`node_modules`, `dist`, `build`,
  `.git`, `vendor`, `__pycache__`, `.venv`, `venv`).

## Manual checks

```
Run arch-check
```

or directly:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cli.py" --root . --full
```

## License

MIT
