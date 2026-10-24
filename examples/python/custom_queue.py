"""Custom queues: independent FIFO delivery paths on one bus."""
import threading

import Mercurius
from Mercurius import Event, EventBus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    done = threading.Event()
    with EventBus() as bus:
        slow_queue = bus.create_queue()

        bus.subscribe("TICK", lambda e: print("default queue:", e.payload["n"]))

        def slow(e: Event) -> None:
            print("custom queue :", e.payload["n"])
            if e.payload["n"] == 2:
                done.set()

        # A slow consumer on its own queue does not delay the default queue.
        bus.subscribe("TICK", slow, queue=slow_queue)

        for n in range(3):
            bus.publish(Event("TICK", {"n": n}))

        done.wait(5)


if __name__ == "__main__":
    main()
