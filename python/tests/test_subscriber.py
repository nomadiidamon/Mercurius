import pytest

from Mercurius import BaseSubscriber, Event, Subscriber
from helpers import Collector


class Recorder(BaseSubscriber):
    def __init__(self, expected=1):
        self.inner = Collector(expected)

    def on_event(self, event):
        self.inner.on_event(event)


def test_base_class_is_abstract():
    with pytest.raises(TypeError):
        BaseSubscriber()


def test_protocol_matches_duck_typing_and_base_class():
    assert isinstance(Collector(), Subscriber)
    assert isinstance(Recorder(), Subscriber)


def test_subscribe_to_and_receive(bus):
    r = Recorder(1)
    sub = r.subscribe_to(bus, "T")
    assert r.subscriptions == (sub,)
    bus.publish(Event("T", {"value": 7}))
    assert r.inner.wait()
    assert r.inner.received == [7]


def test_unsubscribe_all(bus):
    r = Recorder()
    a = r.subscribe_to(bus, "A")
    b = r.subscribe_to(bus, ["B", "C"], queue=bus.create_queue())
    r.unsubscribe_all()
    assert not a.active and not b.active
    assert r.subscriptions == ()
    r.unsubscribe_all()  # safe to repeat


def test_unsubscribe_from_whole_subscription(bus):
    r = Recorder(1)
    a = r.subscribe_to(bus, "A")
    b = r.subscribe_to(bus, "B")
    r.unsubscribe_from("A")
    assert not a.active and b.active
    assert r.subscriptions == (b,)
    bus.publish(Event("A", {"value": "a"}))
    bus.publish(Event("B", {"value": "b"}))
    assert r.inner.wait()
    assert r.inner.received == ["b"]


def test_unsubscribe_from_one_of_several_types_keeps_the_rest(bus):
    r = Recorder(2)
    q = bus.create_queue()
    original = r.subscribe_to(bus, ["A", "B", "C"], queue=q)
    r.unsubscribe_from("B")
    assert not original.active
    (replacement,) = r.subscriptions
    assert replacement.event_types == ("A", "C") and replacement.queue is q
    for t in ("A", "B", "C"):
        bus.publish(Event(t, {"value": t}))
    assert r.inner.wait()
    assert r.inner.received == ["A", "C"]


def test_unsubscribe_from_accepts_list_and_event_instance(bus):
    r = Recorder()
    r.subscribe_to(bus, ["A", "B", "C", "D"])
    r.unsubscribe_from(["A", "B"])
    r.unsubscribe_from(Event("C"))
    (sub,) = r.subscriptions
    assert sub.event_types == ("D",)


def test_unsubscribe_from_unknown_type_is_a_noop(bus):
    r = Recorder()
    sub = r.subscribe_to(bus, "A")
    r.unsubscribe_from("NOPE")
    assert sub.active and r.subscriptions == (sub,)


def test_unsubscribe_from_without_subscriptions_is_safe():
    Recorder().unsubscribe_from("A")


def test_unsubscribe_from_all_types_equals_unsubscribe_all(bus):
    r = Recorder()
    a = r.subscribe_to(bus, ["A", "B"])
    r.unsubscribe_from(["A", "B"])
    assert not a.active and r.subscriptions == ()


def test_subclass_without_super_init_works(bus):
    class NoInit(BaseSubscriber):
        def __init__(self):
            pass

        def on_event(self, event):
            pass

    n = NoInit()
    n.subscribe_to(bus, "T")
    assert len(n.subscriptions) == 1
