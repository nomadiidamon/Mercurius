import logging
import threading

from Mercurius import Event
from helpers import TIMEOUT, Collector


def test_exception_isolated_from_later_subscribers(bus):
    def bad(event):
        raise RuntimeError("boom")

    c = Collector(2)
    bus.subscribe("T", bad)
    bus.subscribe("T", c)
    bus.publish(Event("T", {"value": 1}))
    bus.publish(Event("T", {"value": 2}))
    assert c.wait()
    assert c.received == [1, 2]


def test_worker_survives_failures(bus):
    calls = []

    def flaky(event):
        calls.append(event.payload["value"])
        raise ValueError("always")

    marker = Collector(3)
    bus.subscribe("T", flaky)
    bus.subscribe("T", marker)
    for i in range(3):
        bus.publish(Event("T", {"value": i}))
    assert marker.wait()
    assert calls == [0, 1, 2]
    assert bus.default_queue.is_running


def test_failures_are_logged(bus, caplog):
    done = threading.Event()

    def bad(event):
        try:
            raise RuntimeError("logged")
        finally:
            done.set()

    bus.subscribe("T", bad)
    with caplog.at_level(logging.ERROR, logger="Mercurius"):
        bus.publish(Event("T"))
        assert done.wait(TIMEOUT)
        bus.shutdown()  # join the worker so the log record exists
    assert any("raised" in r.getMessage() for r in caplog.records)


def test_failure_counted_in_queue_stats(bus):
    done = threading.Event()

    def bad(event):
        done.set()
        raise RuntimeError("x")

    bus.subscribe("T", bad)
    bus.publish(Event("T"))
    assert done.wait(TIMEOUT)
    bus.stop()
    assert bus.default_queue.stats()["failed"] == 1
