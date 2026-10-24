# Mercurius Python API

Mercurius is a generic, thread-safe, queue-based pub/sub library. It does not know what events mean; applications define their own event types. See [Concepts.md](Concepts.md) for the ideas and [Architecture.md](Architecture.md) for how it is built.

```python
import Mercurius
from Mercurius import Event, EventBus

Mercurius.init()       # once, at start-up
# ... use buses ...
Mercurius.shutdown()   # once, at exit
```

## Runtime: init() and shutdown()

The Mercurius runtime tracks every live `EventBus` (and through it, its queues).

- `Mercurius.init()`: activates the runtime; idempotent. **Preferred.**
- `Mercurius.shutdown(drain=True, timeout=5.0)`: shuts down every tracked bus (releasing all subscriptions and dropping their queues) and clears the registry. Idempotent; also registered to run at interpreter exit.
- `Mercurius.is_initialized()`, `Mercurius.runtime.buses()`, `Mercurius.runtime.stats()`: inspection.

If an `EventBus()` is created without `init()`, the runtime initializes itself and emits a one-time `RuntimeWarning`. `get_default_bus()` initializes silently. Creating a bus after `Mercurius.shutdown()` initializes again.

## Event

`Event(type, payload={}, source="", timestamp=now)`

- `type`: a `str` identifying the kind of event (`EventType = str`; a `str`-based `Enum` also works).
- `payload`: a dict of data; `source`: free-form origin; `timestamp`: ISO-8601 string.
- `to_dict()` returns a serializable dict.

Ready-made subclasses with a default `type` and type constants: `ApplicationEvent` (`STARTUP`, `SHUTDOWN`, `STATE_CHANGED`), `MessageEvent` (`SENT`, `RECEIVED`), `FileEvent` (`CREATED`, `MODIFIED`, `DELETED`), `ErrorEvent` (`ERROR`, `WARNING`).

## Subscriber

Any object with `on_event(event)`. A plain callable is also accepted. `Subscriber` is the `Protocol`.

`BaseSubscriber` is an optional abstract base class that adds:

- `subscribe_to(bus, event_types, queue=None) -> Subscription`
- `subscriptions`: its active subscriptions
- `unsubscribe_from(event_types)`: stop receiving a type, a list of types, or an `Event`'s type; a subscription covering other types is replaced so they keep arriving
- `unsubscribe_all()`

## EventBus

`EventBus(name=None)` starts running as soon as it is constructed.

| Member | Description |
|---|---|
| `subscribe(event_types, subscriber, queue=None) -> Subscription` | `event_types` is one type or a list of types. Uses the default queue unless `queue` is given. A queue refuses (`ValueError`) types it filters out. |
| `publish(event) -> int` | Non-blocking. Offers the event to every queue; returns how many accepted it. `TypeError` unless `event` is an `Event` with a `str` type. |
| `create_queue(name=None, event_types=None, event_filter=None) -> EventQueue` | Independent FIFO queue; optionally filtered (below). `RuntimeError` once the bus is shut down. |
| `default_queue`, `queues`, `name`, `is_running`, `is_closed` | Inspection. |
| `stop(drain=True, timeout=5.0) -> bool` | Stop the workers. **Subscriptions are kept.** `True` if every worker finished, `False` if one is still running (join timed out, or called from a callback). |
| `start()` | Restart stopped workers. `RuntimeError` if the bus is shut down, or if a previous worker is still running. |
| `shutdown(drain=True, timeout=5.0) -> bool` | `stop()`, then **release every subscription and close the bus** (terminal). |
| `stats()` | Dict with a stats dict per queue. |

`with EventBus() as bus:` calls `shutdown()` on exit.

### stop() versus shutdown()

| | workers | subscriptions | queues | can resume |
|---|---|---|---|---|
| `stop()` | stopped | **kept** (still `active`) | kept | yes, `start()` |
| `shutdown()` | stopped | **released** (inactive, subscribers dereferenced) | **dropped** | no: the bus is closed; `start()`, `create_queue()`, `subscribe()` raise `RuntimeError` |

Both deliver already-queued events first when `drain=True`, and discard them when `drain=False`. Both are idempotent and safe to call from a subscriber callback. While stopped, `publish()` drops events (counted in `stats()["dropped"]`).

### Shutdown contract

1. **Destructor:** there is none. Buses are tracked by the runtime, so `Mercurius.shutdown()` (or the exit hook) stops every worker; a bus you forget is cleaned up there.
2. **Queued events:** `drain=True` (default) delivers them; `drain=False` discards them.
3. **Running callbacks** are never interrupted; `stop()`/`shutdown()` wait up to `timeout` and report `False` if a callback is still running.
4. **Publishing during shutdown:** publishes from other threads are dropped once `stop()` has been called.
5. **Reentrant publishes during a drain:** with `drain=True`, events published by a queue's own callbacks are still accepted and delivered, until the queue is empty. A callback that keeps publishing therefore keeps the drain going. With `drain=False` they are dropped.
6. **Unsubscribing from inside a callback** is supported.
7. **Restart:** only after `stop()`. A shut-down bus is closed for good; `start()` also refuses while the previous worker is still alive, so a queue never has two workers.

Process-wide convenience: `get_default_bus()` (created on demand; a stopped bus is restarted, a shut-down one replaced) and `shutdown_default_bus(drain=True)`. Prefer your own `EventBus()` for isolation and tests.

## EventQueue

Created by the bus. Delivers to its subscriptions in FIFO order on one worker thread.

**Queues do not have to receive every event.** Two optional filters decide what a queue accepts; everything else is ignored at publish time and only counted:

- `event_types`: allow-list of types.
- `event_filter`: `callable(event) -> bool`, applied after `event_types`. If it raises, the exception is logged and the event is ignored.

Members: `name`, `accepts(event)`, `accepted_event_types`, `subscriptions`, `is_running`, `start()`, `stop()`, `shutdown()`, `stats()`. `enqueue(event)` raises `TypeError` for anything but an `Event` with a `str` type; `stop()` returns whether the worker finished; `start()` raises `RuntimeError` while the previous worker is alive.

`stats()` keys: `name`, `running`, `pending`, `accepted_types`, `has_filter`, `subscriptions`, and counters `enqueued`, `filtered`, `dropped`, `dispatched`, `unmatched` (dispatched with no subscriber), `delivered`, `failed`.

## Subscription

Returned by `subscribe()`.

- `unsubscribe()`: idempotent; stops delivery and releases the subscriber.
- `active`, `id`, `event_types`, `queue`, `subscriber_name`.
- Debugging: `delivered_count`, `error_count`, `last_error`, `to_dict()`, and a readable `repr()`.

A subscriber only receives events whose type is in its `event_types`.

## Semantics

- **FIFO per queue only.** No ordering is promised across queues.
- Callbacks run on the queue's worker thread, never the publisher's, and are serialized per queue.
- A callback exception is logged (`logging`, logger `Mercurius.*`); other subscribers and the worker continue. The worker also survives unexpected internal errors.
- Callbacks may `publish()` (appended to the queue, processed after the callback returns) or `unsubscribe()`.
- After `unsubscribe()`, no further events are delivered through that subscription.
- The bus holds a strong reference to a subscriber only while it is subscribed.
- All queues of a bus receive the same `Event` object, so treat events as read-only.

## Example

```python
import Mercurius
from Mercurius import Event, EventBus

class MySubscriber:
    def on_event(self, event):
        print(event.payload)

Mercurius.init()
with EventBus() as bus:
    sub = bus.subscribe("TEST_EVENT", MySubscriber())
    bus.publish(Event("TEST_EVENT", {"value": 42}))
    sub.unsubscribe()
```

More in [examples/python](../examples/python).
