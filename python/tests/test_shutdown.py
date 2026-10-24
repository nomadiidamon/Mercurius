import threading

from Mercurius import Event, EventBus
from helpers import TIMEOUT, Collector


def test_stop_keeps_subscriptions_and_start_resumes():
    bus = EventBus()
    c = Collector(1)
    sub = bus.subscribe("T", c)
    bus.stop()
    assert not bus.is_running and sub.active
    bus.start()
    bus.publish(Event("T", {"value": 1}))
    assert c.wait()
    bus.shutdown()


def test_shutdown_releases_subscriptions():
    bus = EventBus()
    extra = bus.create_queue()
    a = bus.subscribe("T", Collector())
    b = bus.subscribe("T", Collector(), queue=extra)
    bus.shutdown()
    assert not bus.is_running
    assert not a.active and not b.active
    assert bus.default_queue.stats()["subscriptions"] == 0
    assert extra.stats()["subscriptions"] == 0


def test_shutdown_drains_before_releasing():
    bus = EventBus()
    c = Collector(20)
    sub = bus.subscribe("T", c)
    for i in range(20):
        bus.publish(Event("T", {"value": i}))
    bus.shutdown(drain=True)
    assert c.received == list(range(20))
    assert not sub.active


def test_publish_after_stop_is_dropped():
    bus = EventBus()
    c = Collector()
    bus.subscribe("T", c)
    bus.stop()
    assert bus.publish(Event("T", {"value": 1})) == 0
    assert bus.default_queue.stats()["dropped"] == 1
    assert c.received == []
    bus.shutdown()


def test_shutdown_is_idempotent():
    bus = EventBus()
    bus.shutdown()
    bus.shutdown()


def test_context_manager_shuts_down():
    with EventBus() as bus:
        sub = bus.subscribe("T", Collector())
    assert not bus.is_running and not sub.active


def test_shutdown_from_inside_callback_does_not_deadlock():
    bus = EventBus()
    finished = threading.Event()
    sub_holder = {}

    def cb(event):
        bus.shutdown()
        finished.set()

    sub_holder["sub"] = bus.subscribe("T", cb)
    bus.publish(Event("T"))
    assert finished.wait(TIMEOUT)
    assert not sub_holder["sub"].active


def test_stop_without_drain_discards_queued_events():
    bus = EventBus()
    gate, started = threading.Event(), threading.Event()
    seen = []

    def cb(event):
        seen.append(event.payload["value"])
        started.set()
        assert gate.wait(TIMEOUT)

    bus.subscribe("T", cb)
    bus.publish(Event("T", {"value": 1}))
    assert started.wait(TIMEOUT)
    bus.publish(Event("T", {"value": 2}))
    thread = bus.default_queue._thread
    bus.stop(drain=False, timeout=0.01)
    gate.set()
    thread.join(TIMEOUT)
    assert seen == [1]
    bus.shutdown()
