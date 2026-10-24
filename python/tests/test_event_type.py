from enum import Enum

import pytest

from Mercurius import Event
from Mercurius.event_type import normalize_event_types
from helpers import Collector


class Kind(str, Enum):
    A = "a"
    B = "b"


def test_single_string():
    assert normalize_event_types("A") == ("A",)


def test_iterables_keep_order_and_drop_duplicates():
    assert normalize_event_types(["B", "A", "B"]) == ("B", "A")
    assert normalize_event_types(("A", "B")) == ("A", "B")
    assert normalize_event_types(t for t in ["X", "Y"]) == ("X", "Y")
    assert set(normalize_event_types({"A", "B"})) == {"A", "B"}


@pytest.mark.parametrize("empty", [[], (), set()])
def test_empty_is_rejected(empty):
    with pytest.raises(ValueError):
        normalize_event_types(empty)


@pytest.mark.parametrize("bad", [[1], ["A", None], [("A",)]])
def test_non_strings_are_rejected(bad):
    with pytest.raises(TypeError):
        normalize_event_types(bad)


def test_str_enum_members_are_valid_types():
    assert normalize_event_types(Kind.A) == (Kind.A,)
    assert normalize_event_types([Kind.A, Kind.B]) == (Kind.A, Kind.B)


def test_str_enum_end_to_end(bus):
    c = Collector(2)
    bus.subscribe([Kind.A, Kind.B], c)
    bus.publish(Event(Kind.A, {"value": 1}))
    bus.publish(Event(Kind.B, {"value": 2}))
    assert c.wait()
    assert c.received == [1, 2]


def test_str_enum_and_plain_string_are_interchangeable(bus):
    c = Collector(2)
    bus.subscribe(Kind.A, c)
    bus.publish(Event("a", {"value": "plain"}))
    bus.publish(Event(Kind.A, {"value": "enum"}))
    assert c.wait()
    assert c.received == ["plain", "enum"]


def test_str_enum_in_queue_allow_list(bus):
    q = bus.create_queue(event_types=[Kind.A])
    assert q.accepts(Event(Kind.A)) and q.accepts(Event("a"))
    assert not q.accepts(Event(Kind.B))
