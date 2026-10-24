"""Event type identifier; Mercurius assigns no meaning to the value."""
from typing import Iterable, Tuple, Union

EventType = str

EventTypes = Union[EventType, Iterable[EventType]]


def normalize_event_types(event_types: EventTypes) -> Tuple[EventType, ...]:
    """Accept one type or an iterable of types; return a de-duplicated tuple."""
    if isinstance(event_types, str):
        items: Tuple[EventType, ...] = (event_types,)
    else:
        items = tuple(event_types)
    if not items:
        raise ValueError("at least one event type is required")
    for item in items:
        if not isinstance(item, str):
            raise TypeError(f"event types must be str, got {type(item).__name__}")
    return tuple(dict.fromkeys(items))
