"""Generic event: a type, an opaque payload, and metadata."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from .event_type import EventType


@dataclass
class Event:
    type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "timestamp": self.timestamp,
        }
