from typing import Dict, List

import aiohttp

from .AbstractAPI import AbstractAPI
from .HTTP_METHOD import HTTP_METHOD


class GithubAPI(AbstractAPI):
    auth_token: str
    auth_token_check: bool
    EXCEEDED_MSG = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'

    def __init__(self, session: aiohttp.ClientSession = None, config: Dict = None, verbose: int = 0):
        super().__init__(session=session, config=config, verbose=verbose)
        self.auth_token = f"token {config.get('git_token', 'ghp_token')}"
        self.auth_token_check = False
        return

    async def initializeTokens(self) -> bool:
        return await self.checkAuthTokenRetries(self.max_retries)

    def createResponseHandlers(self) -> Dict:
        result = {
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX: self.handleUnpredictedResponse,
            200: self.handleResponse200,
            401: self.handleResponse401,
            403: self.handleResponse403,
            404: self.handleResponse404
        }
        return result

    async def handleResponse202(self, **kwargs):
        return True

    async def handleResponse401(self, resp, **kwargs):
        raise Exception(
            "Your github token is not valid. Github returned err validation code!\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.json()}"
        )

    async def handleResponse403(self, resp, **kwargs):
        resp_json = await resp.json()
        if isinstance(resp_json, dict) and resp_json.get('message', str()) == self.EXCEEDED_MSG:
            return True
        await self.handleUnpredictedResponse(resp=resp, **kwargs)
        return False

    async def handleResponse404(self, url, resp, **kwargs):
        raise Exception(
            "Error, 404 status!\n"
            "Maybe your github repository url is wrong!\n"
            f"Cannot find info on such url: {url}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.json()}"
        )

    async def checkAuthToken(self) -> bool:
        resp = await self.request(
            method=HTTP_METHOD.GET,
            url='https://api.github.com',
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
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

        # some other error occurred
        # currently redundant part of the code
        self.auth_token_check = False
        return False

    async def checkAuthTokenRetries(self, retries_count: int = 0) -> bool:
        count = 0
        if retries_count <= 0:
            retries_count = self.max_retries
        while not self.auth_token_check and count < retries_count:
            self.print("Checking Auth token!")
            await self.checkAuthToken()
            count += 1
            if not self.auth_token_check:
                self.print(f"Retry one more time! Try count: {count}")
            self.print("Auth Token is valid!")
        return self.auth_token_check

    # get list of all contributors:
    # GitHub API expected data:
    # https://docs.github.com/en/rest/repos/repos#list-repository-contributors
    async def getRepoContributors(self, repo_author, repo_name, anon=0) -> List:
        per_page = 100
        page_num = 1
        contributors_json = []
        while True:
            params = {
                'anon': anon,
                'per_page': per_page,
                'page': page_num
            }
            response = await self.request(
                method=HTTP_METHOD.GET,
                url=f"https://api.github.com/repos/{repo_author}/{repo_name}/contributors",
                params=params,
                headers={
                    'Authorization': self.auth_token,
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            response_json = await response.json()
            if len(response_json) == 0:
                break
            contributors_json += response_json
            page_num += 1
            if len(response_json) < per_page:
                break
        return contributors_json

    # get contributors with stats (only top100)
    # expected data
    # https://docs.github.com/en/rest/metrics/statistics#get-all-contributor-commit-activity
    async def getRepoContributorsStats(self, repo_author, repo_name) -> List:
        contributors_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/stats/contributors",
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        contributors_json = await contributors_resp.json()
        return contributors_json

    # get commit by author login
    # returns only one commit
    # expected data
    # https://docs.github.com/en/rest/commits/commits#list-commits
    async def getRepoCommitByAuthor(self, repo_author, repo_name, author, commit_num, per_page) -> List:
        params = {
            'author': author,
            'per_page': per_page,
            'page': commit_num
        }
        commit_info_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/commits",
            params=params,
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        commit_info = await commit_info_resp.json()
        return commit_info

    # get user profile information
    # expected data
    # https://docs.github.com/en/rest/users/users#get-a-user
    async def getUserProfileInfo(self, user_url) -> Dict:
        profile_info_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=user_url,
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        profile_info = await profile_info_resp.json()
        return profile_info
