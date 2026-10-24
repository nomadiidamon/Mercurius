"""
Mercurius - generic, queue-based pub/sub event library.

Call Mercurius.init() once at startup and Mercurius.shutdown() at exit.
"""
import threading
from typing import Optional

from . import runtime
from .event import Event
from .event_bus import EventBus
from .event_queue import EventQueue
from .event_type import EventType
from .events import ApplicationEvent, ErrorEvent, FileEvent, MessageEvent
from .runtime import init, is_initialized, shutdown
from .subscriber import BaseSubscriber, Subscriber
from .subscription import Subscription

__version__ = "0.1.0"

__all__ = [
    "ApplicationEvent",
    "BaseSubscriber",
    "ErrorEvent",
    "Event",
    "EventBus",
    "EventQueue",
    "EventType",
    "FileEvent",
    "MessageEvent",
    "Subscriber",
    "Subscription",
    "get_default_bus",
    "init",
    "is_initialized",
    "runtime",
    "shutdown",
    "shutdown_default_bus",
]

_default_bus: Optional[EventBus] = None
_default_lock = threading.Lock()


def get_default_bus() -> EventBus:
    """
    Return the process-wide bus. It is created (and Mercurius initialized, without
    a warning) on first use; a stopped bus is restarted, a shut-down one replaced.
    """
    global _default_bus
    with _default_lock:
        bus = _default_bus
        if bus is None or bus.is_closed:
            runtime.init()
            _default_bus = EventBus("default", _warn_uninitialized=False)
        elif not bus.is_running:
            bus.start()
        return _default_bus


def shutdown_default_bus(drain: bool = True) -> None:
    """Shut down the process-wide bus and release it."""
    global _default_bus
    with _default_lock:
        bus, _default_bus = _default_bus, None
    if bus is not None:
        bus.shutdown(drain=drain)
