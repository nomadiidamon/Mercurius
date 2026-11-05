# Mercurius

Queue-based, thread-safe publish/subscribe event library. Mercurius defines
**how events move**, not what they mean: applications provide event types and
payloads, and Mercurius provides queues, subscriptions, and delivery.

Mercurius was developed by abstracting useful and common logic from
[Domus-AI](https://github.com/nomadiidamon/Domus-AI).

## Status

Current version: 0.5.0. Project metadata (name, version, license, Python
requirement) lives in [project.ini](project.ini).

| Implementation | State |
|---|---|
| Python (`mercurius-events`, Python 3.10+) | Implemented; see [python/](python/) |
| C++ | Planned, not yet implemented; `cpp/` and `bindings/` are empty placeholders |

## Examples

Runnable Python examples are in [examples/python](examples/python). Run all of
them with `python/scripts/run_examples.bat` (Windows) or
`python/scripts/run_examples.sh`.

## Documentation

- [Concepts](docs/Concepts.md) introduces Mercurius's main pieces—events,
  buses, queues, subscribers, subscriptions, and their lifecycles.
- [Architecture](docs/Architecture.md) describes the current Python package's
  modules, publish and dispatch path, threading, and runtime cleanup.
- [Semantics](docs/Semantics.md) specifies observable behavior, including
  delivery ordering, filtering, failures, and stop/shutdown behavior.
- [Python API reference](docs/Mercurius.md) covers installation, a quick start,
  and the public classes, methods, and helpers.

For installation and a quick-start example, see the
[Python package README](python/README.md).
