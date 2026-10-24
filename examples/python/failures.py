"""
Failures: what happens when things go wrong.

  * An exception in a subscriber is logged; other subscribers still run and the
    worker keeps going.
  * A raising queue filter is logged and the event is ignored by that queue.
  * Subscription and queue counters tell you what happened afterwards.
  * Programming mistakes at subscribe time raise immediately.
"""
import logging
import threading

import Mercurius
from Mercurius import Event, EventBus

# Mercurius reports failures through the standard logging module.
logging.basicConfig(level=logging.ERROR, format="LOG: %(message)s")


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("failures") as bus:
        done = threading.Event()

        def crashes(event: Event) -> None:
            raise RuntimeError("subscriber bug")

        def healthy(event: Event) -> None:
            print("healthy subscriber still received", event.payload)
            done.set()

        bad_sub = bus.subscribe("T", crashes)
        bus.subscribe("T", healthy)
        bus.publish(Event("T", {"n": 1}))
        done.wait(5)

        bus.stop()  # join the worker so the counters are final
        print("crashing subscription:", bad_sub)
        print("last error:", bad_sub.last_error)
        print("queue failed count:", bus.default_queue.stats()["failed"])
        bus.start()

        # Mistakes caught right away:
        for label, call in [
            ("not callable / no on_event", lambda: bus.subscribe("T", object())),
            ("empty type list", lambda: bus.subscribe([], healthy)),
            ("non-string type", lambda: bus.subscribe([42], healthy)),
        ]:
            try:
                call()
            except (TypeError, ValueError) as exc:
                print(f"{label}: {type(exc).__name__}: {exc}")

        # A buggy filter never breaks publish(); the queue just ignores the event.
        broken = bus.create_queue("broken-filter", event_filter=lambda e: 1 / 0)
        bus.publish(Event("T", {"n": 2}))
        print("events ignored by broken filter:", broken.stats()["filtered"])


if __name__ == "__main__":
    main()
