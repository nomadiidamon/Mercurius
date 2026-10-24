"""
Reentrancy: callbacks may publish and unsubscribe.

Because callbacks run on the worker thread and publish() only appends to a queue,
a callback can publish without deadlocking. The new event is processed AFTER the
current callback returns (FIFO), never in the middle of it.
"""
import threading

import Mercurius
from Mercurius import Event, EventBus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("reentrancy") as bus:
        done = threading.Event()

        # A publishes B from inside its callback.
        def on_a(event: Event) -> None:
            print("A start")
            bus.publish(Event("B"))
            print("A end (B has not run yet)")

        def on_b(event: Event) -> None:
            print("B runs after A returned")
            done.set()

        bus.subscribe("A", on_a)
        bus.subscribe("B", on_b)
        bus.publish(Event("A"))
        done.wait(5)

        # A one-shot subscriber that unsubscribes itself.
        finished = threading.Event()
        holder = {}

        def once(event: Event) -> None:
            print("one-shot got", event.payload)
            holder["sub"].unsubscribe()

        holder["sub"] = bus.subscribe("ONCE", once)
        bus.subscribe("ONCE", lambda e: finished.set() if e.payload["n"] == 2 else None)
        bus.publish(Event("ONCE", {"n": 1}))
        bus.publish(Event("ONCE", {"n": 2}))  # the one-shot no longer sees this
        finished.wait(5)
        print("one-shot still active:", holder["sub"].active)


if __name__ == "__main__":
    main()
