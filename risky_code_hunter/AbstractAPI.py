import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

import aiohttp


class AbstractAPI(ABC):
    max_retries: int
    min_await: float
    max_await: float
    verbose: int
    __session: aiohttp.ClientSession
    _response_handlers: Dict
    __results_cache: Dict
    __results_cache_lock: asyncio.Lock
    UNPREDICTED_RESPONSE_HANDLER_INDEX = -1

    def __init__(self, session: aiohttp.ClientSession = None, config: Dict = None, verbose: int = 0):
        if config is None:
            config = {}
        if session:
            self.__session = session
        else:
            self.__session = aiohttp.ClientSession()
        self.max_retries = config.get('request_max_retries', 5)
        self.min_await = config.get('request_min_await', 5.0)
        self.max_await = config.get('request_max_await', 15.0)
        self.verbose = verbose
        self._response_handlers = self.create_response_handlers()
        self.handle_unpredicted_response = self._response_handlers.pop(
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX, self.handle_unpredicted_response
        )
        self.__results_cache = {}

    @abstractmethod
    def create_response_handlers(self) -> Dict:
        raise NotImplementedError("You should implement this!")

    @abstractmethod
    async def initialize_tokens(self) -> bool:
        raise NotImplementedError("You should implement this!")

    async def handle_unpredicted_response(self, url, params, resp, **kwargs) -> bool:
        raise Exception(
            f"Unpredicted response from server\n"
            f"Requested URL: {url}\n"
            f"Requested params: {params}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.text()}"
        )

    async def handle_response_200(self, **kwargs):
        return False

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
    async def _await_from_cache(self, key: Any, create_new_awaitable=False) -> Tuple[bool, Any]:
        async with self.__results_cache_lock.acquire():
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
                await event.wait()
            return is_result_already_present, cached_result.get('cached_result')
        return is_result_already_present, None

    # Enter lock
    # if key is already present -> write `new_value` into dict -> if event is present -> set event
    # if there is no key -> create it -> write `new_value` into dict
    async def _save_to_cache(self, key: Any, new_value: Any):
        async with self.__results_cache_lock.acquire():
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
    async def _pop_from_cache(self, key: Any, default: Any = None):
        async with self.__results_cache_lock.acquire():
            cached_result = self.__pop_from_cache(key, default)
            if cached_result:
                cached_result['cached_result'] = None
                event = cached_result.pop('event', None)
                if event:
                    event.set()
        return


    async def request(self, method, url, params=None, data=None, headers=None) -> aiohttp.ClientResponse:
        retry = 0
        while True:
            retry += 1
            try:
                async with self.__session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                ) as resp:
                    resp_data = await resp.read()
                    response_handler = self._response_handlers.get(
                        resp.status,
                        self.handle_unpredicted_response
                    )
                    need_retry = await response_handler(
                        retry=retry,
                        resp=resp,
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        headers=headers,
                        resp_data=resp_data
                    )
                    if need_retry:
                        await self.request_limit_timeout_and_await(retry_num=retry)
                        continue
                    break
            except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientConnectorError,
                    aiohttp.client_exceptions.ServerDisconnectedError, aiohttp.client_exceptions.ClientOSError):
                await self.request_limit_timeout_and_await(retry_num=retry)
                continue
        return resp

    # will sleep current async flow on time
    # based on retry number
    # and random value between self.min_await
    # and self.max_await
    async def request_limit_timeout_and_await(self, retry_num):
        await asyncio.sleep(self.request_limit_timeout(retry_num))

    # will sleep current async flow on time
    # based on retry number
    # and random value between self.min_await
    # and self.max_await
    def request_limit_timeout(self, retry_num) -> float:
        return random.uniform(
            min(0.1 * retry_num, self.min_await),
            min(0.8 * retry_num, self.max_await)
        )

    def print(self, *args, verbose_level: int = 1, **kwargs):
        if self.verbose >= verbose_level:
            print(*args, **kwargs)
