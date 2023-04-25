from typing import List, Callable, TypeVar

T = TypeVar('T')


class APIRateLimit:
    def __init__(self, max_concurrent_calls: int = 50):
        self._queue: List[Callable[[], None]] = []
        self._in_progress = 0
        self._max_concurrent_calls = max_concurrent_calls

    def call_api(self, api_function: Callable[[], T]) -> T:
        # TODO
        return api_function()
