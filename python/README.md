# Mercurius (Python)

Mercurius: a queue-based, thread-safe publish/subscribe event library.

```python
from Mercurius import Event, EventBus

with EventBus() as bus:
    bus.subscribe("GREETING", lambda event: print(event.payload))
    bus.publish(Event("GREETING", {"text": "hello"}))
```

Requires Python 3.10 or newer. Install from this directory with
`python -m pip install .`; for development, use
`python -m pip install -e ".[dev]"` and run tests with `python -m pytest`.

See the [Python API reference](../docs/Mercurius.md), the [project overview](../README.md),
and [Python examples](../examples/python).
