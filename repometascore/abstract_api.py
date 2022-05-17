import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict

import aiohttp

from .cache import Cache


class AbstractAPI(ABC):
    max_retries: int
    min_await: float
    max_await: float
    verbose: int
    __session: aiohttp.ClientSession
    _response_handlers: Dict
    UNPREDICTED_RESPONSE_HANDLER_INDEX = -1
    _cache: Cache

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
        self._cache = Cache()

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
                    aiohttp.client_exceptions.ServerDisconnectedError, aiohttp.client_exceptions.ClientOSError) \
                    as exception:
                self.print(f"AbstractAPI.request({method}, {url}, {params}, {data}, {headers})."
                           f" Raised an exception: \n{exception}", verbose_level=4)
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
