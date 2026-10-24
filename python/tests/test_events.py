from Mercurius import ApplicationEvent, ErrorEvent, Event, FileEvent, MessageEvent


def test_child_events_are_events_with_default_types():
    assert isinstance(ApplicationEvent(), Event)
    assert ApplicationEvent().type == "application"
    assert MessageEvent().type == "message"
    assert FileEvent().type == "file"
    assert ErrorEvent().type == "error"


def test_specific_type_constants():
    e = FileEvent(FileEvent.CREATED, {"path": "a.txt"})
    assert e.type == "file.created"
    assert e.payload == {"path": "a.txt"}


def test_child_event_to_dict():
    e = MessageEvent(type=MessageEvent.SENT, payload={"text": "hi"}, source="s")
    assert e.to_dict()["type"] == "message.sent"


def test_constants_are_distinct():
    consts = [
        ApplicationEvent.STARTUP, ApplicationEvent.SHUTDOWN, ApplicationEvent.STATE_CHANGED,
        MessageEvent.SENT, MessageEvent.RECEIVED,
        FileEvent.CREATED, FileEvent.MODIFIED, FileEvent.DELETED, FileEvent.MOVED,
        ErrorEvent.ERROR, ErrorEvent.WARNING,
    ]
    assert len(set(consts)) == len(consts)
