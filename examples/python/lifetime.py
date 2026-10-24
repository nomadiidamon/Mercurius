"""
Subscriber lifetime.

Rules demonstrated here:
  1. A subscription keeps its subscriber alive (strong reference).
  2. unsubscribe() releases that reference and stops delivery. It is safe to repeat.
  3. The bus never owns your subscriber; you decide when it goes away.
"""
import gc
import weakref

import Mercurius
from Mercurius import Event, EventBus


class Listener:
    def on_event(self, event: Event) -> None:
        print("  listener got", event.payload)


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("lifetime") as bus:
        listener = Listener()
        probe = weakref.ref(listener)  # lets us observe when the object really dies
        subscription = bus.subscribe("PING", listener)

        # Rule 1: dropping our own reference does not destroy the listener,
        # because the subscription still holds it.
        del listener
        gc.collect()
        print("alive while subscribed:", probe() is not None)

        bus.publish(Event("PING", {"n": 1}))
        bus.stop()   # drain so the line above prints before we continue
        bus.start()

        # Rule 2: unsubscribe releases the subscriber; calling it twice is fine.
        subscription.unsubscribe()
        subscription.unsubscribe()
        gc.collect()
        print("alive after unsubscribe:", probe() is not None)
        print("subscription state:", subscription)

        # Events published now reach nobody.
        bus.publish(Event("PING", {"n": 2}))


if __name__ == "__main__":
    main()
