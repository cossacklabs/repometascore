import asyncio
import random
import time

import aiohttp
import requests
from typing import Dict, List


class MyGithubApi:
    auth_token: str
    auth_token_check: bool
    auth_token_max_retries: int
    min_await: float
    max_await: float

    def __init__(self, auth_token, auth_token_max_retries, min_await, max_await):
        self.initialiseVariables()
        self.auth_token = auth_token
        self.auth_token_max_retries = auth_token_max_retries
        self.min_await = min_await
        self.max_await = max_await

    def initialiseVariables(self):
        self.auth_token = str()
        self.auth_token_check = False
        self.auth_token_max_retries = int()
        self.min_await = int()
        self.max_await = int()

    async def checkAuthTokenAsync(self, session: aiohttp.ClientSession) -> bool:
        print("Checking Auth Token Async")

        resp = await self.getAsyncRequest(
            session=session,
            url='https://api.github.com'
        )
        if resp.status == 401:
            print("Token is not valid!")
            raise Exception("Your github token is not valid. Github returned err validation code!")
        elif resp.status == 200:
            print("Auth Token is valid!")
            self.auth_token_check = True
            return True

        print("Some error occurred while requesting github api")
        self.auth_token_check = False
        return False

    def checkAuthToken(self) -> bool:
        print("Checking Auth Token")

        resp = self.getSyncRequest(
            url='https://api.github.com',
        )
        if resp.status_code == 401:
            print("Token is not valid!")
            raise Exception("Your github token is not valid. Github returned err validation code!")
        elif resp.status_code == 200:
            print("Auth Token is valid!")
            self.auth_token_check = True
            return True

        print("Some error occurred while requesting github api")
        self.auth_token_check = False
        return False

    def checkAuthTokenRetries(self, retries_count) -> bool:
        count = 0
        while not self.auth_token_check and count < retries_count:
            self.checkAuthToken()
            count += 1
            if not self.auth_token_check:
                print(f"Retry one more time! Try count: {count}")
        return self.auth_token_check

    async def checkAuthTokenRetriesAsync(self, session: aiohttp.ClientSession, retries_count: int) -> bool:
        count = 0
        while not self.auth_token_check and count < retries_count:
            await self.checkAuthTokenAsync(session)
            count += 1
            if not self.auth_token_check:
                print(f"Retry one more time! Try count: {count}")
        return self.auth_token_check

    # get list of all contributors:
    # GitHub API expected data:
    # https://docs.github.com/en/rest/reference/repos#list-repository-contributors
    async def getRepoContributors(self, session, repo_author, repo_name, anon=0) -> List:
        per_page = 100
        page_num = 1
        contributors_json = []
        while True:
            response = await self.getAsyncRequest(
                session=session,
                url=f"https://api.github.com/repos/{repo_author}/{repo_name}/contributors"
                    f"?anon={anon}&per_page={per_page}&page={page_num}"
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
    async def getRepoContributorsStats(self, session, repo_author, repo_name) -> List:
        contributors_resp = await self.getAsyncRequest(
            session,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/stats/contributors"
        )
        contributors_json = await contributors_resp.json()
        return contributors_json

    # get commit by author login
    # returns only one commit
    # expected data
    # https://docs.github.com/en/rest/reference/commits#list-commits
    async def getRepoCommitByAuthor(self, session, repo_author, repo_name, author, commit_num) -> List:
        commit_info_resp = await self.getAsyncRequest(
            session,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/commits"
                f"?author={author}&per_page=1&page={commit_num}"
        )
        commit_info = await commit_info_resp.json()
        return commit_info

    # get user profile information
    # expected data
    # https://docs.github.com/en/rest/reference/users#get-a-user
    async def getUserProfileInfo(self, session, user_url) -> Dict:
        profile_info_resp = await self.getAsyncRequest(
            session,
            url=user_url
        )
        profile_info = await profile_info_resp.json()
        return profile_info

    # function-helper
    # to make async request
    async def getAsyncRequest(self, session: aiohttp.ClientSession, url) -> aiohttp.ClientResponse:
        exceeded_msg = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'
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
                result = resp
                if resp.status == 404:
                    raise Exception(
                        "Could not found this url: "
                        f"{url}"
                    )
                elif resp.status == 401:
                    raise Exception(
                        "Your github token is not valid. Github returned err validation code!"
                        f"Status: {resp.status}"
                    )
                elif resp.status == 202:
                    await self.githubLimitTimeout(retry)
                    continue
                elif resp.status == 403 and isinstance(body, dict) and body.get('message', str()) == exceeded_msg:
                    await self.githubLimitTimeout(retry)
                    continue
                elif resp.status != 200:
                    raise Exception(
                        f"Non-predicted response from server\n"
                        f"Status code: {resp.status}\n"
                        f"Response:\n{await result.json()}"
                    )
            break
        return result

    # function-helper
    # to make async request
    def getSyncRequest(self, url) -> requests.Response:
        exceeded_msg = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'
        while True:
            resp = requests.get(
                url=url,
                headers={
                    'Authorization': self.auth_token,
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            result = resp
            body = resp.json()
            if resp.status_code == 404:
                raise Exception(
                    "Could not found this repo: "
                    f"{url}"
                )
            elif resp.status_code == 401:
                raise Exception(
                    "Your github token is not valid. Github returned err validation code!"
                    f"Status: {resp.status_code}"
                )
            elif resp.status_code == 202:
                time.sleep(random.uniform(0, 0.8))
                continue
            elif resp.status_code == 403 and isinstance(body, dict) and body.get('message', str()) == exceeded_msg:
                time.sleep(random.uniform(0, 0.8))
                continue
            elif resp.status_code != 200:
                raise Exception(
                    f"Non-predicted response from server\n"
                    f"Status code: {resp.status_code}\n"
                    f"Response:\n{result}"
                )
            break
        return result

    async def githubLimitTimeout(self, retry_num):
        await asyncio.sleep(
            random.uniform(
                min(0.1 * retry_num, self.min_await),
                min(0.8 * retry_num, self.max_await))
        )
