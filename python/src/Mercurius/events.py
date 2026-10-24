"""
Ready-made Event subclasses for common categories. They only supply a default
type and well-known type constants; Mercurius itself gives them no meaning.
"""
from dataclasses import dataclass

from .event import Event
from .event_type import EventType


@dataclass
class ApplicationEvent(Event):
    """Application lifecycle (startup, shutdown, state changes)."""
    type: EventType = "application"

    STARTUP = "application.startup"
    SHUTDOWN = "application.shutdown"
    STATE_CHANGED = "application.state_changed"


@dataclass
class MessageEvent(Event):
    """Messages exchanged between components."""
    type: EventType = "message"

    SENT = "message.sent"
    RECEIVED = "message.received"


@dataclass
class FileEvent(Event):
    """File system activity; put the path in the payload."""
    type: EventType = "file"

    CREATED = "file.created"
    MODIFIED = "file.modified"
    DELETED = "file.deleted"
    MOVED = "file.moved"


@dataclass
class ErrorEvent(Event):
    """Errors and warnings."""
    type: EventType = "error"

    ERROR = "error"
    WARNING = "warning"
