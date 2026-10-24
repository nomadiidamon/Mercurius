import threading

from Mercurius import Event
from helpers import TIMEOUT, Collector


def run_threads(targets):
    threads = [threading.Thread(target=t) for t in targets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(TIMEOUT)


def test_concurrent_publishers_keep_per_thread_order(bus):
    n_threads, per = 4, 50
    c = Collector(n_threads * per)
    bus.subscribe("T", c)

    def make(t):
        def pub():
            for i in range(per):
                bus.publish(Event("T", {"value": (t, i)}))
        return pub

    run_threads([make(t) for t in range(n_threads)])
    assert c.wait()
    for t in range(n_threads):
        assert [i for (tt, i) in c.received if tt == t] == list(range(per))


def test_order_holds_on_each_queue(bus):
    q = bus.create_queue()
    a, b = Collector(100), Collector(100)
    bus.subscribe("T", a)
    bus.subscribe("T", b, queue=q)
    for i in range(100):
        bus.publish(Event("T", {"value": i}))
    assert a.wait() and b.wait()
    assert a.received == b.received == list(range(100))


def test_subscribe_and_unsubscribe_while_publishing(bus):
    stable = Collector(200)
    bus.subscribe("T", stable)
    errors = []

    def churn():
        try:
            for _ in range(100):
                bus.subscribe("T", Collector()).unsubscribe()
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    def publish():
        for i in range(200):
            bus.publish(Event("T", {"value": i}))

    run_threads([churn, churn, publish])
    assert stable.wait()
    assert errors == []
    assert stable.received == list(range(200))


def test_concurrent_unsubscribe_of_same_subscription(bus):
    sub = bus.subscribe("T", Collector())
    run_threads([sub.unsubscribe] * 8)
    assert not sub.active
    assert bus.default_queue.stats()["subscriptions"] == 0
