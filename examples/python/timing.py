"""
Timing: what runs when, and on which thread.

  * publish() returns immediately; it never runs subscriber code.
  * Callbacks run on the queue's worker thread, one at a time, in FIFO order.
  * A slow subscriber delays later events on ITS queue only.
  * Never sleep() to wait for delivery: wait on a threading.Event instead.
"""
import threading
import time

import Mercurius
from Mercurius import Event, EventBus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    main_thread = threading.current_thread().name

    with EventBus("timing") as bus:
        done = threading.Event()

        def callback(event: Event) -> None:
            where = threading.current_thread().name
            print(f"  callback {event.payload['n']} on {where!r} "
                  f"(publisher was {main_thread!r})")
            if event.payload["n"] == 3:
                done.set()

        bus.subscribe("WORK", callback)

        start = time.perf_counter()
        for n in range(1, 4):
            bus.publish(Event("WORK", {"n": n}))
        print(f"publishing 3 events took {time.perf_counter() - start:.4f}s (non-blocking)")

        done.wait(5)  # deterministic wait, not sleep()

        # A slow consumer on its own queue does not hold up a fast one.
        slow_queue = bus.create_queue("slow")
        fast_done, slow_done = threading.Event(), threading.Event()

        def slow(event: Event) -> None:
            time.sleep(0.3)  # simulated work
            slow_done.set()

        bus.subscribe("JOB", lambda e: fast_done.set())          # default queue
        bus.subscribe("JOB", slow, queue=slow_queue)             # its own queue
        bus.publish(Event("JOB"))
        fast_done.wait(5)
        print("fast subscriber finished while slow one still running:", not slow_done.is_set())
        slow_done.wait(5)

    # Leaving the with-block calls shutdown(), which drains queued events first.


if __name__ == "__main__":
    main()
