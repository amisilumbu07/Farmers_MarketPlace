"""In-process domain events. ponytail: synchronous, same transaction; swap for a queue when work must leave the request."""
from collections import defaultdict
from collections.abc import Callable

_handlers: dict[str, list[Callable]] = defaultdict(list)


def subscribe(event: str) -> Callable:
    def register(handler: Callable) -> Callable:
        _handlers[event].append(handler)
        return handler

    return register


def publish(event: str, db, **payload) -> None:
    for handler in _handlers[event]:
        handler(db, **payload)
