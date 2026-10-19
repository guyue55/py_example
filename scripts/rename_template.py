#!/usr/bin/env python3
"""Rename the ``example`` placeholder package to a real package name.

This is a one-time helper for people who *use* this template. It performs the
mechanical rename so the generated project is immediately importable and
buildable under the new name.

What it does
------------
1. Moves ``src/example`` -> ``src/<name>``.
2. Updates the ``name`` field in ``pyproject.toml``.
3. Rewrites ``from example...`` / ``import example`` across all ``.py`` files
   (source + tests).
4. Updates ``src/example`` references in the docs.
5. Removes the "Template notice" block from README.md.
6. Rewrites the package ``__init__.py`` docstring.

The new name must be a valid Python package identifier: lowercase letters,
digits and underscores only, and it must not start with a digit.

Usage
-----
    python scripts/rename_template.py <new_package_name>
    python scripts/rename_template.py my_sdk --dry-run   # preview only
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_EXAMPLE = os.path.join(REPO_ROOT, "src", "example")

IMPORT_RE = re.compile(r"(from|import)\s+example(\s|\.|$)")
PYPROJECT_NAME_RE = re.compile(r'^name\s*=\s*"example"', re.MULTILINE)
INIT_DOCSTRING_RE = re.compile(r'""".*?"""', re.DOTALL)


def is_valid_package_name(name: str) -> bool:
    """Return True if ``name`` is a legal Python package identifier."""
    return bool(re.fullmatch(r"[a-z_][a-z0-9_]*", name))


def rewrite_imports(text: str, new_name: str) -> str:
    return IMPORT_RE.sub(lambda m: f"{m.group(1)} {new_name}{m.group(2)}", text)


def replace_pyproject_name(text: str, new_name: str) -> str:
    return PYPROJECT_NAME_RE.sub(f'name = "{new_name}"', text)


def remove_readme_notice(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("> **Template notice:**"):
            skipping = True
            continue
        if skipping:
            if stripped.startswith(">"):
                continue
            skipping = False
        out.append(line)
    return "".join(out)


def rewrite_init_docstring(text: str, new_name: str) -> str:
    match = INIT_DOCSTRING_RE.match(text)
    if not match:
        return text
    quote = '"""'
    new_doc = (
        f"{quote}{new_name} - A minimal Python SDK utility package.\n\n"
        f"This is the {new_name} package.\n{quote}\n"
    )
    return text[: match.start()] + new_doc + text[match.end() :]


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def collect_edits(new_name: str) -> list[tuple[str, str]]:
    """Return ``(path, new_content)`` for every file that needs changing."""
    edits: list[tuple[str, str]] = []

    # pyproject.toml
    pyproject = os.path.join(REPO_ROOT, "pyproject.toml")
    txt = read_text(pyproject)
    new = replace_pyproject_name(txt, new_name)
    if new != txt:
        edits.append((pyproject, new))

    # All Python files under src/ and tests/
    for base in ("src", "tests"):
        base_dir = os.path.join(REPO_ROOT, base)
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(root, fn)
                txt = read_text(fp)
                new = rewrite_imports(txt, new_name)
                if fp.endswith("__init__.py") and os.path.dirname(fp) == SRC_EXAMPLE:
                    new = rewrite_init_docstring(new, new_name)
                if new != txt:
                    edits.append((fp, new))

    # README.md
    readme = os.path.join(REPO_ROOT, "README.md")
    if os.path.exists(readme):
        txt = read_text(readme)
        new = rewrite_imports(remove_readme_notice(txt), new_name)
        new = new.replace("src/example", f"src/{new_name}")
        if new != txt:
            edits.append((readme, new))

    # developer_guide.md (Chinese guide references src/example path)
    guide = os.path.join(REPO_ROOT, "developer_guide.md")
    if os.path.exists(guide):
        txt = read_text(guide)
        new = txt.replace("src/example", f"src/{new_name}")
        if new != txt:
            edits.append((guide, new))

    return edits


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("package_name", help="new package name (valid Python identifier)")
    parser.add_argument("--dry-run", action="store_true", help="preview changes without writing")
    args = parser.parse_args()

    new_name = args.package_name
    if not is_valid_package_name(new_name):
        print(
            f"ERROR: '{new_name}' is not a valid Python package name.\n"
            "Use lowercase letters, digits and underscores only; "
            "it must not start with a digit."
        )
        return 1

    target = os.path.join(REPO_ROOT, "src", new_name)
    if os.path.exists(target):
        print(f"ERROR: target already exists: {target}")
        return 1

    edits = collect_edits(new_name)

    if args.dry_run:
        print(f"[dry-run] would rename 'example' -> '{new_name}'")
        print(f"[dry-run] would move src/example -> src/{new_name}")
        for path, _content in edits:
            print(f"  edit  {os.path.relpath(path, REPO_ROOT)}")
        return 0

    for path, content in edits:
        write_text(path, content)

    shutil.move(SRC_EXAMPLE, target)

    print(f"Renamed package 'example' -> '{new_name}'.")
    print("Next steps:")
    print("  1. git add -A && git commit -m 'chore: rename template to <name>'")
    print("  2. pip install -e .")
    print("  3. pytest")
    print("  4. Update authors/urls in pyproject.toml for your project.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
