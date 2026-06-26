---
name: arch-check
description: Run a full architecture compliance scan of the current project (file size limits, layer import direction, circular dependencies) and report violations.
disable-model-invocation: false
---

Run a full architecture scan of the current project using this plugin's checker:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cli.py" --root "$(pwd)" --full
```

If the command reports "no .architecture.json found", tell the user this project has no
architecture rules configured yet and suggest running the `arch-init` skill instead of
inventing rules yourself.

Otherwise, summarize the output for the user:
- The scan separates **errors** (forbidden imports, circular deps, files over the hard limit
  that hold more than one responsibility) from **advisory warnings** (files over the soft
  limit, or over the hard limit but made of a single cohesive unit). Keep that distinction
  in your summary — errors should be fixed before merging; warnings are soft cohesion
  signals, not failures.
- List each violation with its file path and line number.
- Group violations by type (file size, forbidden import, circular dependency).
- For each violation, propose a concrete fix (e.g. which file to move, which import to
  remove or invert) rather than just repeating the raw message.
- For file-size findings, lead with cohesion, not the number: ask whether the file carries
  more than one responsibility, and only suggest a split when it does. Never advise
  splitting a single large function/class just to get under the limit.
- Do not modify any files unless the user asks you to fix the violations.
