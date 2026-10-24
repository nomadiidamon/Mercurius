"""
Debugging: inspecting a bus, its queues and its subscriptions.

  * repr() of a bus, queue or subscription is meant to be readable.
  * queue.stats() / bus.stats() return counters as plain dicts.
  * subscription.to_dict() shows delivery and error counters per subscriber.
"""
import pprint

import Mercurius
from Mercurius import Event, EventBus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("debug") as bus:
        audit = bus.create_queue("audit", event_types=["REFUND"])
        sub = bus.subscribe(["ORDER", "REFUND"], lambda e: None)
        bus.subscribe("REFUND", lambda e: 1 / 0, queue=audit)  # will fail

        bus.publish(Event("ORDER"))
        bus.publish(Event("REFUND"))
        bus.publish(Event("UNKNOWN"))  # nobody subscribed: counted as "unmatched"

        bus.stop()  # join workers so the numbers are final

        print(bus)
        print(audit)
        print(sub)
        print()
        pprint.pprint(bus.stats())
        print()
        for q in bus.queues:
            for s in q.subscriptions:
                pprint.pprint(s.to_dict())


if __name__ == "__main__":
    main()
