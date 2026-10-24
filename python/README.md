# Mercurius (Python)

Queue-based, thread-safe pub/sub event library: FIFO queues, object-based subscribers, explicit subscriptions, no dependencies.

```python
from Mercurius import Event, EventBus

with EventBus() as bus:
    bus.subscribe("GREETING", lambda e: print(e.payload))
    bus.publish(Event("GREETING", {"text": "hello"}))
```

Full documentation, examples and the project overview are in the [repository README](https://github.com/nomadiidamon/Mercurius#readme).
