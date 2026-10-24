"""Uninstall the editable package, preview Python artifacts, then remove them on confirmation."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_NAME = "mercurius"

# Directory names removed wherever they appear.
DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov", ".hypothesis"}
DIR_SUFFIXES = (".egg-info",)
# Only removed directly under python/ so unrelated build/ dirs (e.g. C++) are untouched.
PYTHON_ROOT_DIRS = {"build", "dist", ".eggs"}
FILE_SUFFIXES = (".pyc", ".pyo")
FILE_NAMES = {".coverage"}
PYTHON_ROOT_FILES = {"test_output.txt"}

# Never descend into these.
SKIP_DIRS = {".git", ".venv", "venv", "node_modules"}


def find_artifacts(root: Path):
    python_dir = root / "python"
    found = []

    def walk(directory: Path):
        for entry in directory.iterdir():
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in SKIP_DIRS:
                    continue
                if (
                    entry.name in DIR_NAMES
                    or entry.name.endswith(DIR_SUFFIXES)
                    or (entry.parent == python_dir and entry.name in PYTHON_ROOT_DIRS)
                ):
                    found.append(entry)
                else:
                    walk(entry)
            elif (
                entry.name.endswith(FILE_SUFFIXES)
                or entry.name in FILE_NAMES
                or (entry.parent == python_dir and entry.name in PYTHON_ROOT_FILES)
            ):
                found.append(entry)

    walk(root)
    return found


def uninstall_package() -> None:
    print(f"Uninstalling editable package {PACKAGE_NAME!r}...")
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", PACKAGE_NAME])


def confirm(prompt: str) -> bool:
    try:
        return input(prompt).strip().lower() in ("y", "yes")
    except EOFError:  # non-interactive: never delete without an answer
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="only list what would be removed; no uninstall, no prompt")
    parser.add_argument("-y", "--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    if not args.dry_run:
        uninstall_package()

    artifacts = find_artifacts(REPO_ROOT)
    print("\nDry run:")
    for path in artifacts:
        print(f"  would remove {path.relative_to(REPO_ROOT)}")
    print(f"{len(artifacts)} artifact(s) found.")

    if args.dry_run or not artifacts:
        return 0
    if not args.yes and not confirm("\nRemove them? [y/N] "):
        print("Nothing removed.")
        return 0

    for path in artifacts:
        rel = path.relative_to(REPO_ROOT)
        try:
            shutil.rmtree(path) if path.is_dir() else path.unlink()
            print(f"removed {rel}")
        except OSError as exc:
            print(f"failed to remove {rel}: {exc}", file=sys.stderr)
            return 1

    print(f"{len(artifacts)} artifact(s) removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
