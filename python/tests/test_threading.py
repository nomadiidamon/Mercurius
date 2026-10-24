import threading

from Mercurius import Event, EventBus
from helpers import TIMEOUT, Collector


def test_callbacks_run_on_worker_not_publisher(bus):
    seen = []
    done = threading.Event()

    def cb(event):
        seen.append(threading.current_thread())
        done.set()

    bus.subscribe("T", cb)
    bus.publish(Event("T"))
    assert done.wait(TIMEOUT)
    assert seen[0] is not threading.current_thread()
    assert seen[0].name.startswith("mercurius-")
    assert seen[0].daemon


def test_each_queue_has_its_own_worker_thread(bus):
    q = bus.create_queue()
    threads = {}
    done = threading.Event()

    def record(label):
        def cb(event):
            threads[label] = threading.current_thread()
            if len(threads) == 2:
                done.set()
        return cb

    bus.subscribe("T", record("default"))
    bus.subscribe("T", record("custom"), queue=q)
    bus.publish(Event("T"))
    assert done.wait(TIMEOUT)
    assert threads["default"] is not threads["custom"]


def test_callbacks_on_one_queue_never_overlap(bus):
    lock = threading.Lock()
    state = {"active": 0, "max": 0, "calls": 0}
    done = threading.Event()
    total = 100

    def make():
        def cb(event):
            with lock:
                state["active"] += 1
                state["max"] = max(state["max"], state["active"])
            threading.Event().wait(0.0002)  # widen the window in which an overlap would show
            with lock:
                state["active"] -= 1
                state["calls"] += 1
                if state["calls"] == total * 2:
                    done.set()
        return cb

    bus.subscribe("T", make())
    bus.subscribe("T", make())
    for _ in range(total):
        bus.publish(Event("T"))
    assert done.wait(TIMEOUT)
    assert state["max"] == 1


def test_blocked_queue_does_not_delay_another_queue(bus):
    slow_queue = bus.create_queue("slow")
    started, gate = threading.Event(), threading.Event()
    fast = Collector(3)

    def slow(event):
        started.set()
        assert gate.wait(TIMEOUT)

    bus.subscribe("T", slow, queue=slow_queue)
    bus.subscribe("T", fast)
    for i in range(3):
        bus.publish(Event("T", {"value": i}))
    assert started.wait(TIMEOUT)
    assert fast.wait()  # delivered while the slow queue is still blocked
    assert fast.received == [0, 1, 2]
    gate.set()


def test_publish_does_not_wait_for_subscribers(bus):
    started, gate = threading.Event(), threading.Event()

    def slow(event):
        started.set()
        assert gate.wait(TIMEOUT)

    bus.subscribe("T", slow)
    bus.publish(Event("T"))
    assert started.wait(TIMEOUT)
    for _ in range(50):  # would hang if publish ran subscriber code
        bus.publish(Event("T"))
    assert bus.default_queue.stats()["pending"] >= 1
    gate.set()


def test_publish_racing_with_shutdown_is_safe():
    bus = EventBus()
    c = Collector(10 ** 9)
    bus.subscribe("T", c)
    errors = []
    go = threading.Event()

    def publisher():
        go.wait()
        try:
            for i in range(2000):
                bus.publish(Event("T", {"value": i}))
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=publisher) for _ in range(4)]
    for t in threads:
        t.start()
    go.set()
    assert bus.shutdown() is True
    for t in threads:
        t.join(TIMEOUT)
    assert errors == []
    assert bus.is_closed
