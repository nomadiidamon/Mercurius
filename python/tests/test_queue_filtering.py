import pytest

from Mercurius import Event, EventBus
from helpers import Collector


def test_allow_list_ignores_other_types(bus):
    q = bus.create_queue(event_types=["A"])
    c = Collector(1)
    bus.subscribe("A", c, queue=q)
    assert q.accepts(Event("A")) and not q.accepts(Event("B"))
    bus.publish(Event("B", {"value": "ignored"}))
    bus.publish(Event("A", {"value": "kept"}))
    assert c.wait()
    assert c.received == ["kept"]
    stats = q.stats()
    assert stats["filtered"] == 1 and stats["enqueued"] == 1
    assert stats["accepted_types"] == ("A",)


def test_predicate_filter(bus):
    q = bus.create_queue(event_filter=lambda e: e.payload.get("keep", False))
    c = Collector(1)
    bus.subscribe("T", c, queue=q)
    bus.publish(Event("T", {"value": 1, "keep": False}))
    bus.publish(Event("T", {"value": 2, "keep": True}))
    assert c.wait()
    assert c.received == [2]
    assert q.stats()["has_filter"]


def test_types_and_predicate_combine(bus):
    q = bus.create_queue(event_types="A", event_filter=lambda e: e.source == "ok")
    assert q.accepts(Event("A", source="ok"))
    assert not q.accepts(Event("A", source="no"))
    assert not q.accepts(Event("B", source="ok"))


def test_other_queues_still_receive_everything(bus):
    narrow = bus.create_queue(event_types=["A"])
    everything = Collector(2)
    bus.subscribe(["A", "B"], everything)
    assert bus.publish(Event("A", {"value": 1})) == 2
    assert bus.publish(Event("B", {"value": 2})) == 1  # narrow queue ignored it
    assert everything.wait()
    assert narrow.stats()["filtered"] == 1


def test_subscribing_to_rejected_type_is_an_error(bus):
    q = bus.create_queue(event_types=["A"])
    with pytest.raises(ValueError):
        bus.subscribe("B", Collector(), queue=q)
    with pytest.raises(ValueError):
        bus.subscribe(["A", "B"], Collector(), queue=q)


def test_raising_filter_ignores_event_and_does_not_break_publish(bus):
    def bad(event):
        raise RuntimeError("filter bug")

    q = bus.create_queue(event_filter=bad)
    assert bus.publish(Event("T")) == 1  # default queue only
    assert q.stats()["filtered"] == 1


def test_accepted_types_none_means_all():
    assert EventBus("x").default_queue.accepted_event_types is None
