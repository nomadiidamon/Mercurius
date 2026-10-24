import sys

import pytest

import clean
import run_tests


@pytest.fixture
def tree(tmp_path):
    """A fake repo containing artifacts that should and should not be cleaned."""
    def touch(rel):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")

    # to be removed
    touch("python/src/pkg/__pycache__/mod.cpython-311.pyc")
    touch("python/.pytest_cache/v/cache")
    touch("python/build/lib/x.py")
    touch("python/dist/pkg.whl")
    touch("python/pkg.egg-info/PKG-INFO")
    touch("python/test_output.txt")
    touch("python/tests/stray.pyc")
    touch("examples/python/__pycache__/e.pyc")
    # to be kept
    touch("python/src/pkg/mod.py")
    touch("cpp/build/keep.o")           # build/ is only an artifact directly under python/
    touch(".venv/lib/__pycache__/x.pyc")
    touch(".git/objects/x.pyc")
    touch("test_output.txt")            # only python/test_output.txt is an artifact
    return tmp_path


def rel(root, paths):
    return {p.relative_to(root).as_posix() for p in paths}


def test_find_artifacts(tree):
    found = rel(tree, clean.find_artifacts(tree))
    assert found == {
        "python/src/pkg/__pycache__",
        "python/.pytest_cache",
        "python/build",
        "python/dist",
        "python/pkg.egg-info",
        "python/test_output.txt",
        "python/tests/stray.pyc",
        "examples/python/__pycache__",
    }


def run_main(monkeypatch, tree, args, answer=None):
    monkeypatch.setattr(clean, "REPO_ROOT", tree)
    uninstalled = []
    monkeypatch.setattr(clean, "uninstall_package", lambda: uninstalled.append(True))
    if answer is not None:
        monkeypatch.setattr(clean, "confirm", lambda prompt: answer)
    monkeypatch.setattr(sys, "argv", ["clean.py", *args])
    return clean.main(), uninstalled


def test_dry_run_neither_uninstalls_nor_deletes(monkeypatch, tree):
    before = rel(tree, clean.find_artifacts(tree))
    code, uninstalled = run_main(monkeypatch, tree, ["--dry-run"])
    assert code == 0 and uninstalled == []
    assert rel(tree, clean.find_artifacts(tree)) == before


def test_declined_confirmation_deletes_nothing_but_uninstalls_first(monkeypatch, tree):
    before = rel(tree, clean.find_artifacts(tree))
    code, uninstalled = run_main(monkeypatch, tree, [], answer=False)
    assert code == 0 and uninstalled == [True]
    assert rel(tree, clean.find_artifacts(tree)) == before


def test_confirmed_clean_removes_artifacts_only(monkeypatch, tree):
    code, _ = run_main(monkeypatch, tree, [], answer=True)
    assert code == 0
    assert clean.find_artifacts(tree) == []
    assert (tree / "python/src/pkg/mod.py").exists()
    assert (tree / "cpp/build/keep.o").exists()
    assert (tree / ".venv/lib/__pycache__/x.pyc").exists()


def test_yes_flag_skips_prompt(monkeypatch, tree):
    monkeypatch.setattr(clean, "confirm", lambda prompt: pytest.fail("prompted"))
    code, _ = run_main(monkeypatch, tree, ["--yes"])
    assert code == 0 and clean.find_artifacts(tree) == []


def test_confirm_treats_missing_input_as_no(monkeypatch):
    def eof(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert clean.confirm("?") is False


def test_nothing_to_clean(monkeypatch, tmp_path):
    code, _ = run_main(monkeypatch, tmp_path, [], answer=True)
    assert code == 0


def test_run_tests_paths():
    assert run_tests.PYTHON_DIR.name == "python"
    assert (run_tests.PYTHON_DIR / "pyproject.toml").exists()
    assert run_tests.OUTPUT_FILE.parent == run_tests.PYTHON_DIR
