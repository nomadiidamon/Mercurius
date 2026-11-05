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

Run every example with `scripts/run_examples.bat` (Windows) or
`scripts/run_examples.sh`. Package metadata is read from
`../project.ini` by `setup.py`.

A C++ implementation is planned but not yet implemented.

See the [Python API reference](https://nomadiidamon.github.io/Mercurius/PythonAPI.html), the [project overview](https://nomadiidamon.github.io/Mercurius/index.html),
and [Python examples](https://nomadiidamon.github.io/Mercurius/examples.html).
