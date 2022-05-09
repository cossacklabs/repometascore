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

    async def request(self, method, url, params=None, data=None, headers=None) -> aiohttp.ClientResponse:
        retry = 0
        while True:
            retry += 1
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
                    await self.requestLimitTimeout(retry_num=retry)
                    continue
                break
        return resp

    # will sleep current async flow on time
    # based on retry number
    # and random value between self.min_await
    # and self.max_await
    async def requestLimitTimeout(self, retry_num):
        await asyncio.sleep(
            random.uniform(
                min(0.1 * retry_num, self.min_await),
                min(0.8 * retry_num, self.max_await))
        )

    def print(self, *args, verbose_level: int = 1, **kwargs):
        if self.verbose >= verbose_level:
            print(*args, **kwargs)
