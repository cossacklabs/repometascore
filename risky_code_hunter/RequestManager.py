from typing import Dict

import aiohttp

from .MyGithubApi import GithubApi
from .TwitterAPI import TwitterAPI


class RequestManager:
    githubApi: GithubApi
    twitterAPI: TwitterAPI
    __session: aiohttp.ClientSession

    def __init__(self, config: Dict):
        self.__session = aiohttp.ClientSession()

        auth_token = f"token {config['git_token']}"
        self.githubApi = GithubApi(
            auth_token,
            config.get('auth_token_max_retries', 5),
            config.get('github_min_await', 5.0),
            config.get('github_max_await', 15.0),
            self.__session
        )
        self.twitterAPI = TwitterAPI(self.__session)
        return

    async def closeSession(self):
        if self.__session and not self.__session.closed:
            await self.__session.close()
        return
