"""
BaseSubscriber and the ready-made event classes.

BaseSubscriber is optional (any object with on_event() works). It adds
subscribe_to(), unsubscribe_from() and unsubscribe_all() so an object can
manage its own subscriptions. ApplicationEvent/MessageEvent/FileEvent/ErrorEvent are plain
Event subclasses with a default type and handy type constants.
"""
import Mercurius
from Mercurius import (
    ApplicationEvent,
    BaseSubscriber,
    ErrorEvent,
    Event,
    EventBus,
    FileEvent,
    MessageEvent,
)


class Logger(BaseSubscriber):
    """Subscribes to several event types and dispatches on event.type."""

    def __init__(self, bus: EventBus):
        self.subscribe_to(bus, [
            ApplicationEvent.STARTUP,
            MessageEvent.RECEIVED,
            FileEvent.CREATED,
            ErrorEvent.ERROR,
        ])

    def on_event(self, event: Event) -> None:
        print(f"[{event.type}] {event.payload}")


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("classes") as bus:
        logger = Logger(bus)

        bus.publish(ApplicationEvent(ApplicationEvent.STARTUP, {"version": "1.0"}))
        bus.publish(MessageEvent(MessageEvent.RECEIVED, {"text": "hello"}, source="chat"))
        bus.publish(FileEvent(FileEvent.CREATED, {"path": "notes.txt"}))
        bus.publish(ErrorEvent(ErrorEvent.ERROR, {"reason": "disk full"}))
        bus.publish(FileEvent(FileEvent.DELETED, {"path": "old.txt"}))  # not subscribed: ignored

        bus.stop()  # let the queue drain so output appears before the summary
        print("active subscriptions:", len(logger.subscriptions))

        # Stop listening to some types; the others keep arriving. Pass a type, a
        # list of types, or an Event instance (its type is used).
        bus.start()
        logger.unsubscribe_from([MessageEvent.RECEIVED, FileEvent.CREATED])
        bus.publish(MessageEvent(MessageEvent.RECEIVED, {"text": "ignored now"}))
        bus.publish(ErrorEvent(ErrorEvent.ERROR, {"reason": "still delivered"}))
        bus.stop()
        print("types still subscribed:", [s.event_types for s in logger.subscriptions])
        bus.start()

        logger.unsubscribe_all()  # one call releases everything this object subscribed
        print("after unsubscribe_all:", len(logger.subscriptions))


if __name__ == "__main__":
    main()
