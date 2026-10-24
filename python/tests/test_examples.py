import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES = sorted((ROOT / "examples" / "python").glob("*.py"))


def test_examples_exist():
    assert EXAMPLES


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.name)
def test_example_runs_cleanly(example):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "python" / "src")}
    result = subprocess.run(
        [sys.executable, str(example)],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    # Examples show the preferred explicit Mercurius.init().
    assert "RuntimeWarning" not in result.stderr, result.stderr
