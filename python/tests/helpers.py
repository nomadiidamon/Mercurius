"""Shared test helpers; synchronization uses threading.Event, never sleep()."""
import threading

TIMEOUT = 5.0


class Collector:
    """Subscriber that records payload["value"] and signals once `expected` arrived."""

    def __init__(self, expected=1):
        self.received = []
        self.done = threading.Event()
        self._expected = expected

    def on_event(self, event):
        self.received.append(event.payload.get("value"))
        if len(self.received) >= self._expected:
            self.done.set()

    def wait(self):
        return self.done.wait(TIMEOUT)
