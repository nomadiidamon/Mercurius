@page Concepts Concepts

# Mercurius Concepts

**Mercurius defines how events move, not what they mean.** Applications own
event meaning and the vocabulary used by their subscribers.

## Event

An event carries a string `type`, a dictionary `payload`, and metadata:
`source` and an ISO-formatted `timestamp`. Event types are application-defined;
Mercurius does not impose a required naming scheme. Ready-made event subclasses
are conveniences, not a required vocabulary.

## Runtime

The process-wide runtime tracks live buses. Call `Mercurius.init()` during
startup and `Mercurius.shutdown()` during cleanup. The runtime shuts down all
registered buses, and also registers cleanup for interpreter exit. Constructing
a bus before calling `init()` initializes the runtime automatically and warns
once.

## EventBus

An `EventBus` publishes events to its default queue and any custom queues
created on it. Separate buses have separate subscriptions and queues.
`get_default_bus()` provides a process-wide convenience bus when a shared bus
is appropriate.

## Queue

A queue is an independent FIFO delivery path with its own worker thread. Each
bus starts with a default queue. Custom queues can separate consumers so a
slow callback on one queue does not block callbacks on another.

An optional event-type allow-list, predicate, or both can filter a queue.
Filtering happens as the event is published; the queue does not enqueue events
it rejects.

## Subscriber and subscription

A subscriber can be an object with `on_event(event)` or a callable. It receives
only events whose types match its subscription. `BaseSubscriber` is an optional
helper for tracking and releasing subscriptions.

A `Subscription` represents the relationship between event types, a subscriber,
and a queue. It can be unsubscribed directly and exposes counters useful for
debugging. A subscription keeps its subscriber alive until it is released.

## Lifecycle

`stop()` stops a bus's workers but retains its queues and subscriptions;
`start()` resumes it. `shutdown()` stops workers, releases subscriptions, and
closes the bus permanently. A closed bus cannot create queues or subscriptions.

With `drain=True`, a queue processes pending events before stopping. Events
published by that queue's own callbacks during the drain are also processed;
otherwise-accepted publishes from other threads after stopping begins are
dropped. With `drain=False`, pending events are discarded.

For exact guarantees and edge cases, see [Semantics](Semantics.md). For the
implementation structure, see [Architecture](Architecture.md).
