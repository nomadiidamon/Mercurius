# Contributing Guidelines

## Introduction

Thank you for your interest in contributing! This document outlines the guidelines and best practices for contributing to this project, which currently provides a Python implementation. A C++ implementation is planned but not yet implemented.

### Code of Conduct

All contributors are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Repository Model

This repository separates **implementation** from **shared semantics and concepts**:

- **Concepts and semantics** live in [`docs/Concepts.md`](docs/Concepts.md) and [`docs/Semantics.md`](docs/Semantics.md). These documents describe the project and the behavior of its current Python implementation.
- **Implementation** lives in [`python/`](python/), packaged with [`python/pyproject.toml`](python/pyproject.toml); source is under `python/src/` and tests under `python/tests/`.
- **Examples** live in [`examples/python/`](examples/python/).

See [`docs/Architecture.md`](docs/Architecture.md) for the full layout.

### Ground Rules

- A change to behavior should update [`docs/Semantics.md`](docs/Semantics.md) (or [`docs/Concepts.md`](docs/Concepts.md)) and at least one of the language implementations. An issue should be created for the language where the chagne was not propgated.
- Keep docs and examples consistent with current langauage implementations.

## Getting Started

1. **Fork the Repository** using the "Fork" button on the repository page.
2. **Clone Your Fork**:
```bash
git clone --recursive https://github.com/nomadiidamon/Mercurius <desiredLocation>
```
3. **Set Up the Development Environment** for the language(s) you are working on (see below).
4. **Create a Branch** with a descriptive name for your feature or fix.
5. **Make Changes** following the coding standards and naming conventions below.
6. **Test Your Changes**: run existing tests and add new ones where needed.
7. **Commit** with clear, concise messages in small, focused commits.
8. **Push** to your fork.
9. **Open a Pull Request** describing the problem, the solution, and which implementations are affected.
10. **Address Feedback**: maintainers may request changes. Be open to feedback and responsive.
11. **Merge**: once approved, a maintainer will merge your changes.

## Development Setup

### C++

Planned, not yet implemented. The `cpp/` and `bindings/` directories are empty placeholders.

### Python

Python 3.10 or newer is required. From the repository root, create a virtual environment in `python/`, then activate it:

```bash
cd python
python -m venv .venv
```

Activate the environment using the command for your shell:

```text
Windows PowerShell: .\.venv\Scripts\Activate.ps1
Windows Command Prompt: .venv\Scripts\activate.bat
macOS/Linux: source .venv/bin/activate
```

With the environment active and the working directory still set to `python/`, install the package and its development dependency, then run the test suite:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Run all examples with `python/scripts/run_examples.bat` or `python/scripts/run_examples.sh`. Every example must start with an `@example <file>.py` Doxygen marker in its docstring.

The version is kept in [`project.ini`](project.ini), the [`Doxyfile`](Doxyfile) (`PROJECT_NUMBER`), and `python/src/Mercurius/__init__.py`; the `03-match-version` pre-commit hook and the build workflow require all three to match.

The `dev` extra currently installs pytest. These commands use the package's configured test discovery and do not install linters or formatters.

## Naming Conventions

### C++

- Snake_Case/snake_case/snake_Case is fine for private member or local variables.
- camelCase is fine for public member or local variables, although `Name` is preferred to something like `myName`.
- Functions should always be PascalCase - `DoThing()` - unless it is a variant - `DoThing_Internal()` - in which case Snake_Case is fine.

Examples:
- Class member variables (private): `m_name`, `m_array`, etc.
- Class member variables (public): `Name`, `myName`, `Length`, `applicationConfig`, etc.
- Class functions (private): `DoThing()`, `DoThing_Internal()`, etc.
- Class functions (public): `DoThing()`, `DoThingAgain()`, etc.
- Class static variables (private): `s_name`, `s_array`, etc.
- Class static variables (public): `sName`, `sArray`, etc.
- Boolean values: `bHasAccess`, `b_Access`, etc.

### Python

Follow [PEP 8](https://peps.python.org/pep-0008/):

- Modules and packages: `lower_snake_case` (short, no hyphens).
- Classes and exceptions: `PascalCase` (`CapWords`).
- Functions, methods, variables, and arguments: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Non-public members and helpers: single leading underscore (`_internal_value`, `_do_thing()`).
- Name-mangled attributes: double leading underscore only when truly needed.
- Booleans: read as predicates (`is_valid`, `has_access`).
- Add type hints to public APIs and docstrings to public modules, classes, and functions.

### Cross-Language Parity

Equivalent public concepts should be recognizably the same across implementations (e.g. C++ `DoThing()` corresponds to Python `do_thing()`). Each language uses its own conventions rather than copying the other's.

## Coding Standards

- Follow the existing style of the language tree you are editing.
- Use clear, descriptive names.
- Comment only where the code cannot explain itself, such as complex logic or non-obvious constraints.
- Keep code modular and reusable; avoid duplication.
- Write unit tests for new features and bug fixes.
- Ensure behavior matches [`docs/Semantics.md`](docs/Semantics.md).
- Update docs and examples when public behavior changes.
