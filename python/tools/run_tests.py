"""Run the Mercurius Python test suite; extra arguments are passed to pytest."""
import subprocess
import sys
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PYTHON_DIR / "test_output.txt"


def main() -> int:
    cmd = [sys.executable, "-m", "pytest", *sys.argv[1:]]
    # Mode "w" overwrites the previous run's output.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        proc = subprocess.Popen(
            cmd,
            cwd=PYTHON_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            sys.stdout.write(line)
            out.write(line)
        return proc.wait()


if __name__ == "__main__":
    sys.exit(main())
