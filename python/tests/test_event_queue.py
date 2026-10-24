import threading

from Mercurius import Event, EventQueue
from helpers import TIMEOUT, Collector


def make_queue(**kw):
    q = EventQueue("test", **kw)
    q.start()
    return q


def test_fifo():
    q = make_queue()
    c = Collector(10)
    q.subscribe("T", c)
    for i in range(10):
        q.enqueue(Event("T", {"value": i}))
    assert c.wait()
    assert c.received == list(range(10))
    q.shutdown()


def test_empty_queue_stats():
    q = make_queue()
    s = q.stats()
    assert s["pending"] == 0 and s["enqueued"] == 0 and s["running"]
    q.shutdown()


def test_worker_lifecycle():
    q = EventQueue("lifecycle")
    assert not q.is_running
    q.start()
    q.start()  # idempotent
    assert q.is_running
    q.stop()
    q.stop()  # idempotent
    assert not q.is_running
    q.start()  # restartable
    assert q.is_running
    q.shutdown()


def test_enqueue_when_stopped_is_dropped():
    q = EventQueue("stopped")
    assert q.enqueue(Event("T")) is False
    assert q.stats()["dropped"] == 1


def test_stop_drains_queued_events():
    q = make_queue()
    c = Collector(50)
    q.subscribe("T", c)
    for i in range(50):
        q.enqueue(Event("T", {"value": i}))
    q.stop(drain=True)
    assert c.received == list(range(50))


def test_stop_without_drain_discards_pending():
    q = make_queue()
    started, gate = threading.Event(), threading.Event()
    received = []

    def blocker(event):
        received.append(event.payload["value"])
        started.set()
        assert gate.wait(TIMEOUT)

    q.subscribe("T", blocker)
    q.enqueue(Event("T", {"value": "A"}))
    assert started.wait(TIMEOUT)
    q.enqueue(Event("T", {"value": "B"}))
    q.enqueue(Event("T", {"value": "C"}))
    thread = q._thread
    q.stop(drain=False, timeout=0.01)  # worker is busy in A, so this returns early
    gate.set()
    thread.join(TIMEOUT)
    assert received == ["A"]


def test_subscribe_on_stopped_queue_then_start_delivers():
    q = EventQueue("late")
    c = Collector(1)
    q.subscribe("T", c)
    q.start()
    q.enqueue(Event("T", {"value": 1}))
    assert c.wait()
    q.shutdown()


def test_callback_can_enqueue_without_deadlock():
    q = make_queue()
    c = Collector(2)

    def republish(event):
        q.enqueue(Event("B", {"value": 2}))
        c.on_event(event)

    q.subscribe("A", republish)
    q.subscribe("B", c)
    q.enqueue(Event("A", {"value": 1}))
    assert c.wait()
    assert c.received == [1, 2]
    q.shutdown()


def test_stats_count_dispatch_and_unmatched():
    q = make_queue()
    c = Collector(1)
    q.subscribe("A", c)
    q.enqueue(Event("A", {"value": 1}))
    assert c.wait()
    q.stop()
    s = q.stats()
    assert s["enqueued"] == 1 and s["dispatched"] == 1 and s["delivered"] == 1
    assert s["unmatched"] == 0 and s["failed"] == 0
    q.start()
    q.enqueue(Event("NOBODY"))
    q.stop()
    assert q.stats()["unmatched"] == 1


def test_name_and_repr():
    q = EventQueue("named")
    assert q.name == "named"
    assert "named" in repr(q)
