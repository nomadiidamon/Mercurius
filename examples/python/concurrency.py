"""
Concurrency: publishing from many threads.

  * publish(), subscribe() and unsubscribe() are thread-safe.
  * Order is FIFO per queue: events from one publisher thread arrive in the
    order that thread published them. Events from different threads interleave
    in an unspecified way.
  * Subscribers on one queue never run concurrently with each other, so they do
    not need their own locking for state touched only from that queue.
"""
import threading

import Mercurius
from Mercurius import Event, EventBus

THREADS = 4
PER_THREAD = 5


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("concurrency") as bus:
        received = []
        done = threading.Event()

        def collect(event: Event) -> None:
            received.append((event.payload["thread"], event.payload["i"]))  # no lock needed
            if len(received) == THREADS * PER_THREAD:
                done.set()

        bus.subscribe("T", collect)

        def publisher(thread_id: int) -> None:
            for i in range(PER_THREAD):
                bus.publish(Event("T", {"thread": thread_id, "i": i}))

        threads = [threading.Thread(target=publisher, args=(t,)) for t in range(THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        done.wait(5)

        for t in range(THREADS):
            order = [i for (tid, i) in received if tid == t]
            print(f"thread {t}: {order}  in order: {order == sorted(order)}")


if __name__ == "__main__":
    main()
