"""Core static-analysis engine for ai-architecture-enforcer.

Stdlib only, no third-party dependencies, so it runs anywhere python3 runs.
"""
import fnmatch
import json
import os
import re
from pathlib import Path

CONFIG_FILENAME = ".architecture.json"

SCAN_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

DEFAULT_EXCLUDE_PATHS = ["node_modules", "dist", "build", ".git", "vendor", "__pycache__", ".venv", "venv"]

_JS_IMPORT_PATTERNS = [
    re.compile(r"""\bimport\s+(?:[\w*{}\s,]+\s+from\s+)?['"](?P<path>[^'"]+)['"]"""),
    re.compile(r"""\brequire\(\s*['"](?P<path>[^'"]+)['"]\s*\)"""),
    re.compile(r"""\bexport\s+[\w*{}\s,]*\s+from\s+['"](?P<path>[^'"]+)['"]"""),
]

_PY_IMPORT_PATTERNS = [
    re.compile(r"""^\s*from\s+(?P<path>[.\w]+)\s+import\b"""),
    re.compile(r"""^\s*import\s+(?P<path>[.\w]+)"""),
]


def find_config(start_dir):
    """Search start_dir (and only start_dir) for the config file. Returns dict or None."""
    config_path = Path(start_dir) / CONFIG_FILENAME
    if not config_path.is_file():
        return None
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    config.setdefault("maxLinesPerFile", None)
    config.setdefault("excludePaths", [])
    config.setdefault("checkCircularDeps", True)
    config.setdefault("layers", [])
    config["excludePaths"] = list(dict.fromkeys(DEFAULT_EXCLUDE_PATHS + config["excludePaths"]))
    return config


def match_pattern(path_str, pattern):
    if fnmatch.fnmatch(path_str, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        if path_str == prefix or path_str.startswith(prefix + "/"):
            return True
    return False


def to_rel_posix(path, root):
    return str(Path(path).resolve().relative_to(Path(root).resolve())).replace(os.sep, "/")


def should_exclude(rel_dir_posix, exclude_paths):
    if rel_dir_posix in ("", "."):
        return False
    parts = rel_dir_posix.split("/")
    if any(part in exclude_paths for part in parts):
        return True
    return any(rel_dir_posix == ex or rel_dir_posix.startswith(ex.rstrip("/") + "/") for ex in exclude_paths)


def iter_source_files(root, exclude_paths):
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = str(Path(dirpath).relative_to(root)).replace(os.sep, "/")
        dirnames[:] = [
            d for d in dirnames if not should_exclude((rel_dir + "/" + d).lstrip("/"), exclude_paths)
        ]
        for name in filenames:
            if Path(name).suffix in SCAN_EXTENSIONS:
                yield Path(dirpath) / name


def find_layer(rel_path, layers):
    for layer in layers:
        for pattern in layer.get("paths", []):
            if match_pattern(rel_path, pattern):
                return layer
    return None


def extract_imports(file_path):
    """Returns list of (line_no, raw_import_path)."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    results = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        matched = False
        for pat in _JS_IMPORT_PATTERNS:
            m = pat.search(line)
            if m:
                results.append((lineno, m.group("path")))
                matched = True
                break
        if matched:
            continue
        for pat in _PY_IMPORT_PATTERNS:
            m = pat.match(line)
            if m:
                results.append((lineno, m.group("path").replace(".", "/")))
                break
    return results


def resolve_import(file_path, root, raw_path):
    """Best-effort resolution of an import string to a root-relative posix path. Returns None if unresolvable."""
    root = Path(root).resolve()
    if raw_path.startswith("."):
        candidate = (file_path.parent / raw_path).resolve()
        try:
            return str(candidate.relative_to(root)).replace(os.sep, "/")
        except ValueError:
            return None
    candidate_str = raw_path.replace("\\", "/").lstrip("/")
    return candidate_str


def resolve_import_to_file(file_path, root, raw_path):
    """Like resolve_import, but only returns a path if it actually maps to a real source file in the repo."""
    resolved = resolve_import(file_path, root, raw_path)
    if resolved is None:
        return None
    root = Path(root)
    candidates = [resolved] + [f"{resolved}{ext}" for ext in SCAN_EXTENSIONS]
    candidates += [f"{resolved}/index{ext}" for ext in SCAN_EXTENSIONS]
    for c in candidates:
        p = root / c
        if p.is_file():
            return str(p.resolve().relative_to(root.resolve())).replace(os.sep, "/")
    return None


def check_line_count(file_path, root, max_lines):
    if not max_lines:
        return None
    try:
        line_count = sum(1 for _ in file_path.open(encoding="utf-8", errors="ignore"))
    except OSError:
        return None
    if line_count > max_lines:
        return {
            "file": to_rel_posix(file_path, root),
            "line": 1,
            "message": f"file has {line_count} lines, exceeds max {max_lines}",
        }
    return None


def check_import_direction(file_path, root, layers):
    rel_path = to_rel_posix(file_path, root)
    layer = find_layer(rel_path, layers)
    if layer is None:
        return []
    forbidden = layer.get("forbiddenImports", [])
    if not forbidden:
        return []
    violations = []
    for lineno, raw in extract_imports(file_path):
        resolved = resolve_import(file_path, root, raw)
        if resolved is None:
            continue
        for pattern in forbidden:
            if match_pattern(resolved, pattern):
                violations.append({
                    "file": rel_path,
                    "line": lineno,
                    "message": (
                        f"layer '{layer.get('name', '?')}' must not import '{raw}' "
                        f"(matches forbidden pattern '{pattern}')"
                    ),
                })
                break
    return violations


def find_circular_imports(root, config, max_cycles=20):
    exclude_paths = config.get("excludePaths", DEFAULT_EXCLUDE_PATHS)
    root = Path(root)
    graph = {}
    for file_path in iter_source_files(root, exclude_paths):
        rel = to_rel_posix(file_path, root)
        edges = set()
        for _, raw in extract_imports(file_path):
            target = resolve_import_to_file(file_path, root, raw)
            if target and target != rel:
                edges.add(target)
        graph[rel] = edges

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    stack = []
    cycles = []

    def visit(node):
        if len(cycles) >= max_cycles:
            return
        color[node] = GRAY
        stack.append(node)
        for neighbor in graph.get(node, ()):
            if len(cycles) >= max_cycles:
                break
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                idx = stack.index(neighbor)
                cycles.append(stack[idx:] + [neighbor])
            elif color[neighbor] == WHITE:
                visit(neighbor)
        stack.pop()
        color[node] = BLACK

    for node in list(graph):
        if color[node] == WHITE and len(cycles) < max_cycles:
            visit(node)

    truncated = len(cycles) >= max_cycles
    return cycles[:max_cycles], truncated


def run_full_scan(root, config):
    """Returns (violations: list[dict], cycles: list[list[str]], truncated: bool)."""
    exclude_paths = config.get("excludePaths", DEFAULT_EXCLUDE_PATHS)
    layers = config.get("layers", [])
    max_lines = config.get("maxLinesPerFile")
    violations = []
    for file_path in iter_source_files(root, exclude_paths):
        line_violation = check_line_count(file_path, root, max_lines)
        if line_violation:
            violations.append(line_violation)
        violations.extend(check_import_direction(file_path, root, layers))

    cycles, truncated = ([], False)
    if config.get("checkCircularDeps", True):
        cycles, truncated = find_circular_imports(root, config)

    return violations, cycles, truncated


def check_single_file(file_path, root, config):
    """Used by the PostToolUse hook: cheap, file-scoped checks only (no repo-wide circular-dep scan)."""
    violations = []
    max_lines = config.get("maxLinesPerFile")
    line_violation = check_line_count(file_path, root, max_lines)
    if line_violation:
        violations.append(line_violation)
    violations.extend(check_import_direction(file_path, root, config.get("layers", [])))
    return violations
