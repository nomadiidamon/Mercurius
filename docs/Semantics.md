# Mercurius Semantics

This document describes behavior provided by the current Python implementation.
It is the behavioral reference for the project; implementation details are
described in [Architecture](Architecture.md).

## Events and event types

- An event is an `Event` instance whose `type` is a string. Publishing anything
  else, or an event with a non-string type, raises `TypeError`.
- An event type is an opaque string. `str`-based enums are accepted as strings.
- An event carries a dictionary payload, a source string, and a timestamp
  string. Mercurius does not validate or interpret payload contents.
- `EventBus.publish()` offers the same event object to each queue on the bus.
  Subscribers should treat events as read-only when multiple queues or
  subscribers may receive them.

## Subscriptions and delivery

- A subscription covers one or more distinct event types. Types are matched
  exactly; a subscriber receives no event types it did not subscribe to.
- Subscribers may be objects with `on_event(event)` or plain callables.
- Events are delivered to matching subscriptions in the order each queue
  dispatches them. Callback execution is serialized within a queue, but
  different queues may execute callbacks concurrently.
- Callbacks run on queue worker threads, never on the thread calling
  `publish()`. `publish()` enqueues accepted events and does not wait for
  callbacks to complete.
- The same event is offered to every queue. A queue's allow-list is checked
  before its optional predicate; rejected events are not enqueued. A predicate
  exception is logged and treated as rejection.
- `publish()` returns the number of queues that enqueued the event. Stopped
  queues do not count as accepting it.
- If a subscriber raises, the exception is logged and counted; other
  subscribers and later events continue to be processed.
- `unsubscribe()` is idempotent and marks the subscription inactive. A
  delivery that already captured its subscriber reference may still run, even
  if `unsubscribe()` completes before the callback starts; later dispatches
  skip the inactive subscription.
- A subscription retains its subscriber until it is unsubscribed or its queue
  is shut down. Shutting down a bus releases all of its subscriptions.

## Ordering and concurrency

- FIFO ordering is guaranteed independently for each queue, in the order
  events are enqueued there. No ordering is promised between queues.
- Each queue has one worker, so callbacks on that queue do not overlap.
- Publishing, subscribing, and unsubscribing are designed to be callable from
  different threads. Callbacks may publish more events or unsubscribe.

## Stop, drain, and shutdown

- `stop()` halts queue workers but keeps the bus's queues and subscriptions.
  `start()` resumes a stopped bus after its previous workers have exited.
- `stop(drain=True)` processes events already pending. A callback running on a
  queue may publish more events to that queue during the drain; they are
  processed before its worker exits. After stopping begins, otherwise-accepted
  events published from other threads are dropped by that queue.
- `stop(drain=False)` discards pending events. While a queue is stopped, events
  that pass its filters are dropped.
- `stop()` returns whether all workers finished before the timeout. A callback
  already running is not interrupted; a timeout or a call from that callback
  can result in `False`.
- `shutdown()` stops the workers, releases subscriptions, removes the queues
  from the bus, and permanently closes the bus. Repeated shutdown is safe.
  `start()`, `create_queue()`, and `subscribe()` on a closed bus raise
  `RuntimeError`.
- `Mercurius.shutdown()` shuts down every bus registered with the process-wide
  runtime. The runtime also performs cleanup at interpreter exit.

## Statistics

Queue statistics include:

| Counter | Meaning |
|---|---|
| `enqueued` | Events accepted and placed on the queue |
| `filtered` | Events rejected by the allow-list or predicate |
| `dropped` | Events accepted by filters but rejected because the queue was stopped |
| `dispatched` | Events removed from the queue for dispatch |
| `unmatched` | Dispatched events with no matching subscription |
| `delivered` | Successful subscriber calls |
| `failed` | Subscriber calls that raised |

These are operational counters, not delivery guarantees across process
failures. Mercurius does not provide persistence, replay, retries, priorities,
bounded queues, cross-process delivery, or worker pools.
