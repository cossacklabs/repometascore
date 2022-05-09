from typing import Dict

import aiohttp

from .DomainInfo import DomainInfo
from .MyGithubApi import GithubAPI
from .TwitterAPI import TwitterAPI


class RequestManager:
    githubAPI: GithubAPI
    twitterAPI: TwitterAPI
    domainInfo: DomainInfo
    __session: aiohttp.ClientSession

    def __init__(self, config: Dict = None, verbose: int = 0):
        if config is None:
            config = {}
        self.__session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))

        self.githubAPI = GithubAPI(session=self.__session, config=config, verbose=verbose)
        self.twitterAPI = TwitterAPI(session=self.__session, config=config, verbose=verbose)
        self.domainInfo = DomainInfo(session=self.__session, verbose=verbose)

        return

    async def initialize_tokens(self) -> bool:
        return await self.githubAPI.initialize_tokens() and await self.twitterAPI.initialize_tokens()

    async def close_session(self):
        if self.__session and not self.__session.closed:
            await self.__session.close()
        return
