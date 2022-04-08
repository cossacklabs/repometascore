import asyncio
import json
import random
import requests
from typing import Dict, List


class MyGithubApi:
    auth_token: str
    auth_token_check: bool
    auth_token_max_retries: int

    def __init__(self, auth_token, auth_token_max_retries):
        self.initialiseVariables()
        self.auth_token = auth_token
        self.auth_token_max_retries = auth_token_max_retries

    def initialiseVariables(self):
        self.auth_token = str()
        self.auth_token_check = False
        self.auth_token_max_retries = int()

    def checkAuthToken(self) -> bool:
        print("Checking Auth Token")

        resp = requests.get(
            url='https://api.github.com',
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
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

    # get list of all contributors:
    # GitHub API expected data:
    # https://docs.github.com/en/rest/reference/repos#list-repository-contributors
    def getRepoContributors(self, repo_author, repo_name, anon=0) -> List:
        per_page = 100
        page_num = 1
        contributors_json = []
        while True:
            response = requests.get(
                url=f"https://api.github.com/repos/{repo_author}/{repo_name}/contributors"
                    f"?anon={anon}&per_page={per_page}&page={page_num}",
                headers={
                    'Authorization': self.auth_token,
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            response_json = json.loads(response.text)
            if len(response_json) == 0:
                break
            contributors_json += response_json
            page_num += 1
        return contributors_json

    # get contributors with stats (only top100)
    # expected data
    # https://docs.github.com/en/rest/reference/metrics#get-all-contributor-commit-activity
    def getRepoContributorsStats(self, repo_author, repo_name) -> List:
        response = requests.get(
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/stats/contributors",
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        contributors_json = json.loads(response.text)
        return contributors_json

    # get commit by author login
    # returns only one commit
    # expected data
    # https://docs.github.com/en/rest/reference/commits#list-commits
    async def getRepoCommitByAuthor(self, session, repo_author, repo_name, author, commit_num) -> List:
        commit_info = await self.getAsyncRequest(
            session,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/commits"
                f"?author={author}&per_page=1&page={commit_num}"
        )
        return commit_info

    # get user profile information
    # expected data
    # https://docs.github.com/en/rest/reference/users#get-a-user
    async def getUserProfileInfo(self, session, user_url) -> Dict:
        profile_info = await self.getAsyncRequest(
            session,
            url=user_url
        )
        return profile_info

    # function-helper
    # to make async request
    async def getAsyncRequest(self, session, url):
        exceeded_msg = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'
        while True:
            async with session.get(
                    url=url,
                    headers={
                        'Authorization': self.auth_token,
                        'Accept': 'application/vnd.github.v3+json'
                    }
            ) as resp:
                result = await resp.json()
            if type(result) is dict and result.get('message', '') == exceeded_msg:
                await asyncio.sleep(random.uniform(0, 0.8))
                continue
            break
        return result
