#!/usr/bin/env python3
"""SessionStart hook: if the project has a .architecture.json, summarize the active
rules and inject them as additionalContext so the model knows about them from turn one."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arch_lib  # noqa: E402


def build_summary(config):
    lines = ["Architecture rules are enforced in this project (ai-architecture-enforcer plugin)."]
    if config.get("maxLinesPerFile"):
        lines.append(f"- Max {config['maxLinesPerFile']} lines per source file.")
    for layer in config.get("layers", []):
        forbidden = layer.get("forbiddenImports") or []
        paths = ", ".join(layer.get("paths", []))
        if forbidden:
            lines.append(f"- Layer '{layer['name']}' ({paths}) must NOT import: {', '.join(forbidden)}.")
        else:
            lines.append(f"- Layer '{layer['name']}' ({paths}) has no import restrictions.")
    if config.get("checkCircularDeps", True):
        lines.append("- Circular imports between source files are flagged.")
    lines.append("Edits are checked automatically; run the arch-check skill for a full report.")
    return "\n".join(lines)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd = payload.get("cwd") or "."

    config = arch_lib.find_config(cwd)
    if config is None:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": build_summary(config),
        }
    }))


if __name__ == "__main__":
    main()
