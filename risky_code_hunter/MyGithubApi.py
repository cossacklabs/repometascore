import asyncio
import random

import aiohttp
from typing import Dict, List


class GithubApi:
    auth_token: str
    auth_token_check: bool
    auth_token_max_retries: int
    min_await: float
    max_await: float
    __session: aiohttp.ClientSession

    def __init__(self, auth_token, auth_token_max_retries=5, min_await=5.0, max_await=15.0):
        self.auth_token = auth_token
        self.auth_token_check = False
        self.auth_token_max_retries = auth_token_max_retries
        self.min_await = min_await
        self.max_await = max_await
        self.__session = aiohttp.ClientSession()
        return

    async def checkAuthToken(self, session: aiohttp.ClientSession = None) -> bool:
        if not session:
            session = self.__session
        resp = await self.getAsyncRequest(
            url='https://api.github.com',
            session=session
        )
        # Currently, this piece of the code is redundant
        # As we successfully will get response only from
        # 200 OK status code
        if resp.status == 401:
            raise Exception(
                "Your github token is not valid. Github returned err validation code!\n"
                f"Status code: {resp.status}\n"
                f"Response:\n{await resp.json()}"
            )
        elif resp.status == 200:
            self.auth_token_check = True
            return True

        # some other error occured
        # currently redundant part of the code
        self.auth_token_check = False
        return False

    async def checkAuthTokenRetries(self, retries_count: int, session: aiohttp.ClientSession = None) -> bool:
        if not session:
            session = self.__session
        count = 0
        while not self.auth_token_check and count < retries_count:
            await self.checkAuthToken(session)
            count += 1
            if not self.auth_token_check:
                print(f"Retry one more time! Try count: {count}")
            print("Auth Token is valid!")
        return self.auth_token_check

    # get list of all contributors:
    # GitHub API expected data:
    # https://docs.github.com/en/rest/reference/repos#list-repository-contributors
    async def getRepoContributors(self, repo_author, repo_name, anon=0, session: aiohttp.ClientSession = None) -> List:
        if not session:
            session = self.__session
        per_page = 100
        page_num = 1
        contributors_json = []
        while True:
            response = await self.getAsyncRequest(
                url=f"https://api.github.com/repos/{repo_author}/{repo_name}/contributors"
                    f"?anon={anon}&per_page={per_page}&page={page_num}",
                session=session
            )
            response_json = await response.json()
            if len(response_json) == 0:
                break
            contributors_json += response_json
            page_num += 1
        return contributors_json

    # get contributors with stats (only top100)
    # expected data
    # https://docs.github.com/en/rest/reference/metrics#get-all-contributor-commit-activity
    async def getRepoContributorsStats(self, repo_author, repo_name, session: aiohttp.ClientSession = None) -> List:
        if not session:
            session = self.__session
        contributors_resp = await self.getAsyncRequest(
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/stats/contributors",
            session=session
        )
        contributors_json = await contributors_resp.json()
        return contributors_json

    # get commit by author login
    # returns only one commit
    # expected data
    # https://docs.github.com/en/rest/reference/commits#list-commits
    async def getRepoCommitByAuthor(self, repo_author, repo_name, author, commit_num, session: aiohttp.ClientSession = None) -> List:
        if not session:
            session = self.__session
        commit_info_resp = await self.getAsyncRequest(
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/commits"
                f"?author={author}&per_page=1&page={commit_num}",
            session=session
        )
        commit_info = await commit_info_resp.json()
        return commit_info

    # get user profile information
    # expected data
    # https://docs.github.com/en/rest/reference/users#get-a-user
    async def getUserProfileInfo(self, user_url, session: aiohttp.ClientSession = None) -> Dict:
        if not session:
            session = self.__session
        profile_info_resp = await self.getAsyncRequest(
            url=user_url,
            session=session
        )
        profile_info = await profile_info_resp.json()
        return profile_info

    # function-helper
    # to make async request
    async def getAsyncRequest(self, url, session: aiohttp.ClientSession = None) -> aiohttp.ClientResponse:
        if not session:
            session = self.__session
        EXCEEDED_MSG = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'
        retry = 0
        while True:
            retry += 1
            async with session.get(
                    url=url,
                    headers={
                        'Authorization': self.auth_token,
                        'Accept': 'application/vnd.github.v3+json'
                    }
            ) as resp:
                body = await resp.json()
            if resp.status == 404:
                raise Exception(
                    "Error, 404 status!\n"
                    f"Status code: {resp.status}\n"
                    f"Response:\n{await resp.json()}"
                )
            elif resp.status == 401:
                raise Exception(
                    "Your github token is not valid. Github returned err validation code!\n"
                    f"Status code: {resp.status}\n"
                    f"Response:\n{await resp.json()}"
                )
            elif resp.status == 202:
                await self.githubLimitTimeout(retry)
                continue
            elif resp.status == 403 and isinstance(body, dict) and body.get('message', str()) == EXCEEDED_MSG:
                await self.githubLimitTimeout(retry)
                continue
            elif resp.status != 200:
                raise Exception(
                    f"Non-predicted response from server\n"
                    f"Status code: {resp.status}\n"
                    f"Response:\n{await resp.json()}"
                )
            break
        return resp

    # will sleep current async flow on time
    # based on retry number
    # and random value between self.min_await
    # and self.max_await
    async def githubLimitTimeout(self, retry_num):
        await asyncio.sleep(
            random.uniform(
                min(0.1 * retry_num, self.min_await),
                min(0.8 * retry_num, self.max_await))
        )

    async def closeSession(self):
        if self.__session and not self.__session.closed:
            await self.__session.close()
        return
