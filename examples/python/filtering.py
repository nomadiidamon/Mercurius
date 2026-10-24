"""
Filtering: queues do not have to receive every event.

publish() offers each event to every queue on the bus. A queue can refuse
events up front, so they are never stored or dispatched:

  * event_types=[...]    allow-list of event types
  * event_filter=func    predicate on the Event (applied after event_types)

On top of that, a subscriber only ever gets the event types it subscribed to,
which can be one type or a list of types.
"""
import threading

import Mercurius
from Mercurius import Event, EventBus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("filtering") as bus:
        done = threading.Event()

        # 1. Default queue: accepts everything.
        bus.subscribe(["ORDER", "REFUND"], lambda e: print("default queue:", e.type))

        # 2. Audit queue: only cares about refunds.
        audit = bus.create_queue("audit", event_types=["REFUND"])
        bus.subscribe("REFUND", lambda e: print("audit queue  :", e.type), queue=audit)

        # 3. Big-orders queue: type allow-list plus a predicate.
        big = bus.create_queue(
            "big-orders",
            event_types=["ORDER"],
            event_filter=lambda e: e.payload.get("total", 0) >= 100,
        )

        def on_big(event: Event) -> None:
            print("big orders   :", event.payload)
            done.set()

        bus.subscribe("ORDER", on_big, queue=big)

        # publish() reports how many queues accepted the event.
        print("small order accepted by", bus.publish(Event("ORDER", {"total": 10})), "queue(s)")
        print("big order accepted by  ", bus.publish(Event("ORDER", {"total": 500})), "queue(s)")
        print("refund accepted by     ", bus.publish(Event("REFUND", {"total": 5})), "queue(s)")
        done.wait(5)

        # A queue refuses subscriptions it could never serve.
        try:
            bus.subscribe("ORDER", lambda e: None, queue=audit)
        except ValueError as exc:
            print("rejected:", exc)

        bus.stop()
        for q in bus.queues:
            s = q.stats()
            print(f"{s['name']:>22}: enqueued={s['enqueued']} filtered={s['filtered']}")


if __name__ == "__main__":
    main()
