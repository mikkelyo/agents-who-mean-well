"""Rename this template: ``uv run python scripts/rename_project.py my_app``."""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NEXT_STEPS = """
Next:
  git diff HEAD                          # review it; `git reset --hard` undoes it all
  git remote set-url origin <your-repo>  # origin still points at the template
  uv run pytest

Prose that merely mentions the template was rewritten too, so read any .md
above before committing. The example scaffolding is still wired in; to drop it
delete {name}/infrastructure/clients/example_client.py and
{name}/infrastructure/configurations/example_api_config.py, then their uses in
app.py, config.py, settings.json, {name}/di_container.py,
tests/unit/test_config.py and tests/unit/test_di_container.py.
"""


class RenameError(Exception):
    """A failure worth reporting as a message rather than a traceback."""


def run(*args: str) -> str:
    """Run a command in ROOT and return its stdout."""
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenameError(f"`{' '.join(args)}` failed:\n{result.stderr.strip()}")
    return result.stdout


def current_name() -> str:
    """Read the package name from pyproject.toml, so this can be run again later."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(pyproject["project"]["name"]).replace("-", "_")


def check(new: str, old: str) -> None:
    """Reject a bad name, or a tree too dirty for `git reset --hard` to undo."""
    if run("git", "status", "--porcelain").strip():
        raise RenameError("commit or stash your changes first, so this can be undone.")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", new):
        raise RenameError(f"'{new}' is not a valid Python package name.")
    if new in sys.stdlib_module_names:
        raise RenameError(f"'{new}' shadows a standard library module.")
    if (ROOT / new).exists() or (ROOT / f"{new}.py").exists():
        raise RenameError(f"'{new}' already exists at the repository root.")
    if not (ROOT / old).is_dir():
        raise RenameError(f"the package directory {old}/ is missing.")


def rewrite(old: str, new: str) -> list[str]:
    """Replace the old name in every tracked text file; return the files changed."""
    old_kebab, new_kebab = old.replace("_", "-"), new.replace("_", "-")
    # The boundaries keep `my_template_project_helper`, and prose like it, intact.
    pattern = re.compile(
        rf"(?<![\w-])(?:{re.escape(old)}|{re.escape(old_kebab)})(?![\w-])"
    )
    changed = []
    for name in run("git", "ls-files", "-z").split("\0"):
        if not name:
            continue
        path = ROOT / name
        data = path.read_bytes()
        if b"\0" in data:  # git's own heuristic: a NUL byte means binary.
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        renamed = pattern.sub(lambda match: new if match[0] == old else new_kebab, text)
        if renamed != text:
            # newline="" keeps each file's own line endings instead of rewriting them.
            path.write_text(renamed, encoding="utf-8", newline="")
            changed.append(name)
    return changed


def main() -> int:
    """Move the package directory, rewrite the old name everywhere, then relock."""
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    new = sys.argv[1]

    try:
        old = current_name()
        check(new, old)
        # Moving first means a failed `git mv` leaves the tree completely untouched.
        run("git", "mv", old, new)
        changed = rewrite(old, new)
        run("uv", "lock")
    except RenameError as error:
        print(f"error: {error}", file=sys.stderr)
        print("undo anything already done with `git reset --hard`.", file=sys.stderr)
        return 1

    print(f"moved {old}/ -> {new}/ and rewrote {len(changed)} file(s):")
    for name in changed:
        print(f"  {name}")
    print(NEXT_STEPS.format(name=new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
