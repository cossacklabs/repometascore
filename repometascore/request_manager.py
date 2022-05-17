import os
from typing import Dict

import aiohttp

from .domain_info import DomainInfo
from .github_api import GithubAPI
from .twitter_api import TwitterAPI


class RequestManager:
    github_api: GithubAPI
    twitter_api: TwitterAPI
    domain_info: DomainInfo
    __session: aiohttp.ClientSession

    def __init__(self, config: Dict = None, verbose: int = 0):
        if config is None:
            config = {}

        HTTP_REQUEST_TIMEOUT = int(os.environ.get('HTTP_REQUEST_TIMEOUT', 20))
        self.__session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT))

        self.github_api = GithubAPI(session=self.__session, config=config, verbose=verbose)
        self.twitter_api = TwitterAPI(session=self.__session, config=config, verbose=verbose)
        self.domain_info = DomainInfo(session=self.__session, verbose=verbose)

        return

    async def initialize_tokens(self) -> bool:
        return await self.github_api.initialize_tokens() and await self.twitter_api.initialize_tokens()

    async def close_session(self):
        if self.__session and not self.__session.closed:
            await self.__session.close()
        return
