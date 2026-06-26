English | [한국어](README.ko.md)

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

Checks performed: file size (soft + hard line limits), forbidden imports across layer
boundaries, and circular import chains. The import scanner understands JS/TS (`import`,
`require`) and Python (`import`, `from ... import`) syntax via regex — it's a fast heuristic
linter, not a full compiler, by design.

## Cohesion first, line count second

Line count is a *proxy*; the real target is **one file = one responsibility + a good name**.
A well-named, cohesive 500-line file is friendlier to humans and agents than two 250-line
files that import each other, and splitting a single large function just to pass a line
budget makes a flow harder to follow, not easier. So the file-size check is deliberately
two-tiered and cohesion-aware:

- **`warnLinesPerFile` (soft signal, default 300)** — a non-blocking nudge: "is this still
  one responsibility?" It never fails a scan or blocks an edit.
- **`maxLinesPerFile` (hard limit, default 600)** — blocks, *unless* the file is a single
  cohesive unit.
- **`exemptSingleResponsibilityFile` (default true)** — a file over the hard limit that is
  one dominant definition (a single function or class) is downgraded to a warning instead of
  being forced to split. Detection uses Python's AST and a conservative JS/TS heuristic.

Every finding is tagged `error` or `warning`. The live hook only blocks on errors; warnings
are surfaced as advisory context. Set `warnLinesPerFile` to `null` to drop the soft signal,
or `exemptSingleResponsibilityFile` to `false` if you want a strict line cap.

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
  "maxLinesPerFile": 600,
  "warnLinesPerFile": 300,
  "exemptSingleResponsibilityFile": true,
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
- `maxLinesPerFile` — hard limit; over it is an `error` (blocks). Set to `null` to disable
  the hard file-size check entirely.
- `warnLinesPerFile` — soft signal; over it is a non-blocking `warning`. Set to `null` to
  disable the soft signal. See [Cohesion first](#cohesion-first-line-count-second) above.
- `exemptSingleResponsibilityFile` — when `true` (default), a file over the hard limit that
  is a single cohesive unit is downgraded to a warning rather than forced to split.
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
