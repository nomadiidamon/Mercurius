"""Event bus: a default queue plus optional independent queues."""
import itertools
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from .event import Event
from .event_queue import EventQueue
from .event_type import EventTypes
from .subscription import Subscription
from . import runtime

_bus_ids = itertools.count(1)


class EventBus:
    """
    publish() offers an event to every queue on the bus. Each queue may
    filter it out; the ones that accept it deliver FIFO to their own
    subscriptions. Ordering is guaranteed per queue only.

    The bus starts on construction and is tracked by the Mercurius runtime
    (call Mercurius.init() first; otherwise it auto-initializes with a warning).
      stop()     halts the workers; subscriptions are kept and start() resumes.
      shutdown() stops the workers, releases every subscription and closes the
                 bus for good: its queues are dropped and start(), create_queue()
                 and subscribe() raise RuntimeError.
    While stopped, publish() drops events.
    """

    def __init__(self, name: Optional[str] = None, *, _warn_uninitialized: bool = True):
        self._name = name or f"bus-{next(_bus_ids)}"
        self._lock = threading.RLock()
        self._closed = False
        self._default_queue = EventQueue(f"{self._name}/default")
        self._queues: List[EventQueue] = [self._default_queue]
        self._queue_count = 0
        runtime._register(self, warn=_warn_uninitialized)
        self._default_queue.start()

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_closed(self) -> bool:
        return self._closed

    def _check_open(self) -> None:
        if self._closed:
            raise RuntimeError(f"bus {self._name!r} has been shut down")

    @property
    def default_queue(self) -> EventQueue:
        return self._default_queue

    @property
    def queues(self) -> Tuple[EventQueue, ...]:
        with self._lock:
            return tuple(self._queues)

    @property
    def is_running(self) -> bool:
        return self._default_queue.is_running

    def create_queue(
        self,
        name: Optional[str] = None,
        event_types: Optional[EventTypes] = None,
        event_filter: Optional[Callable[[Event], bool]] = None,
    ) -> EventQueue:
        """
        Create an independent FIFO queue. With event_types and/or event_filter
        the queue ignores every other event instead of receiving all of them.
        """
        with self._lock:
            self._check_open()
            self._queue_count += 1
            label = name or f"queue-{self._queue_count}"
            queue = EventQueue(f"{self._name}/{label}", event_types, event_filter)
            self._queues.append(queue)
            queue.start()
        return queue

    def subscribe(
        self,
        event_types: EventTypes,
        subscriber,
        queue: Optional[EventQueue] = None,
    ) -> Subscription:
        """
        Subscribe an object with on_event(event), or a plain callable, to one
        event type or a list of types. Only events of those types are delivered.
        The subscription keeps the subscriber alive until it is released.
        """
        target = queue if queue is not None else self._default_queue
        with self._lock:
            self._check_open()
            if target not in self._queues:
                raise ValueError("queue does not belong to this bus")
        return target.subscribe(event_types, subscriber)

    def publish(self, event: Event) -> int:
        """
        Non-blocking; safe from any thread, including subscriber callbacks.
        Returns how many queues accepted the event. Raises TypeError if `event`
        is not an Event with a str type.
        """
        accepted = 0
        if not isinstance(event, Event) or not isinstance(event.type, str):
            raise TypeError(
                f"expected an Event with a str type, got {type(event).__name__}"
            )
        for q in self.queues:
            if q.enqueue(event):
                accepted += 1
        return accepted

    def start(self) -> None:
        """Restart stopped workers. RuntimeError if the bus is shut down or a worker is stuck."""
        with self._lock:
            self._check_open()
            queues = list(self._queues)
        stuck = []
        for q in queues:
            try:
                q.start()
            except RuntimeError:
                stuck.append(q.name)
        if stuck:
            raise RuntimeError(f"workers still running for queues: {stuck}")

    def stop(self, drain: bool = True, timeout: Optional[float] = 5.0) -> bool:
        """Stop all workers; subscriptions stay registered. True if every worker finished."""
        results = [q.stop(drain=drain, timeout=timeout) for q in self.queues]
        return all(results)

    def shutdown(self, drain: bool = True, timeout: Optional[float] = 5.0) -> bool:
        """
        Stop all workers, release every subscription and close the bus; the queues
        are dropped and the runtime stops tracking it. Idempotent.
        Returns True if every worker finished.
        """
        with self._lock:
            if self._closed:
                return True
            self._closed = True
            queues = list(self._queues)
        results = [q.shutdown(drain=drain, timeout=timeout) for q in queues]
        with self._lock:
            self._queues.clear()
        runtime._unregister(self)
        return all(results)

    def stats(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "running": self.is_running,
            "closed": self._closed,
            "queues": [q.stats() for q in self.queues],
        }

    def __repr__(self) -> str:
        state = "closed" if self._closed else f"running={self.is_running}"
        return f"<EventBus {self._name!r} {state} queues={len(self.queues)}>"

    def __enter__(self) -> "EventBus":
        return self

    def __exit__(self, *exc) -> None:
        self.shutdown()
