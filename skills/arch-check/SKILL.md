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
- List each violation with its file path and line number.
- Group violations by type (file size, forbidden import, circular dependency).
- For each violation, propose a concrete fix (e.g. which file to move, which import to
  remove or invert) rather than just repeating the raw message.
- Do not modify any files unless the user asks you to fix the violations.
