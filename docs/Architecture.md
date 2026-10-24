# Mercurius Architecture

## Modules (`python/src/Mercurius`)

| Module | Responsibility |
|---|---|
| `event.py`, `events.py` | `Event` and the ready-made subclasses |
| `event_type.py` | `EventType` (`str`) and type-list normalization |
| `subscriber.py` | `Subscriber` protocol, optional `BaseSubscriber` |
| `subscription.py` | `Subscription`: state, counters, `unsubscribe()` |
| `event_queue.py` | `EventQueue`: FIFO storage, worker thread, filtering, stats |
| `event_bus.py` | `EventBus`: owns the queues, fans `publish()` out to them |
| `runtime.py` | Governor: `init()`/`shutdown()`, tracks live buses and their queues, exit hook |
| `__init__.py` | Public exports and the default-bus helpers |

## Publish path

1. `EventBus.publish(event)` loops over the bus's queues.
2. Each queue checks `accepts(event)` (type allow-list, then predicate) on the **publisher's thread**. Rejected events are counted as `filtered`.
3. Accepted events are put on the queue (`enqueued`), or counted as `dropped` if the queue is stopped.
4. The queue's worker takes events in FIFO order and delivers each to the subscriptions registered for `event.type`.
5. Each delivery is wrapped so an exception is logged, counted (`failed`) and does not stop the loop.

## Threading and locking

- One daemon worker thread per queue; callbacks never run on publishers.
- A per-queue `RLock` protects the subscription registry and counters. It is **not** held while subscriber callbacks run, so callbacks can publish, subscribe and unsubscribe.
- Dispatch takes a snapshot of the subscriptions for the event type; each `Subscription` re-checks its own `active` flag just before calling the subscriber, so an `unsubscribe()` takes effect for every event not yet delivered.
- The bus lock only guards the list of queues.
- `stop()` enqueues a sentinel behind pending events (drain) or clears the queue first (no drain). It never joins the calling thread, so it is safe inside a callback, and it returns whether the worker finished.
- While draining, the worker re-queues the sentinel whenever events were published behind it (reentrant publishes from its own callbacks), so they are processed before it exits.
- `start()` refuses to run while the previous worker thread is alive, so a queue never has two workers.
- The dispatch loop catches unexpected errors per event, and `publish()` validates its input, so a bad call cannot kill a worker.

## Lifecycle

```text
construct --> running --stop()--> stopped --start()--> running
                 |                   |
                 +---- shutdown() ---+--> closed (terminal)
```

`shutdown()` releases the subscriptions, drops the queues and makes the runtime stop tracking the bus. `start()`, `create_queue()` and `subscribe()` then raise `RuntimeError`.

The runtime (`runtime.py`) keeps a registry of live buses. `EventBus.__init__` registers the bus (initializing the runtime, with a one-time warning, if `init()` was not called) and `EventBus.shutdown()` unregisters it. `Mercurius.shutdown()` and the `atexit` hook shut down everything still registered.

## Design decisions

- Mercurius is generic: event meaning lives in the application.
- FIFO is guaranteed per queue; queues are independent and may later run concurrently.
- Subscribers are objects; the bus only holds a reference while subscribed.
- Python and C++ are independent implementations of the same concepts.
