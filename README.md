# Mercurius

Queue-based, thread-safe publish/subscribe event library. Mercurius defines
**how events move**, not what they mean: applications provide event types and
payloads, and Mercurius provides queues, subscriptions, and delivery.

Mercurius was developed by abstracting useful and common logic from
[Domus-AI](https://github.com/nomadiidamon/Domus-AI).

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
