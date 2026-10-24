# Mercurius

Queue-based, thread-safe pub/sub event library. Mercurius defines **how events move**, not what they mean: you bring the event types, it brings FIFO delivery, queues and subscriptions.

> Status: v0.1.0. The Python implementation is available. A C++ implementation is planned.

## Features

- Generic `Event` (string type, dict payload); no application-specific vocabulary.
- Non-blocking `publish()`; subscriber code runs on worker threads.
- FIFO per queue, with a default queue and optional independent queues.
- Queues can ignore events they do not need (type allow-list and/or predicate).
- Subscribers are plain objects (or functions); subscribe to one type or a list of types.
- First-class `Subscription` objects with safe `unsubscribe()` and debug counters.
- Failure isolation: a raising subscriber never stops delivery.
- `stop()` pauses workers and keeps subscriptions; `shutdown()` closes the bus for good and releases them.
- A process-wide runtime (`Mercurius.init()` / `Mercurius.shutdown()`) tracks every bus and its queues and cleans them up.
- No dependencies beyond the standard library.

## Install (Python)

```bash
cd python
pip install -e .[dev]
```

Requires Python 3.10+.

## Quick start

```python
import Mercurius
from Mercurius import Event, EventBus

class Printer:
    def on_event(self, event):
        print(event.type, event.payload)

Mercurius.init()                 # preferred: explicit start-up
with EventBus() as bus:          # shutdown() runs on exit
    sub = bus.subscribe("GREETING", Printer())
    bus.publish(Event("GREETING", {"text": "hello"}))
    sub.unsubscribe()
Mercurius.shutdown()             # shuts down any bus still running
```

Creating an `EventBus` without `Mercurius.init()` works too: the runtime initializes itself and warns once.

Custom, filtered queue:

```python
audit = bus.create_queue("audit", event_types=["REFUND"])
bus.subscribe("REFUND", handler, queue=audit)   # only REFUND events reach this queue
```

## Guarantees

- Events on one queue are delivered in publish order; there is no ordering across queues.
- Callbacks never run on the publisher's thread, and callbacks of one queue never overlap.
- Subscribers may publish and unsubscribe from inside a callback.

## Repository layout

| Path | Contents |
|---|---|
| `python/` | Python package (`src/Mercurius`), tests, scripts |
| `examples/python/` | Runnable, commented examples |
| `docs/` | [API](docs/MercuriusAPI.md), [Concepts](docs/Concepts.md), [Architecture](docs/Architecture.md) |
| `cpp/`, `bindings/` | Planned C++ implementation and optional bindings |

## Tests

```bash
python/scripts/run_tests.sh      # Linux / macOS
python\scripts\run_tests.bat     # Windows
```

Both call `python/tools/run_tests.py`, which runs pytest and writes the output to `python/test_output.txt`. Extra arguments are passed to pytest. Or simply run `pytest` inside `python/`.

`python/scripts/clean.sh` / `clean.bat` call `python/tools/clean.py`: it uninstalls the editable package, lists the Python artifacts it would delete, and removes them after you confirm (`--dry-run` only lists; `--yes` skips the prompt). All wrappers pause for a key press at the end.

## Examples

Run from the repository root after installing the package.

| Example | Shows |
|---|---|
| `basic.py` | subscribe, publish, unsubscribe |
| `custom_queue.py` | independent queues |
| `filtering.py` | queues that ignore events; type lists |
| `base_subscriber.py` | `BaseSubscriber` and the event classes |
| `app_events.py` | an application-defined event vocabulary |
| `lifetime.py` | subscriber lifetime and release |
| `shutdown.py` | `stop()` versus `shutdown()` |
| `multiple_buses.py` | isolated buses and the default bus |
| `timing.py` | threads, non-blocking publish, slow consumers |
| `failures.py` | exception isolation, bad input, counters |
| `reentrancy.py` | publishing and unsubscribing inside callbacks |
| `concurrency.py` | many publisher threads |
| `debugging.py` | `stats()`, `repr()`, `to_dict()` |

## Documentation

- [API reference](docs/MercuriusAPI.md)
- [Concepts](docs/Concepts.md)
- [Architecture](docs/Architecture.md)
- [Migration plan](migration.md)
