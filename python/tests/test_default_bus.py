import pytest

import Mercurius
from Mercurius import Event, get_default_bus, shutdown_default_bus
from helpers import Collector


@pytest.fixture(autouse=True)
def clean_default():
    shutdown_default_bus()
    yield
    shutdown_default_bus()


def test_returns_same_bus_while_running():
    assert get_default_bus() is get_default_bus()


def test_works_end_to_end():
    c = Collector(1)
    get_default_bus().subscribe("T", c)
    get_default_bus().publish(Event("T", {"value": 1}))
    assert c.wait()


def test_shutdown_releases_and_next_call_creates_fresh_bus():
    first = get_default_bus()
    sub = first.subscribe("T", Collector())
    shutdown_default_bus()
    assert not first.is_running and not sub.active
    second = get_default_bus()
    assert second is not first and second.is_running


def test_shutdown_without_bus_is_noop():
    shutdown_default_bus()
    shutdown_default_bus()


def test_version_is_semver():
    parts = Mercurius.__version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)


def test_stopped_default_bus_is_restarted_not_replaced():
    bus = get_default_bus()
    c = Collector(1)
    bus.subscribe("T", c)
    bus.stop()
    again = get_default_bus()
    assert again is bus and bus.is_running
    bus.publish(Event("T", {"value": 1}))
    assert c.wait()


def test_closed_default_bus_is_replaced():
    first = get_default_bus()
    first.shutdown()
    assert get_default_bus() is not first


def test_global_shutdown_replaces_default_bus():
    first = get_default_bus()
    Mercurius.shutdown()
    second = get_default_bus()
    assert second is not first and second.is_running
