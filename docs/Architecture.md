@page Architecture Architecture

# Mercurius Architecture

Mercurius is currently implemented as a Python package in
[`python/src/Mercurius`](../python/src/Mercurius). The package uses only the
Python standard library at runtime. The repository also contains its tests in
[`python/tests`](../python/tests), runnable examples in
[`examples/python`](../examples/python), and project documentation in this
directory. A C++ implementation is planned but not yet implemented; `cpp/` and
`bindings/` are empty placeholders.

## Modules

| Module | Responsibility |
|---|---|
| `event.py` and `events.py` | Generic `Event` and ready-made event subclasses |
| `event_type.py` | `EventType` and normalization/validation of one or more types |
| `subscriber.py` | `Subscriber` protocol and optional `BaseSubscriber` helper |
| `subscription.py` | Subscriber relationship, active state, counters, and unsubscribe |
| `event_queue.py` | FIFO queue, filtering, dispatch worker, and queue statistics |
| `event_bus.py` | Default and custom queue ownership; event fan-out |
| `runtime.py` | Process-wide bus registry, lifecycle helpers, and interpreter-exit cleanup |
| `__init__.py` | Public exports and default-bus helpers |

## Publish and dispatch

1. `EventBus.publish(event)` validates the event and offers the same event object
   to each queue owned by that bus.
2. Each queue applies its event-type allow-list and then its optional predicate
   on the publishing thread. Rejected events increment `filtered`; exceptions
   from predicates are logged and also reject the event.
3. An event accepted by a running queue is appended to that queue. A stopped
   queue drops it. The return value from `publish()` is the number of queues
   that accepted and enqueued the event.
4. Each queue's worker removes events in FIFO order and takes a snapshot of the
   subscriptions matching the event's exact type.
5. Delivery exceptions are logged and counted without preventing other
   subscribers or later events from being processed.

## Threads and synchronization

- Each queue has one daemon worker thread. Callbacks run on that worker, not on
  the publishing thread, and callbacks for a single queue do not overlap.
- Each queue lock protects its subscription registry and counters. Subscriber
  callbacks run without that lock, so callbacks can publish, subscribe, and
  unsubscribe.
- A subscription checks its active state as delivery begins. A delivery that
  has already captured its subscriber reference may still run if
  `unsubscribe()` completes before the callback starts.
- The bus lock protects the queue list and bus lifecycle operations.
- `stop(drain=True)` places a stop marker behind pending events. If a callback
  on that queue publishes during the drain, the worker processes those events
  before exiting. Other threads' publishes are dropped after stopping begins.
- `stop(drain=False)` clears pending events before stopping. Neither `stop()`
  nor `shutdown()` joins the worker when called from that worker's callback.
  Both report whether workers finished before the timeout.
- A queue cannot restart while its previous worker is still alive.

## Lifecycle and runtime

```text
construct --> running --stop()--> stopped --start()--> running
                 |                   |
                 +---- shutdown() ---+--> closed (terminal)
```

`EventBus` starts its default queue when constructed. Construction registers the
bus with the process-wide runtime. Calling `Mercurius.init()` explicitly at
startup is preferred; otherwise a bus initializes the runtime automatically
and emits a one-time warning. `get_default_bus()` initializes silently.

`stop()` halts workers and keeps subscriptions and queues, so `start()` can
resume the bus. `shutdown()` stops workers, releases subscriptions, removes the
queues from the bus, and unregisters the bus. The closed bus cannot be started
or used to create queues or subscriptions. `Mercurius.shutdown()` shuts down
all currently registered buses; the runtime also registers cleanup at
interpreter exit.

## Design

- Mercurius transports generic events; applications define event meaning and
  vocabulary.
- FIFO ordering is per queue only. Queues have independent workers and no
  cross-queue ordering guarantee.
- A subscription retains its subscriber until it is unsubscribed or its queue
  is shut down.
- The default queue receives every event unless a custom queue is used for
  separate consumers or filtering.
