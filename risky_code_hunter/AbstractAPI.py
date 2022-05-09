import asyncio
from abc import ABC, abstractmethod
import random
from typing import Dict

import aiohttp


class AbstractAPI(ABC):
    max_retries: int
    min_await: float
    max_await: float
    verbose: int
    __session: aiohttp.ClientSession
    _response_handlers: Dict
    _results_cache: Dict
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
        self._response_handlers = self.createResponseHandlers()
        self.handleUnpredictedResponse = self._response_handlers.pop(
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX, self.handleUnpredictedResponse
        )
        self._results_cache = {}

    @abstractmethod
    def createResponseHandlers(self) -> Dict:
        raise NotImplementedError("You should implement this!")

    @abstractmethod
    async def initializeTokens(self) -> bool:
        raise NotImplementedError("You should implement this!")

    async def handleUnpredictedResponse(self, url, params, resp, **kwargs) -> bool:
        raise Exception(
            f"Unpredicted response from server\n"
            f"Requested URL: {url}\n"
            f"Requested params: {params}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.text()}"
        )

    async def handleResponse200(self, **kwargs):
        return False

    def _saveToCache(self, key: Any, some_result: Any):
        self._results_cache[key] = some_result
        return

    async def _awaitFromCache(self, key: Any) -> Tuple[bool, Dict]:
        cached_result = self._getFromCache(key)
        if cached_result:
            event: asyncio.Event = cached_result.get('event')
            if event:
                await event.wait()
                return True, cached_result
        else:
            event = asyncio.Event()
            cached_result = {'event': event}
            self._saveToCache(key, cached_result)
        return False, cached_result

    def _getFromCache(self, key: Any) -> Any:
        return self._results_cache.get(key)

    def _removeFromCache(self, key):
        self._results_cache.pop(key, None)
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
                        self.handleUnpredictedResponse
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
                        await self.requestLimitTimeoutAndAwait(retry_num=retry)
                        continue
                    break
            except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientConnectorError,
                    aiohttp.client_exceptions.ServerDisconnectedError, aiohttp.client_exceptions.ClientOSError):
                await self.requestLimitTimeoutAndAwait(retry_num=retry)
                continue
        return resp

    # will sleep current async flow on time
    # based on retry number
    # and random value between self.min_await
    # and self.max_await
    async def requestLimitTimeoutAndAwait(self, retry_num):
        await asyncio.sleep(self.requestLimitTimeout(retry_num))

    # will sleep current async flow on time
    # based on retry number
    # and random value between self.min_await
    # and self.max_await
    def requestLimitTimeout(self, retry_num) -> float:
        return random.uniform(
            min(0.1 * retry_num, self.min_await),
            min(0.8 * retry_num, self.max_await)
        )

    def print(self, *args, verbose_level: int = 1, **kwargs):
        if self.verbose >= verbose_level:
            print(*args, **kwargs)
