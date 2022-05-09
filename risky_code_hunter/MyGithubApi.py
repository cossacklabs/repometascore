import asyncio
import datetime
import random
import time
from typing import Dict, List

import aiohttp

from .AbstractAPI import AbstractAPI
from .HTTP_METHOD import HTTP_METHOD


class BadToken(Exception):
    pass


class NoTokensLeft(Exception):
    pass


class TokenExceededRateLimit(Exception):
    pass


class PageNotFound(Exception):
    pass


class GithubAPI(AbstractAPI):
    auth_tokens: Dict[str, Dict]
    EXCEEDED_RATE_LIMIT_MSG = 'API rate limit exceeded for user ID'
    EXCEEDED_SECONDARY_MSG = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'
    auth_tokens_checked: bool
    __print_timestamps: Dict

    def __init__(self, session: aiohttp.ClientSession = None, config: Dict = None, verbose: int = 0):
        super().__init__(session=session, config=config, verbose=verbose)
        self.auth_tokens = {}
        git_tokens = config.get('git_tokens', [])
        for git_token in git_tokens:
            self.auth_tokens[f'token {git_token}'] = {"isGood": False, "reset": -1, "isFull": False, "event": None}
        self.auth_tokens_checked = False
        self.__print_timestamps = {}
        return

    async def initialize_tokens(self) -> bool:
        return await self.check_auth_tokens()

    def create_response_handlers(self) -> Dict:
        result = {
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX: self.handle_unpredicted_response,
            200: self.handle_response_200,
            202: self.handle_response_202,
            401: self.handle_response_401,
            403: self.handle_response_403,
            404: self.handle_response_404,
            429: self.handle_response_429,
            502: self.handle_response_502,
            503: self.handle_response_503
        }
        return result

    async def handle_response_202(self, **kwargs):
        return True

    async def handle_response_401(self, resp, **kwargs):
        raise BadToken(
            "Your GitHub token is not valid. Github returned err validation code!\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.json()}"
        )

    async def handle_response_403(self, resp, **kwargs):
        resp_json = await resp.json()
        if isinstance(resp_json, dict):
            if resp_json.get('message', str()) == self.EXCEEDED_SECONDARY_MSG:
                return True
            elif self.EXCEEDED_RATE_LIMIT_MSG in resp_json.get('message', str()):
                raise TokenExceededRateLimit(resp_json.get('message', str()))
        await self.handle_unpredicted_response(resp=resp, **kwargs)
        return False

    async def handle_response_404(self, url, resp, **kwargs):
        raise PageNotFound(
            "Error, 404 status!\n"
            "Maybe your GitHub repository url is wrong!\n"
            f"Cannot find info on such url: {url}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.json()}"
        )

    async def handle_response_429(self, resp, **kwargs):
        resp_json = await resp.json()
        raise TokenExceededRateLimit(f"{resp_json}")

    async def handle_response_502(self, **kwargs):
        return True

    async def handle_response_503(self, **kwargs):
        return True

    async def check_auth_token(self, token) -> bool:
        if token in self.auth_tokens:
            event: asyncio.Event = self.auth_tokens[token]['event']
            if event:
                await event.wait()
                return token in self.auth_tokens
            if self.auth_tokens[token]['isFull'] and self.auth_tokens[token]['reset'] > int(time.time()):
                return True
        else:
            self.auth_tokens[token] = {"isGood": False, "reset": -1, "isFull": False, "event": None}

        event = asyncio.Event()
        self.auth_tokens[token]["event"] = event
        try:
            resp = await self.request(
                method=HTTP_METHOD.GET,
                url='https://api.github.com/rate_limit',
                headers={
                    'Authorization': token,
                },
                auth_check=True
            )
        except BadToken:
            self.auth_tokens.pop(token, None)
            event.set()
            return False
        except Exception as exception:
            event.set()
            raise exception

        if resp.status == 200:
            resp_json = await resp.json()
            self.auth_tokens[token]['isGood'] = True
            self.auth_tokens[token]['reset'] = resp_json['rate']['reset']
            self.auth_tokens[token]['isFull'] = resp_json['rate']['remaining'] <= 0
            self.auth_tokens[token]['event'] = None
            event.set()
            return True
        else:
            # some other error occurred
            # currently redundant part of the code
            self.auth_tokens.pop(token, None)
            event.set()
            return False

    async def check_auth_tokens(self, ) -> bool:
        if self.auth_tokens_checked:
            return True
        self.print("Checking Auth tokens!")
        index = 1
        for token in self.auth_tokens.copy():
            if self.auth_tokens[token]['isGood']:
                continue
            if not await self.check_auth_token(token):
                self.print(f"Token #{index} is not valid!")
            index += 1
        if len(self.auth_tokens) == 0:
            raise BadToken("All your github tokens are not valid!")
        self.print("Auth Tokens are valid!")
        self.auth_tokens_checked = True
        return True

    # get list of all contributors:
    # GitHub API expected data:
    # https://docs.github.com/en/rest/repos/repos#list-repository-contributors
    async def get_repo_contributors(self, repo_author, repo_name, anon=0) -> List:
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
    async def get_repo_contributors_stats(self, repo_author, repo_name) -> List:
        contributors_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/stats/contributors",
        )
        contributors_json = await contributors_resp.json()
        return contributors_json

    # get commit by author login
    # returns only one commit
    # expected data
    # https://docs.github.com/en/rest/commits/commits#list-commits
    async def get_repo_commit_by_author(self, repo_author, repo_name, author, commit_num, per_page) -> List:
        params = {
            'author': author,
            'per_page': per_page,
            'page': commit_num
        }
        commit_info_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=f"https://api.github.com/repos/{repo_author}/{repo_name}/commits",
            params=params,
        )
        commit_info = await commit_info_resp.json()
        return commit_info

    # get user profile information
    # expected data
    # https://docs.github.com/en/rest/users/users#get-a-user
    async def get_user_profile_info(self, user_url) -> Dict:
        try:
            profile_info_resp = await self.request(
                method=HTTP_METHOD.GET,
                url=user_url,
            )
            profile_info = await profile_info_resp.json()
        except PageNotFound:
            return {}
        return profile_info

    # get companies (organizations) list of specific user
    # get companies (organizations) list of specific user
    # expected data
    # https://docs.github.com/en/rest/orgs/orgs#list-organizations-for-a-user
    async def get_user_companies_info(self, user_url) -> List[Dict]:
        companies_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=user_url + "/orgs",
        )
        companies = await companies_resp.json()
        tasks = []
        for company in companies:
            tasks.append(asyncio.ensure_future(self.get_company_info(company['url'])))
        companies_info = list(await asyncio.gather(*tasks))
        return companies_info

    # get company (organization) information
    # expected data
    # https://docs.github.com/en/rest/orgs/orgs#get-an-organization
    async def get_company_info(self, company_url) -> Dict:
        is_result_present, cached_result = await self._await_from_cache(company_url)
        if is_result_present:
            return cached_result['result']
        company_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=company_url,
        )
        company_info = await company_resp.json()
        cached_result['result'] = company_info
        event = cached_result.pop('event', None)
        if event:
            event.set()
        return company_info

    async def get_random_token(self) -> str:
        remaining_tokens = []
        is_greater_than_2mins = True
        time_of_token_reset = 999999999999999999999999999999999999999999
        for token, token_info in self.auth_tokens.copy().items():
            if token_info['isFull']:
                token_reset = token_info.get('reset', 0)
                if token_reset >= int(time.time()):
                    is_greater_than_2mins = is_greater_than_2mins and (int(time.time()) - token_reset) > 12000
                    time_of_token_reset = min(time_of_token_reset, token_reset)
                else:
                    self.auth_tokens[token]['isFull'] = False
                    remaining_tokens.append(token)
            else:
                remaining_tokens.append(token)
        if len(remaining_tokens) == 0:
            if is_greater_than_2mins:
                print("Timeout is too big")
                raise NoTokensLeft("Every token is on long cooldown right now!")
            sleep_duration = max(time_of_token_reset - time.time(), 0.5) + 2
            self.print(
                f"Let's wait till {datetime.datetime.fromtimestamp(time_of_token_reset)} and then back to work!",
                f"Requests to GitHub will not be done in the next {datetime.timedelta(seconds=sleep_duration)} seconds",
                signature="Let's wait till",
                time_to_wait=5.0
            )
            await asyncio.sleep(sleep_duration)
            await self.request_limit_timeout_and_await(5)
            self.print("GitHub requests are running again!", signature="Running Again", time_to_wait=5.0)
            return await self.get_random_token()
        return random.choice(remaining_tokens)

    async def request(self, method, url, params=None, data=None, headers=None,
                      auth_check=False) -> aiohttp.ClientResponse:
        if auth_check:
            result = await super().request(method=method, url=url, params=params, data=data, headers=headers)
            return result
        if not isinstance(headers, Dict):
            headers = {}
        headers['Accept'] = 'application/vnd.github.v3+json'
        while True:
            headers['Authorization'] = await self.get_random_token()
            try:
                result = await super().request(method=method, url=url, params=params, data=data, headers=headers)
                return result
            except TokenExceededRateLimit:
                await self.check_auth_token(headers['Authorization'])
                continue

    def print(self, *args, signature=None, time_to_wait: float = 1, **kwargs):
        if isinstance(signature, str):
            if signature in self.__print_timestamps:
                if (time.time() - self.__print_timestamps[signature]['last_print']) < \
                        self.__print_timestamps[signature]['time_to_wait']:
                    return
            else:
                self.__print_timestamps[signature] = {}
            self.__print_timestamps[signature]['last_print'] = time.time()
            self.__print_timestamps[signature]['time_to_wait'] = time_to_wait
        super().print(*args, **kwargs)
        return
