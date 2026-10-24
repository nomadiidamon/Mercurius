import os
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

import Mercurius
from Mercurius import Event, EventBus, get_default_bus, runtime
from helpers import Collector

SRC = Path(__file__).resolve().parent.parent / "src"


def test_init_is_idempotent():
    runtime._reset()
    assert not Mercurius.is_initialized()
    Mercurius.init()
    Mercurius.init()
    assert Mercurius.is_initialized()


def test_explicit_init_does_not_warn():
    runtime._reset()
    Mercurius.init()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        EventBus().shutdown()


def test_auto_init_warns_once():
    runtime._reset()
    with pytest.warns(RuntimeWarning, match="init"):
        first = EventBus()
    assert Mercurius.is_initialized()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        second = EventBus()
    first.shutdown()
    second.shutdown()


def test_default_bus_auto_initializes_silently():
    runtime._reset()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        bus = get_default_bus()
    assert Mercurius.is_initialized() and bus in runtime.buses()


def test_runtime_tracks_live_buses_and_queues():
    a, b = EventBus("a"), EventBus("b")
    a.create_queue("extra")
    assert set(runtime.buses()) == {a, b}
    stats = runtime.stats()
    assert stats["initialized"]
    assert {s["name"]: len(s["queues"]) for s in stats["buses"]} == {"a": 2, "b": 1}


def test_stop_keeps_bus_tracked_but_shutdown_untracks_it():
    bus = EventBus()
    bus.stop()
    assert bus in runtime.buses()
    bus.shutdown()
    assert bus not in runtime.buses()


def test_global_shutdown_closes_every_bus_and_queue():
    a, b = EventBus("a"), EventBus("b")
    extra = a.create_queue()
    sub = a.subscribe("T", Collector())
    Mercurius.shutdown()
    assert not Mercurius.is_initialized()
    assert runtime.buses() == ()
    assert a.is_closed and b.is_closed
    assert not a.default_queue.is_running and not extra.is_running and not b.default_queue.is_running
    assert not sub.active


def test_global_shutdown_is_idempotent():
    Mercurius.shutdown()
    Mercurius.shutdown()


def test_global_shutdown_drains_by_default():
    bus = EventBus()
    c = Collector(20)
    bus.subscribe("T", c)
    for i in range(20):
        bus.publish(Event("T", {"value": i}))
    Mercurius.shutdown()
    assert c.received == list(range(20))


def test_closed_bus_rejects_new_work():
    bus = EventBus()
    bus.shutdown()
    with pytest.raises(RuntimeError):
        bus.create_queue()
    with pytest.raises(RuntimeError):
        bus.subscribe("T", Collector())
    with pytest.raises(RuntimeError):
        bus.start()


def test_queues_cleaned_when_bus_shuts_down():
    bus = EventBus()
    q = bus.create_queue()
    bus.subscribe("T", Collector(), queue=q)
    bus.shutdown()
    assert bus.queues == ()
    assert q.stats()["subscriptions"] == 0 and not q.is_running
    assert bus.publish(Event("T")) == 0


def test_bus_shutdown_is_idempotent_and_reports_state():
    bus = EventBus()
    assert bus.shutdown() is True
    assert bus.shutdown() is True
    assert bus.stats()["closed"] and "closed" in repr(bus)


def test_new_bus_works_after_global_shutdown():
    Mercurius.shutdown()
    with pytest.warns(RuntimeWarning):  # not explicitly re-initialized
        bus = EventBus()
    c = Collector(1)
    bus.subscribe("T", c)
    bus.publish(Event("T", {"value": 1}))
    assert c.wait()
    bus.shutdown()


def test_exit_hook_shuts_everything_down():
    bus = EventBus()
    runtime._shutdown_at_exit()
    assert bus.is_closed


def test_process_exits_cleanly_with_a_running_bus():
    code = (
        "import Mercurius\n"
        "Mercurius.init()\n"
        "bus = Mercurius.EventBus()\n"
        "bus.subscribe('T', lambda e: None)\n"
        "bus.publish(Mercurius.Event('T'))\n"
    )
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", code],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
