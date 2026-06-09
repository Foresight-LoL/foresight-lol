"""Static check that every third-party import in the project resolves in the
current environment.

Parses each .py file's imports with `ast`, drops stdlib and local packages,
and verifies the rest with `importlib.util.find_spec` — without executing any
module code (so DB/API connections at import time are never triggered).

Exits non-zero if any imported package is not installed. Intended for CI, but
runnable locally: `python scripts/check_imports.py`.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib
import sys

# Top-level project packages/dirs — imports of these are "local", not deps.
LOCAL = {"utils", "sample", "tests", "scripts"}
EXCLUDE_DIRS = {".venv", "venv", ".git", "__pycache__", "notebooks"}

ROOT = pathlib.Path(__file__).resolve().parent.parent


def iter_py_files() -> list[pathlib.Path]:
    return [
        f
        for f in ROOT.rglob("*.py")
        if not EXCLUDE_DIRS & set(f.relative_to(ROOT).parts)
    ]


def collect_imports() -> dict[str, set[str]]:
    imports: dict[str, set[str]] = {}
    for f in iter_py_files():
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            print(f"SYNTAX ERROR in {f}: {e}", file=sys.stderr)
            raise SystemExit(2)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.setdefault(alias.name.split(".")[0], set()).add(str(f))
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:  # absolute import only
                    imports.setdefault(node.module.split(".")[0], set()).add(str(f))
    return imports


def main() -> int:
    stdlib = set(sys.stdlib_module_names)
    missing: dict[str, set[str]] = {}

    for mod, files in sorted(collect_imports().items()):
        if mod in stdlib or mod in LOCAL:
            continue
        if importlib.util.find_spec(mod) is None:
            missing[mod] = files

    if not missing:
        print("OK: all third-party imports resolve in this environment.")
        return 0

    print("MISSING packages (imported but not installed):\n", file=sys.stderr)
    for mod, files in missing.items():
        print(f"  {mod}", file=sys.stderr)
        for fl in sorted(files):
            print(f"      used in {fl}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
