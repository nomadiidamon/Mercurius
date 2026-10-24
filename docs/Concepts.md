# Mercurius Concepts

**Mercurius defines how events move, not what they mean.** Applications own the meaning.

## Event
Something that happened: a `type`, a `payload`, and metadata (`source`, `timestamp`). Event types are plain strings so any application can define its own vocabulary.

## Runtime
Call `Mercurius.init()` once at start-up and `Mercurius.shutdown()` at exit. The runtime tracks every live bus and its queues; shutting it down shuts down all of them. A bus created without `init()` auto-initializes the runtime and warns once.

## EventBus
The object you use. You publish events to it and subscribe to it. Create as many independent buses as you like; `get_default_bus()` offers one shared process-wide bus when you want that.

## Queue
A queue is a FIFO delivery path with its own worker thread. Every bus has a **default queue**; you can add **custom queues** so independent consumers get independent delivery (a slow consumer does not delay a fast one).

A queue does not have to receive every event. It can be given an allow-list of event types and/or a predicate; events it does not accept are ignored before they are stored.

## Subscriber
An object with `on_event(event)`; a plain function works too. It receives only the event types it subscribed to. `BaseSubscriber` is an optional helper that tracks the subscriptions an object creates.

## Subscription
The relationship `event types + subscriber + queue`, returned by `subscribe()`. Call `unsubscribe()` to end it. It carries counters for debugging.

## Guarantees

- **FIFO per queue.** Events published to one queue are delivered in publish order. Across queues there is no ordering.
- **Non-blocking publish.** Subscriber code never runs on the publisher's thread.
- **Failure isolation.** A subscriber exception is logged and does not stop other subscribers or the queue.
- **Thread safety.** Publishing, subscribing and unsubscribing may happen from any thread. Subscribers on one queue run one at a time.

## Lifetime

- The bus does not own your subscriber. A subscription holds a reference only until it is released.
- `unsubscribe()` releases one subscription; it is safe to repeat.
- `stop()` halts workers but keeps subscriptions; `start()` resumes. `shutdown()` halts workers, releases all subscriptions and closes the bus for good (its queues are dropped, and it can no longer create queues or accept subscriptions).
- With `stop(drain=True)`, events published by a queue's own callbacks are still delivered until the queue is empty; other threads' publishes are dropped.

## Not included (yet)
Persistence, replay, cross-process delivery, priorities, retries, bounded queues and worker pools are out of scope for v0.1.
