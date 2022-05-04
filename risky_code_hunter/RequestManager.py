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

    def __init__(self, config: Dict = None):
        if config is None:
            config = {}
        self.__session = aiohttp.ClientSession()

        self.githubAPI = GithubAPI(session=self.__session, config=config)
        self.twitterAPI = TwitterAPI(session=self.__session, config=config)
        self.domainInfo = DomainInfo()

        return

    async def initializeTokens(self) -> bool:
        return await self.githubAPI.initializeTokens() and await self.twitterAPI.initializeTokens()

    async def closeSession(self):
        if self.__session and not self.__session.closed:
            await self.__session.close()
        return
