from Mercurius import Event


def test_construction_defaults():
    e = Event("T")
    assert e.type == "T"
    assert e.payload == {}
    assert e.source == ""
    assert e.timestamp


def test_payload_and_source():
    e = Event(type="T", payload={"a": 1}, source="unit")
    assert e.payload == {"a": 1}
    assert e.source == "unit"


def test_payload_default_is_not_shared():
    a, b = Event("T"), Event("T")
    a.payload["x"] = 1
    assert b.payload == {}


def test_to_dict():
    e = Event("T", {"a": 1}, "s")
    assert e.to_dict() == {
        "type": "T",
        "payload": {"a": 1},
        "source": "s",
        "timestamp": e.timestamp,
    }
