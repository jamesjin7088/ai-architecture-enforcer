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
   - `maxLinesPerFile`: the **hard** per-file line limit that blocks (default 600). The goal
     is one responsibility per file — line count is just a proxy, so keep this generous.
   - `warnLinesPerFile`: the **soft** line signal (default 300). Files over this get a
     non-blocking "is this still one responsibility?" nudge, not a failure. Set to `null` to
     turn the soft signal off.
   - `exemptSingleResponsibilityFile`: when true (default), a file over the hard limit that
     is a single cohesive unit (one dominant function/class) is downgraded to a warning
     instead of forcing a split. Leave this on unless you really want a strict line cap.
   - `checkCircularDeps`: whether to flag circular imports (default true).
   - `excludePaths`: directories to skip (node_modules, dist, build, vendor, etc. are
     already excluded by default — only add project-specific ones).

   When discussing limits with the user, explain that the primary criterion is "one file =
   one responsibility + a good name." Treat 300 as a smell signal and 600 as the hard cap;
   don't push for splits that just move lines around without separating responsibilities.

4. Confirm the final config with the user before leaving it in place. Do not silently
   overwrite an existing `.architecture.json` — if one exists, show its contents and ask
   what they want changed instead of regenerating it.

5. Once confirmed, suggest running the `arch-check` skill to verify the project currently
   passes (or to see what it would need to fix).
