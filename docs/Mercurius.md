# Mercurius Python API

This reference covers the current Python package. For the project model, start
with [Concepts](Concepts.md); [Semantics](Semantics.md) specifies behavioral
guarantees and [Architecture](Architecture.md) describes the implementation.

## Installation

Python 3.10 or newer is required. From the repository root:

```bash
python -m pip install -e "./python"
```

For development, install the `dev` extra from the package directory:

```bash
cd python
python -m pip install -e ".[dev]"
python -m pytest
```

## Quick start

```python
import Mercurius
from Mercurius import Event, EventBus

Mercurius.init()
with EventBus() as bus:
    subscription = bus.subscribe(
        "GREETING", lambda event: print(event.payload["text"])
    )
    bus.publish(Event("GREETING", {"text": "hello"}))
    subscription.unsubscribe()
Mercurius.shutdown()
```

Explicit `init()` is preferred. Constructing a bus without it initializes the
runtime automatically and emits a one-time `RuntimeWarning`.

## Event and event types

`Event(type, payload, source, timestamp)` is a dataclass. The type must be a
string when published. The payload defaults to a new dictionary for each event;
source defaults to an empty string; timestamp defaults to the current local
time in ISO format. `Event.to_dict()` returns the event fields as a dictionary.

`EventType` is an alias for `str`. Subscription and queue APIs accept one event
type or an iterable of strings. Empty collections and non-string members are
rejected. Duplicate types are removed while retaining their first occurrence.

Ready-made subclasses are also exported: `ApplicationEvent`, `MessageEvent`,
`FileEvent`, and `ErrorEvent`. They provide default type values and constants,
but applications may define their own types and event classes.

## Subscribers and subscriptions

A subscriber may be an object with `on_event(event)` or a callable. The
`Subscriber` protocol describes the object form.

`BaseSubscriber` is an optional abstract base class with:

- `subscribe_to(bus, event_types, queue=None) -> Subscription`
- `subscriptions`, the active subscriptions it tracks
- `unsubscribe_from(event_types)`, which accepts a type, list of types, or an
  `Event`; it stops delivery for the selected type or types while preserving
  any remaining event types on a subscription
- `unsubscribe_all()`

`EventBus.subscribe(event_types, subscriber, queue=None)` subscribes on the
default queue unless a queue belonging to that bus is specified. It returns a
`Subscription`. A queue with an allow-list rejects subscriptions to excluded
types with `ValueError`; a queue belonging to another bus is also rejected.

A `Subscription` exposes `id`, `active`, `event_types`, `queue`, and
`subscriber_name`. `unsubscribe()` is idempotent, marks it inactive, and
releases its subscriber reference. Debugging fields include `delivered_count`,
`error_count`, `last_error`, and `to_dict()`.

## EventBus

`EventBus(name=None)` starts its default queue when constructed and is tracked
by the process-wide runtime. It can be used as a context manager; leaving the
`with` block calls `shutdown()`.

| Member | Description |
|---|---|
| `subscribe(event_types, subscriber, queue=None)` | Subscribe to one or more types; returns a `Subscription`. |
| `publish(event) -> int` | Non-blocking fan-out. Returns the number of queues that enqueued the event. Raises `TypeError` for an invalid event. |
| `create_queue(name=None, event_types=None, event_filter=None)` | Create an independent queue, optionally filtered by an allow-list and/or predicate. |
| `default_queue`, `queues`, `name`, `is_running`, `is_closed` | Read-only bus state. |
| `stop(drain=True, timeout=5.0) -> bool` | Stop workers but keep queues and subscriptions; reports whether workers finished. |
| `start()` | Restart a stopped bus. Raises `RuntimeError` if closed or a previous worker is still running. |
| `shutdown(drain=True, timeout=5.0) -> bool` | Stop workers, release subscriptions, and close the bus permanently. |
| `stats()` | Return bus state and a stats dictionary for each queue. |

`stop()` can be followed by `start()`. `shutdown()` is terminal; subsequent
calls to `start()`, `create_queue()`, or `subscribe()` raise `RuntimeError`.
Both methods return whether all queue workers finished before the timeout and
are safe to call from a callback.

## Process-wide helpers

- `Mercurius.init()` activates the runtime and registers interpreter-exit
  cleanup; it is idempotent.
- `Mercurius.shutdown(drain=True, timeout=5.0)` shuts down every registered
  bus and clears the runtime registry.
- `Mercurius.is_initialized()` reports runtime state.
- `Mercurius.runtime.buses()` returns the currently registered buses, and
  `Mercurius.runtime.stats()` returns runtime and bus statistics.
- `get_default_bus()` creates a shared bus on demand, restarts it if stopped,
  or replaces it if shut down.
- `shutdown_default_bus(drain=True)` shuts down and releases the shared bus.

## EventQueue

Queues are created by an `EventBus`. `create_queue()` accepts:

- `event_types`: optional allow-list of accepted types.
- `event_filter`: optional `callable(event) -> bool`, applied after the
  allow-list. If it raises, the error is logged and the event is rejected.

The queue exposes `name`, `accepted_event_types`, `subscriptions`, `is_running`,
`accepts(event)`, `start()`, `stop()`, `shutdown()`, and `stats()`. A queue's
`enqueue(event)` validates that the event is an `Event` with a string type.
Queue `start()` raises `RuntimeError` if its previous worker is still running.

Queue stats include `name`, `running`, `pending`, `accepted_types`,
`has_filter`, `subscriptions`, `enqueued`, `filtered`, `dropped`, `dispatched`,
`unmatched`, `delivered`, and `failed`.

For ordering, filtering, errors, and shutdown edge cases, see
[Semantics](Semantics.md). Runnable examples are in
[`examples/python`](../examples/python).
