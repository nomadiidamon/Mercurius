"""
Several independent buses in one process.

Each EventBus has its own queues, subscriptions and worker threads, so buses
never see each other's events. This is the recommended way to isolate
components (and tests). get_default_bus() is only a convenience for apps that
want a single process-wide bus.
"""
import Mercurius
from Mercurius import Event, EventBus, get_default_bus, shutdown_default_bus


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus("audio") as audio, EventBus("video") as video:
        audio.subscribe("START", lambda e: print("audio bus got START"))
        video.subscribe("START", lambda e: print("video bus got START"))

        # Only the audio bus sees this event.
        audio.publish(Event("START", {"track": "intro.wav"}))

    # The shared, process-wide bus: created on first use.
    shared = get_default_bus()
    print("same object every call:", shared is get_default_bus())
    shared.subscribe("HELLO", lambda e: print("default bus got", e.payload))
    shared.publish(Event("HELLO", {"from": "anywhere in the process"}))

    # Releases subscriptions; the next get_default_bus() returns a fresh bus.
    shutdown_default_bus()
    print("fresh bus after shutdown:", get_default_bus() is not shared)
    shutdown_default_bus()


if __name__ == "__main__":
    main()
