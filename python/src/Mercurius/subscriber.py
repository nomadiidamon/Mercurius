"""Subscriber protocol and an optional convenience base class."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Protocol, Tuple, Union, runtime_checkable

from .event import Event
from .event_type import EventTypes, normalize_event_types

if TYPE_CHECKING:
    from .event_bus import EventBus
    from .event_queue import EventQueue
    from .subscription import Subscription


@runtime_checkable
class Subscriber(Protocol):
    """Any object with on_event(event) is a subscriber; no inheritance needed."""

    def on_event(self, event: Event) -> None: ...


class BaseSubscriber(ABC):
    """
    Optional base class. It remembers the subscriptions it created so one
    call to unsubscribe_all() releases them, e.g. before the object is discarded.
    """

    @abstractmethod
    def on_event(self, event: Event) -> None: ...

    def subscribe_to(
        self,
        bus: "EventBus",
        event_types: EventTypes,
        queue: Optional["EventQueue"] = None,
    ) -> "Subscription":
        subscription = bus.subscribe(event_types, self, queue=queue)
        # setdefault so subclasses need not call super().__init__()
        self.__dict__.setdefault("_mercurius_subscriptions", []).append(subscription)
        return subscription

    @property
    def subscriptions(self) -> Tuple["Subscription", ...]:
        subs: List["Subscription"] = self.__dict__.get("_mercurius_subscriptions", [])
        return tuple(s for s in subs if s.active)

    def unsubscribe_from(self, event_types: Union[EventTypes, Event]) -> None:
        """
        Stop receiving the given event type(s) (or the type of the given Event).
        A subscription that also covers other types is replaced by one for the
        remaining types, so those keep arriving. Unknown types are ignored.
        """
        removed = set(normalize_event_types(
            event_types.type if isinstance(event_types, Event) else event_types
        ))
        kept: List["Subscription"] = []
        for sub in self.__dict__.get("_mercurius_subscriptions", []):
            if not sub.active:
                continue
            remaining = [t for t in sub.event_types if t not in removed]
            if len(remaining) == len(sub.event_types):
                kept.append(sub)
                continue
            sub.unsubscribe()
            if remaining:
                kept.append(sub.queue.subscribe(remaining, self))
        self.__dict__["_mercurius_subscriptions"] = kept

    def unsubscribe_all(self) -> None:
        for sub in self.__dict__.get("_mercurius_subscriptions", []):
            sub.unsubscribe()
        self.__dict__["_mercurius_subscriptions"] = []
