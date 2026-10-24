"""
stop() versus shutdown().

  stop()      halts the worker threads. Subscriptions are KEPT, so start() resumes
              delivery. While stopped, publish() drops events.
  shutdown()  stops the workers and then RELEASES every subscription. Use it when
              you are finished with the bus. `with EventBus() as bus:` calls it.
"""
import Mercurius
from Mercurius import Event, EventBus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    bus = EventBus("shutdown-demo")
    received = []
    sub = bus.subscribe("TICK", lambda e: received.append(e.payload["n"]))

    bus.publish(Event("TICK", {"n": 1}))
    bus.stop()  # drain=True (default): event 1 is delivered before stopping
    print("after stop:    running =", bus.is_running, "| subscription active =", sub.active)

    accepted = bus.publish(Event("TICK", {"n": 2}))  # dropped: workers are stopped
    print("published while stopped, queues accepting it:", accepted)

    bus.start()  # same subscription, delivery resumes
    bus.publish(Event("TICK", {"n": 3}))
    bus.stop()
    print("received:", received)  # [1, 3]

    bus.shutdown()  # releases the subscription for good
    print("after shutdown: running =", bus.is_running, "| subscription active =", sub.active)

    # drain=False discards events that are still waiting instead of delivering them.
    bus2 = EventBus("discard-demo")
    bus2.shutdown(drain=False)


if __name__ == "__main__":
    main()
