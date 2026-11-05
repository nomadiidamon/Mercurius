"""Run every Python example in examples/python; exit non-zero if any fails."""
import os
import subprocess
import sys
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PYTHON_DIR.parent / "examples" / "python"


def main() -> int:
    examples = sorted(EXAMPLES_DIR.glob("*.py"))
    if not examples:
        print(f"No examples found in {EXAMPLES_DIR}")
        return 1

    # Run against the in-repo sources so no install is required.
    env = {**os.environ, "PYTHONPATH": str(PYTHON_DIR / "src")}
    failed = []
    for index, example in enumerate(examples, start=1):
        print("=" * 70)
        print(f"[{index}/{len(examples)}] {example.name}")
        print("=" * 70, flush=True)
        result = subprocess.run([sys.executable, str(example)], env=env)
        if result.returncode != 0:
            failed.append(example.name)
            print(f"--- FAILED: {example.name} (exit code {result.returncode})", flush=True)
        print()

    print("=" * 70)
    print(f"Ran {len(examples)} examples, {len(failed)} failed")
    for name in failed:
        print(f"  FAILED: {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
