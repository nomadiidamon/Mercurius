"""Basic Mercurius usage: object subscriber, callable subscriber, unsubscribe."""
import Mercurius
from Mercurius import Event, EventBus


class Printer:
    def on_event(self, event: Event) -> None:
        print(f"[{event.type}] {event.payload}")


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus() as bus:  # stop() drains queued events on exit
        subscription = bus.subscribe("GREETING", Printer())
        bus.subscribe("GREETING", lambda e: print("callable got", e.source))

        bus.publish(Event("GREETING", {"text": "hello"}, source="basic.py"))
        bus.publish(Event("GREETING", {"text": "world"}, source="basic.py"))

        subscription.unsubscribe()  # no further deliveries to Printer


if __name__ == "__main__":
    main()
