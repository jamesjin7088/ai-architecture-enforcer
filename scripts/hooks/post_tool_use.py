#!/usr/bin/env python3
"""PostToolUse hook (matcher: Edit|Write): checks the just-edited file against
.architecture.json. Reports violations back to Claude via decision:block (the
edit already happened — this is feedback, not an actual block) so it can self-correct."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import arch_lib  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    cwd = payload.get("cwd") or "."
    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return

    config = arch_lib.find_config(cwd)
    if config is None:
        return

    target = Path(file_path)
    if target.suffix not in arch_lib.SCAN_EXTENSIONS or not target.is_file():
        return

    try:
        rel = arch_lib.to_rel_posix(target, cwd)
    except ValueError:
        return  # file is outside the project root, not our concern

    if arch_lib.should_exclude(str(Path(rel).parent), config.get("excludePaths", [])):
        return

    violations = arch_lib.check_single_file(target, cwd, config)
    if not violations:
        return

    reason = "Architecture violation(s) in " + rel + ":\n" + "\n".join(
        f"  line {v['line']}: {v['message']}" for v in violations
    )
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
