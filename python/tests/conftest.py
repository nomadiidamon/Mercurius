import pytest

from Mercurius import EventBus, runtime


@pytest.fixture(autouse=True)
def clean_runtime():
    """Every test starts initialized with no buses, and leaves nothing running."""
    runtime._reset()
    runtime.init()
    yield
    runtime._reset()


@pytest.fixture
def bus():
    b = EventBus()
    yield b
    b.shutdown()
