import threading

import pytest

from Mercurius import Event, EventBus, EventQueue
from helpers import TIMEOUT, Collector


@pytest.mark.parametrize("bad", ["oops", None, 42, {"type": "T"}, Event(type=1)])
def test_bus_publish_rejects_non_events(bus, bad):
    with pytest.raises(TypeError):
        bus.publish(bad)


def test_queue_enqueue_rejects_non_events():
    q = EventQueue("q")
    q.start()
    try:
        with pytest.raises(TypeError):
            q.enqueue("oops")
    finally:
        q.shutdown()


def test_rejected_publish_does_not_disturb_the_worker(bus):
    c = Collector(1)
    bus.subscribe("T", c)
    with pytest.raises(TypeError):
        bus.publish("oops")
    assert bus.default_queue.stats()["enqueued"] == 0
    bus.publish(Event("T", {"value": 1}))
    assert c.wait()


def test_worker_survives_an_unexpected_dispatch_error(bus):
    q = bus.default_queue
    original = q._dispatch
    state = {"calls": 0}

    def flaky(event):
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("internal failure")
        original(event)

    q._dispatch = flaky
    c = Collector(1)
    bus.subscribe("T", c)
    bus.publish(Event("T", {"value": "lost"}))
    bus.publish(Event("T", {"value": "kept"}))
    assert c.wait()
    assert c.received == ["kept"]
    assert q._thread.is_alive()


def _block_worker(bus):
    """Subscribe a callback that blocks the default worker; returns (started, gate)."""
    started, gate = threading.Event(), threading.Event()

    def blocker(event):
        started.set()
        assert gate.wait(TIMEOUT)

    bus.subscribe("BLOCK", blocker)
    bus.publish(Event("BLOCK"))
    assert started.wait(TIMEOUT)
    return started, gate


def test_stop_reports_whether_worker_finished(bus):
    assert bus.stop() is True
    assert bus.stop() is True  # already stopped

    never_started = EventQueue("idle")
    assert never_started.stop() is True


def test_stop_timeout_returns_false_and_blocks_restart():
    bus = EventBus()
    _, gate = _block_worker(bus)
    thread = bus.default_queue._thread

    assert bus.stop(timeout=0.01) is False
    with pytest.raises(RuntimeError):
        bus.default_queue.start()
    with pytest.raises(RuntimeError):
        bus.start()

    gate.set()
    thread.join(TIMEOUT)
    bus.start()  # the old worker is gone, restart is allowed again
    c = Collector(1)
    bus.subscribe("T", c)
    bus.publish(Event("T", {"value": 1}))
    assert c.wait()
    bus.shutdown()


def test_restart_never_creates_a_second_worker():
    bus = EventBus()
    _, gate = _block_worker(bus)
    old = bus.default_queue._thread
    bus.stop(timeout=0.01)
    with pytest.raises(RuntimeError):
        bus.start()
    assert bus.default_queue._thread is old
    gate.set()
    old.join(TIMEOUT)
    bus.shutdown()


def test_stop_from_inside_callback_returns_false(bus):
    result = []
    done = threading.Event()

    def cb(event):
        result.append(bus.stop(timeout=0))
        done.set()

    bus.subscribe("T", cb)
    bus.publish(Event("T"))
    assert done.wait(TIMEOUT)
    assert result == [False]


def test_reentrant_publish_during_drain_is_delivered(bus):
    received = []
    done = threading.Event()

    def chain(event):
        n = event.payload["n"]
        received.append(n)
        if n == 0:
            bus.stop(drain=True, timeout=0)  # now draining, from the worker itself
        if n < 3:
            assert bus.publish(Event("T", {"n": n + 1})) == 1
        else:
            done.set()

    bus.subscribe("T", chain)
    bus.publish(Event("T", {"n": 0}))
    assert done.wait(TIMEOUT)
    bus.default_queue._thread.join(TIMEOUT)
    assert received == [0, 1, 2, 3]
    assert not bus.default_queue._thread.is_alive()


def test_reentrant_publish_without_drain_is_dropped(bus):
    received = []
    done = threading.Event()

    def cb(event):
        received.append(event.payload["n"])
        bus.stop(drain=False, timeout=0)
        assert bus.publish(Event("T", {"n": 1})) == 0
        done.set()

    bus.subscribe("T", cb)
    bus.publish(Event("T", {"n": 0}))
    assert done.wait(TIMEOUT)
    bus.default_queue._thread.join(TIMEOUT)
    assert received == [0]


def test_drain_ignores_publishes_from_other_threads(bus):
    _, gate = _block_worker(bus)
    stopper = threading.Thread(target=bus.stop, kwargs={"timeout": TIMEOUT})
    stopper.start()
    # The stop() call sets running=False before it blocks in join().
    while bus.default_queue.is_running:
        pass
    assert bus.publish(Event("T")) == 0
    assert bus.default_queue.stats()["dropped"] == 1
    gate.set()
    stopper.join(TIMEOUT)
