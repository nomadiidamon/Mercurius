import gc
import threading
import weakref

import pytest

from Mercurius import Event
from helpers import TIMEOUT, Collector


def test_subscribe_returns_active_subscription(bus):
    sub = bus.subscribe("T", Collector())
    assert sub.active
    assert sub.event_types == ("T",)
    assert sub.queue is bus.default_queue


def test_unsubscribe_is_idempotent_and_stops_delivery(bus):
    gone, marker = Collector(1), Collector(1)
    sub = bus.subscribe("T", gone)
    bus.subscribe("T", marker)  # same queue: once it fires, `gone` would have too
    sub.unsubscribe()
    sub.unsubscribe()
    assert not sub.active
    bus.publish(Event("T", {"value": 1}))
    assert marker.wait()
    assert gone.received == []


def test_multiple_event_types_one_subscription(bus):
    c = Collector(2)
    sub = bus.subscribe(["A", "B"], c)
    bus.publish(Event("A", {"value": "a"}))
    bus.publish(Event("C", {"value": "c"}))
    bus.publish(Event("B", {"value": "b"}))
    assert c.wait()
    assert c.received == ["a", "b"]
    assert sub.event_types == ("A", "B")


def test_duplicate_types_delivered_once(bus):
    c = Collector(1)
    bus.subscribe(["A", "A"], c)
    bus.publish(Event("A", {"value": 1}))
    assert c.wait()
    assert c.received == [1]


def test_invalid_event_types(bus):
    with pytest.raises(ValueError):
        bus.subscribe([], Collector())
    with pytest.raises(TypeError):
        bus.subscribe([1], Collector())


def test_unsubscribe_one_type_set_removes_all_types(bus):
    c, marker = Collector(), Collector(2)
    sub = bus.subscribe(["A", "B"], c)
    bus.subscribe(["A", "B"], marker)
    sub.unsubscribe()
    bus.publish(Event("A", {"value": 1}))
    bus.publish(Event("B", {"value": 2}))
    assert marker.wait()
    assert c.received == []


def test_unsubscribe_inside_callback(bus):
    seen = []
    holder = {}
    marker = Collector(2)

    def once(event):
        seen.append(event.payload["value"])
        holder["sub"].unsubscribe()

    holder["sub"] = bus.subscribe("T", once)
    bus.subscribe("T", marker)
    bus.publish(Event("T", {"value": 1}))
    bus.publish(Event("T", {"value": 2}))
    assert marker.wait()
    assert seen == [1]


def test_subscription_holds_then_releases_subscriber(bus):
    c = Collector()
    ref = weakref.ref(c)
    sub = bus.subscribe("T", c)
    del c
    gc.collect()
    assert ref() is not None  # kept alive by the subscription
    sub.unsubscribe()
    gc.collect()
    assert ref() is None


def test_debug_counters_and_to_dict(bus):
    c = Collector(2)
    sub = bus.subscribe("T", c)
    assert sub.delivered_count == 0 and sub.to_dict()["last_event_at"] is None
    bus.publish(Event("T", {"value": 1}))
    bus.publish(Event("T", {"value": 2}))
    assert c.wait()
    bus.stop()  # joins the worker so counters are final
    d = sub.to_dict()
    assert d["delivered"] == 2 and d["failed"] == 0
    assert d["subscriber"] == "Collector" and d["queue"] == bus.default_queue.name
    assert d["last_event_at"] is not None


def test_error_counters(bus):
    done = threading.Event()

    def bad(event):
        done.set()
        raise RuntimeError("boom")

    sub = bus.subscribe("T", bad)
    bus.publish(Event("T"))
    assert done.wait(TIMEOUT)
    bus.shutdown()  # joins the worker so counters are final
    assert sub.error_count == 1
    assert "boom" in sub.last_error


def test_repr_and_subscriber_name(bus):
    sub = bus.subscribe("T", lambda e: None)
    assert "Subscription" in repr(sub) and "active" in repr(sub)
    sub.unsubscribe()
    assert "inactive" in repr(sub)
    assert sub.subscriber_name  # still available after release
