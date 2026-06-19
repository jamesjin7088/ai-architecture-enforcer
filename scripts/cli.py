#!/usr/bin/env python3
"""CLI entry point used by the plugin's skills.

Usage:
    cli.py --root <path> --full     # scan the whole project, print a report
    cli.py --root <path> --init     # scaffold a .architecture.json from detected folders
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arch_lib  # noqa: E402

COMMON_LAYER_DIRS = [
    ("domain", ["src/domain/**", "domain/**"]),
    ("application", ["src/application/**", "src/app/**", "application/**"]),
    ("infra", ["src/infra/**", "src/infrastructure/**", "infra/**", "infrastructure/**"]),
    ("adapters", ["src/adapters/**", "adapters/**"]),
    ("presentation", ["src/presentation/**", "src/ui/**", "presentation/**"]),
]


def cmd_full(root):
    config = arch_lib.find_config(root)
    if config is None:
        print(f"no {arch_lib.CONFIG_FILENAME} found in {root} — nothing to check.")
        print("Run the arch-init skill to scaffold one.")
        return 0

    violations, cycles, truncated = arch_lib.run_full_scan(root, config)

    if not violations and not cycles:
        print("Architecture check passed: no violations found.")
        return 0

    if violations:
        print(f"Found {len(violations)} architecture violation(s):\n")
        for v in violations:
            print(f"  {v['file']}:{v['line']}  {v['message']}")

    if cycles:
        print(f"\nFound {len(cycles)} circular import chain(s):\n")
        for cycle in cycles:
            print("  " + " -> ".join(cycle))
        if truncated:
            print("  ... (more cycles exist but were not shown, capped for performance)")

    return 1


def cmd_init(root):
    root = Path(root)
    config_path = root / arch_lib.CONFIG_FILENAME
    if config_path.exists():
        print(f"{config_path} already exists — not overwriting.")
        return 1

    layers = []
    for name, candidate_patterns in COMMON_LAYER_DIRS:
        for pattern in candidate_patterns:
            base = pattern.split("/**")[0]
            if (root / base).is_dir():
                layers.append({"name": name, "paths": [pattern], "forbiddenImports": []})
                break

    if layers:
        # Conservative default: domain must not import from anything below it.
        names = {layer["name"] for layer in layers}
        for layer in layers:
            if layer["name"] == "domain":
                layer["forbiddenImports"] = [
                    f"{other['paths'][0]}" for other in layers if other["name"] != "domain"
                ]

    config = {
        "maxLinesPerFile": 300,
        "excludePaths": arch_lib.DEFAULT_EXCLUDE_PATHS,
        "checkCircularDeps": True,
        "layers": layers,
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Wrote {config_path}")
    if not layers:
        print(
            "No common layer directories were auto-detected. "
            "Edit the 'layers' array to describe your project's structure."
        )
    else:
        print(f"Detected layers: {', '.join(l['name'] for l in layers)}. Review and adjust forbiddenImports.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true")
    group.add_argument("--init", action="store_true")
    args = parser.parse_args()

    if args.full:
        sys.exit(cmd_full(args.root))
    else:
        sys.exit(cmd_init(args.root))


if __name__ == "__main__":
    main()
