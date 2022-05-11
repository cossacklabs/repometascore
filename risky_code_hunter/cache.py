import asyncio
from typing import Dict, Any, Tuple


class Cache:
    __results_cache: Dict[Any, Dict[str, Any]]
    __results_cache_lock: asyncio.Lock

    def __init__(self,):
        self.__results_cache = {}
        self.__results_cache_lock = asyncio.Lock()

    def __save_to_cache(self, key: Any, new_value: Any):
        self.__results_cache[key] = new_value
        return

    def __get_from_cache(self, key: Any) -> Any:
        return self.__results_cache.get(key)

    def __pop_from_cache(self, key: Any, default: Any = None) -> Any:
        return self.__results_cache.pop(key, default)

    # Enter lock
    # if key is present in cache -> wait for event to be set if it is present ->
    #   -> return value from cache dict with `is_result_already_present` flag as True
    # if there is no key ->
    #   -> if `create_new_awaitable` is True ->
    #       -> will create an event and save it to cache dict -> Exit lock ->
    #           -> return `is_result_already_present` as False and `None` as a result ->
    #               -> caller MUST call `_save_to_cache` when he will get a result
    #   -> elif `create_new_awaitable` is False -> Exit lock ->
    #       -> return `is_result_already_present` as False and `None` as a result
    # if timeout set to < 0 - will await infinitely
    async def get_and_await(self, key: Any, create_new_awaitable=False, timeout: float = 60) -> Tuple[bool, Any]:
        async with self.__results_cache_lock:
            is_result_already_present = False
            cached_result = self.__get_from_cache(key)
            if cached_result:
                event: asyncio.Event = cached_result.get('event')
                is_result_already_present = True
            elif create_new_awaitable:
                event = asyncio.Event()
                cached_result = {'event': event}
                self.__save_to_cache(key, cached_result)
        if is_result_already_present:
            if event:
                if timeout >= 0:
                    await asyncio.wait_for(event.wait(), timeout=timeout)
                else:
                    await event.wait()
            return is_result_already_present, cached_result.get('cached_result')
        return is_result_already_present, None

    async def get(self, key: Any, default: Any = None) -> Tuple[bool, Any]:
        try:
            return await self.get_and_await(key=key, create_new_awaitable=False, timeout=0)
        except asyncio.TimeoutError:
            # as we can get timeout exception if and only if result is already present, but must be awaited
            return True, default

    # Enter lock
    # if key is already present -> write `new_value` into dict -> if event is present -> set event
    # if there is no key -> create it -> write `new_value` into dict
    async def set(self, key: Any, new_value: Any):
        async with self.__results_cache_lock:
            cached_result = self.__get_from_cache(key)
            if cached_result:
                cached_result['cached_result'] = new_value
                event = cached_result.pop('event', None)
                if event:
                    event.set()
            else:
                cached_result = {'cached_result': new_value}
                self.__save_to_cache(key, cached_result)
        return

    # Enter lock
    # pop key from cache dict -> if it was present -> rewrite result to None ->
    #   -> if event was present -> set event
    async def pop(self, key: Any, default: Any = None):
        async with self.__results_cache_lock:
            cached_result = self.__pop_from_cache(key, default)
            if cached_result:
                result = cached_result.pop('cached_result', None)
                event = cached_result.pop('event', None)
                if event:
                    event.set()
                return result
        return None
