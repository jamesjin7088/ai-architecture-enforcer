---
name: arch-init
description: Create an .architecture.json config for the current project so the ai-architecture-enforcer plugin can start enforcing architecture rules.
disable-model-invocation: false
---

Help the user set up architecture rules for this project.

1. Run the scaffolding command to auto-detect common layer directories (domain,
   application, infra, adapters, presentation):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cli.py" --root "$(pwd)" --init
   ```

2. Read the resulting `.architecture.json`. If layers were auto-detected, show them to the
   user and ask whether the detected layers and the default rule ("domain must not import
   from any other layer") match their intended architecture.

3. If the project doesn't match common hexagonal/layered naming, or the user wants a
   different structure, explore the actual folder layout yourself (e.g. `ls src`) and edit
   `.architecture.json` directly to reflect:
   - `layers`: each with a `name`, glob `paths`, and `forbiddenImports` (glob patterns the
     layer must not import from).
   - `maxLinesPerFile`: a sensible per-file line limit for this codebase (default 300).
   - `checkCircularDeps`: whether to flag circular imports (default true).
   - `excludePaths`: directories to skip (node_modules, dist, build, vendor, etc. are
     already excluded by default — only add project-specific ones).

4. Confirm the final config with the user before leaving it in place. Do not silently
   overwrite an existing `.architecture.json` — if one exists, show its contents and ask
   what they want changed instead of regenerating it.

5. Once confirmed, suggest running the `arch-check` skill to verify the project currently
   passes (or to see what it would need to fix).
