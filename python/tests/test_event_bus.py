import pytest

from Mercurius import Event, EventBus
from helpers import Collector


def test_fifo_default_queue(bus):
    c = Collector(10)
    bus.subscribe("T", c)
    for i in range(10):
        bus.publish(Event("T", {"value": i}))
    assert c.wait()
    assert c.received == list(range(10))


def test_callable_subscriber(bus):
    c = Collector(1)
    bus.subscribe("T", c.on_event)
    bus.publish(Event("T", {"value": 1}))
    assert c.wait()


def test_invalid_subscriber_rejected(bus):
    with pytest.raises(TypeError):
        bus.subscribe("T", object())


def test_only_matching_type_delivered(bus):
    c = Collector(1)
    bus.subscribe("A", c)
    bus.publish(Event("B", {"value": 0}))
    bus.publish(Event("A", {"value": 1}))
    assert c.wait()
    assert c.received == [1]


def test_multiple_subscribers_same_type(bus):
    a, b = Collector(3), Collector(3)
    bus.subscribe("T", a)
    bus.subscribe("T", b)
    for i in range(3):
        bus.publish(Event("T", {"value": i}))
    assert a.wait() and b.wait()
    assert a.received == b.received == [0, 1, 2]


def test_multiple_event_types_separate_subscribers(bus):
    a, b = Collector(1), Collector(1)
    bus.subscribe("A", a)
    bus.subscribe("B", b)
    bus.publish(Event("A", {"value": "a"}))
    bus.publish(Event("B", {"value": "b"}))
    assert a.wait() and b.wait()
    assert a.received == ["a"] and b.received == ["b"]


def test_custom_queue_independent_fifo(bus):
    q = bus.create_queue()
    a, b = Collector(5), Collector(5)
    bus.subscribe("T", a)
    bus.subscribe("T", b, queue=q)
    for i in range(5):
        bus.publish(Event("T", {"value": i}))
    assert a.wait() and b.wait()
    assert a.received == b.received == list(range(5))


def test_multiple_custom_queues(bus):
    queues = [bus.create_queue() for _ in range(3)]
    cs = [Collector(4) for _ in queues]
    for q, c in zip(queues, cs):
        bus.subscribe("T", c, queue=q)
    for i in range(4):
        bus.publish(Event("T", {"value": i}))
    for c in cs:
        assert c.wait()
        assert c.received == [0, 1, 2, 3]


def test_foreign_queue_rejected(bus):
    other = EventBus()
    try:
        with pytest.raises(ValueError):
            bus.subscribe("T", Collector(), queue=other.create_queue())
    finally:
        other.shutdown()


def test_publish_returns_accepting_queue_count(bus):
    bus.create_queue()
    assert bus.publish(Event("T")) == 2


def test_queue_names_and_listing(bus):
    q = bus.create_queue(name="audit")
    assert q.name.endswith("/audit")
    assert bus.queues == (bus.default_queue, q)


def test_independent_buses_do_not_share_state():
    a, b = EventBus("a"), EventBus("b")
    try:
        ca, cb = Collector(1), Collector(1)
        a.subscribe("T", ca)
        b.subscribe("T", cb)
        a.publish(Event("T", {"value": "from-a"}))
        assert ca.wait()
        assert cb.received == []
        assert a.name == "a" and b.name == "b"
    finally:
        a.shutdown()
        b.shutdown()


def test_stats(bus):
    bus.create_queue(name="extra")
    s = bus.stats()
    assert s["running"] and len(s["queues"]) == 2
