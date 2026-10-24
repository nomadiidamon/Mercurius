"""FIFO event queue with its own dispatch thread and optional event filtering."""
import logging
import queue
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from .event import Event
from .event_type import EventType, EventTypes, normalize_event_types
from .subscription import Subscription

logger = logging.getLogger(__name__)

_STOP = object()  # sentinel that ends the dispatch loop


class _CallableSubscriber:
    def __init__(self, fn):
        self._fn = fn
        self.on_event = fn


class EventQueue:
    """
    Delivers events to its subscriptions in FIFO order on one worker thread.

    A queue does not have to receive every event on the bus. `event_types`
    (an allow-list) and `event_filter` (a predicate) decide what is enqueued;
    anything else is ignored at publish time and only counted in stats().

    Lifecycle: stop() halts the worker but keeps subscriptions (start() resumes);
    shutdown() stops and then releases every subscription.

    During stop(drain=True), events published by this queue's own callbacks are
    still accepted and delivered until the queue is empty; publishes from any
    other thread are dropped once stop() has been called.
    """

    def __init__(
        self,
        name: str = "queue",
        event_types: Optional[EventTypes] = None,
        event_filter: Optional[Callable[[Event], bool]] = None,
    ):
        self._name = name
        self._accepted = (
            None if event_types is None else frozenset(normalize_event_types(event_types))
        )
        self._filter = event_filter
        self._subscriptions: Dict[EventType, List[Subscription]] = {}
        self._lock = threading.RLock()
        self._queue: "queue.Queue" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._draining = False  # stop(drain=True) requested, worker not finished yet
        self._counts = {
            "enqueued": 0,    # accepted into the queue
            "filtered": 0,    # ignored by event_types/event_filter
            "dropped": 0,     # accepted by filters but queue was stopped
            "dispatched": 0,  # taken off the queue by the worker
            "unmatched": 0,   # dispatched with no subscription for the type
            "delivered": 0,   # successful subscriber calls
            "failed": 0,      # subscriber calls that raised
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def accepted_event_types(self) -> Optional[Tuple[EventType, ...]]:
        """None means every type is accepted (subject to event_filter)."""
        return None if self._accepted is None else tuple(sorted(self._accepted))

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def subscriptions(self) -> Tuple[Subscription, ...]:
        with self._lock:
            unique = {s.id: s for subs in self._subscriptions.values() for s in subs}
        return tuple(unique.values())

    def accepts(self, event: Event) -> bool:
        """True if this queue would take the event (ignores running state)."""
        if self._accepted is not None and event.type not in self._accepted:
            return False
        if self._filter is not None:
            try:
                return bool(self._filter(event))
            except Exception:
                logger.exception("Event filter of queue %r raised; event ignored", self._name)
                return False
        return True

    def subscribe(self, event_types: EventTypes, subscriber) -> Subscription:
        types = normalize_event_types(event_types)
        if self._accepted is not None:
            rejected = [t for t in types if t not in self._accepted]
            if rejected:
                raise ValueError(
                    f"queue {self._name!r} only accepts {sorted(self._accepted)}; "
                    f"cannot subscribe to {rejected}"
                )
        if not hasattr(subscriber, "on_event"):
            if not callable(subscriber):
                raise TypeError("subscriber must have on_event(event) or be callable")
            subscriber = _CallableSubscriber(subscriber)
        subscription = Subscription(types, subscriber, self)
        with self._lock:
            for event_type in types:
                self._subscriptions.setdefault(event_type, []).append(subscription)
        return subscription

    def enqueue(self, event: Event) -> bool:
        """
        Append an event. False means it was ignored (filtered) or dropped (stopped).
        Raises TypeError if `event` is not an Event with a str type.
        """
        if not isinstance(event, Event) or not isinstance(event.type, str):
            raise TypeError(
                f"expected an Event with a str type, got {type(event).__name__}"
            )
        if not self.accepts(event):
            with self._lock:
                self._counts["filtered"] += 1
            return False
        with self._lock:
            reentrant = self._draining and threading.current_thread() is self._thread
            if not self._running and not reentrant:
                self._counts["dropped"] += 1
                return False
            self._queue.put(event)
            self._counts["enqueued"] += 1
            return True

    def start(self) -> None:
        """Start the worker. Raises RuntimeError if a previous worker is still alive."""
        with self._lock:
            if self._running:
                return
            old = self._thread
            if old is not None and old.is_alive():
                raise RuntimeError(
                    f"queue {self._name!r}: previous worker is still running "
                    "(stop() timed out or is still draining)"
                )
            self._running = True
            self._draining = False
            self._thread = threading.Thread(
                target=self._dispatch_loop, name=f"mercurius-{self._name}", daemon=True
            )
            self._thread.start()

    def stop(self, drain: bool = True, timeout: Optional[float] = 5.0) -> bool:
        """
        Stop accepting events and stop the worker; subscriptions are kept.
        drain=True delivers already-queued events first (including ones published
        by this queue's own callbacks); drain=False discards them.

        Returns True if the worker has finished, False if it is still running
        (join timed out, or stop() was called from the worker's own callback).
        """
        with self._lock:
            thread = self._thread
            if self._running:
                self._running = False
                self._draining = drain
                if not drain:
                    with self._queue.mutex:
                        self._queue.queue.clear()
                self._queue.put(_STOP)

        if thread is None:
            return True
        if thread is not threading.current_thread():
            thread.join(timeout=timeout)
        return not thread.is_alive()

    def shutdown(self, drain: bool = True, timeout: Optional[float] = 5.0) -> bool:
        """stop(), then release every subscription. Returns stop()'s result."""
        finished = self.stop(drain=drain, timeout=timeout)
        for sub in self.subscriptions:
            sub.unsubscribe()
        return finished

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self._name,
                "running": self._running,
                "pending": self._queue.qsize(),
                "accepted_types": self.accepted_event_types,
                "has_filter": self._filter is not None,
                "subscriptions": len(self.subscriptions),
                **self._counts,
            }

    def __repr__(self) -> str:
        return f"<EventQueue {self._name!r} running={self._running} {self.stats()}>"

    def _remove(self, subscription: Subscription) -> None:
        with self._lock:
            for event_type in subscription.event_types:
                subs = self._subscriptions.get(event_type, [])
                if subscription in subs:
                    subs.remove(subscription)

    def _dispatch_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is _STOP:
                with self._lock:
                    if self._queue.empty():
                        self._draining = False
                        return
                    # Reentrant events landed behind the sentinel: process them first.
                    self._queue.put(_STOP)
                continue
            try:
                self._dispatch(item)
            except Exception:
                logger.exception("Queue %r failed to dispatch an event", self._name)

    def _dispatch(self, event: Event) -> None:
        with self._lock:
            subs = list(self._subscriptions.get(event.type, []))
            self._counts["dispatched"] += 1
            if not subs:
                self._counts["unmatched"] += 1
        for sub in subs:
            try:
                sub._deliver(event)
            except Exception:
                with self._lock:
                    self._counts["failed"] += 1
                logger.exception("Subscriber raised while handling %r event", event.type)
            else:
                with self._lock:
                    self._counts["delivered"] += 1
