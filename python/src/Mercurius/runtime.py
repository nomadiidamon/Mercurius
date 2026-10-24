"""
Process-wide governor: tracks every live EventBus (and through it, its queues).

Mercurius.init() is the preferred way to start; creating an EventBus without it
auto-initializes (with a one-time warning). Mercurius.shutdown() shuts down all
tracked buses, which drops them and their queues from the registry.
"""
import atexit
import threading
import warnings
from typing import Any, Dict, List, Tuple

_lock = threading.RLock()
_initialized = False
_warned = False
_atexit_registered = False
_buses: List[Any] = []


def init() -> None:
    """Activate Mercurius. Idempotent."""
    global _initialized, _atexit_registered
    with _lock:
        _initialized = True
        if not _atexit_registered:
            atexit.register(_shutdown_at_exit)
            _atexit_registered = True


def shutdown(drain: bool = True, timeout: float = 5.0) -> None:
    """Shut down every tracked bus and clear the registry. Safe to call repeatedly."""
    global _initialized
    with _lock:
        buses = list(_buses)
        _buses.clear()
        _initialized = False
    for bus in buses:
        bus.shutdown(drain=drain, timeout=timeout)


def is_initialized() -> bool:
    return _initialized


def buses() -> Tuple[Any, ...]:
    """The live (not shut down) buses."""
    with _lock:
        return tuple(_buses)


def stats() -> Dict[str, Any]:
    return {"initialized": _initialized, "buses": [b.stats() for b in buses()]}


def _register(bus: Any, *, warn: bool = True) -> None:
    """Called by EventBus; auto-initializes if init() was not called first."""
    global _warned
    with _lock:
        if not _initialized:
            if warn and not _warned:
                _warned = True
                warnings.warn(
                    "Mercurius was not initialized; call Mercurius.init() explicitly "
                    "(auto-initializing now).",
                    RuntimeWarning,
                    stacklevel=3,
                )
            init()
        _buses.append(bus)


def _unregister(bus: Any) -> None:
    with _lock:
        if bus in _buses:
            _buses.remove(bus)


def _reset() -> None:
    """Test hook: shut everything down and forget the one-time warning."""
    global _warned
    shutdown(drain=False, timeout=1.0)
    _warned = False


def _shutdown_at_exit() -> None:
    shutdown(drain=True, timeout=2.0)
