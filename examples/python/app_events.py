"""Domus-AI style layering: the application owns its event vocabulary."""
from enum import Enum

import Mercurius
from Mercurius import Event, EventBus


class AppEvent(str, Enum):
    MODEL_LOADED = "model_loaded"
    ERROR = "error"


class ModelManager:
    def on_event(self, event: Event) -> None:
        print("model manager saw:", event.type, event.payload)


def main() -> None:
    Mercurius.init()  # explicit start-up (an EventBus created without it auto-inits with a warning)
    with EventBus() as bus:
        bus.subscribe(AppEvent.MODEL_LOADED, ModelManager())
        bus.publish(Event(AppEvent.MODEL_LOADED, {"model": "example"}))


if __name__ == "__main__":
    main()
