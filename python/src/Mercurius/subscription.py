"""Handle linking event types, a subscriber and a queue."""
import itertools
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Tuple

from .event_type import EventType
from .subscriber import Subscriber

if TYPE_CHECKING:
    from .event_queue import EventQueue

_ids = itertools.count(1)


def _describe(subscriber: Any) -> str:
    target = getattr(subscriber, "_fn", subscriber)
    return getattr(target, "__qualname__", None) or type(target).__qualname__


class Subscription:
    """
    Returned by EventBus.subscribe(). Holds a strong reference to the
    subscriber until unsubscribe() (or a bus/queue shutdown) releases it.
    Counters and repr()/to_dict() are provided for debugging.
    """

    def __init__(
        self,
        event_types: Iterable[EventType],
        subscriber: Subscriber,
        queue: "EventQueue",
    ):
        self._id = next(_ids)
        self._event_types: Tuple[EventType, ...] = tuple(event_types)
        self._subscriber: Optional[Subscriber] = subscriber
        self._subscriber_name = _describe(subscriber)  # kept after release
        self._queue = queue
        self._lock = threading.Lock()
        self._active = True
        self._created_at = datetime.now().isoformat()
        self._delivered = 0
        self._failed = 0
        self._last_event_at: Optional[str] = None
        self._last_error: Optional[str] = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def event_types(self) -> Tuple[EventType, ...]:
        return self._event_types

    @property
    def queue(self) -> "EventQueue":
        return self._queue

    @property
    def active(self) -> bool:
        return self._active

    @property
    def subscriber_name(self) -> str:
        return self._subscriber_name

    @property
    def delivered_count(self) -> int:
        return self._delivered

    @property
    def error_count(self) -> int:
        return self._failed

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def unsubscribe(self) -> None:
        """Stop future delivery and release the subscriber. Safe to call multiple times."""
        with self._lock:
            if not self._active:
                return
            self._active = False
            self._subscriber = None
        self._queue._remove(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self._id,
            "active": self._active,
            "subscriber": self._subscriber_name,
            "event_types": list(self._event_types),
            "queue": self._queue.name,
            "created_at": self._created_at,
            "delivered": self._delivered,
            "failed": self._failed,
            "last_event_at": self._last_event_at,
            "last_error": self._last_error,
        }

    def __repr__(self) -> str:
        state = "active" if self._active else "inactive"
        return (
            f"<Subscription #{self._id} {state} {self._subscriber_name} "
            f"types={list(self._event_types)} queue={self._queue.name!r} "
            f"delivered={self._delivered} failed={self._failed}>"
        )

    def _deliver(self, event) -> None:
        with self._lock:
            subscriber = self._subscriber if self._active else None
        if subscriber is None:
            return
        self._last_event_at = datetime.now().isoformat()
        try:
            subscriber.on_event(event)
        except Exception as exc:
            self._failed += 1
            self._last_error = repr(exc)
            raise
        self._delivered += 1
