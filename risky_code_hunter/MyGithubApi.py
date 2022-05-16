import asyncio
import datetime
import os
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
    EXCEEDED_RATE_LIMIT_MSG = 'API rate limit exceeded for user ID'
    EXCEEDED_SECONDARY_MSG = 'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'
    auth_tokens: Dict[str, Dict]
    auth_tokens_checked: bool
    check_auth_token_lock: asyncio.Lock
    __print_timestamps: Dict
    ALLOWED_TIME_TO_WAIT_DEFAULT: float = 12000.0
    allowed_time_to_wait: float

    def __init__(self, session: aiohttp.ClientSession = None, config: Dict = None, verbose: int = 0):
        super().__init__(session=session, config=config, verbose=verbose)
        self.auth_tokens = {}
        git_tokens = config.get('git_tokens', [])
        for git_token in git_tokens:
            self.auth_tokens[f'token {git_token}'] = \
                {"is_good": False, "reset_time": -1, "is_full": False, "event": None}
        self.auth_tokens_checked = False
        self.check_auth_token_lock = asyncio.Lock()
        self.__print_timestamps = {}
        self.allowed_time_to_wait = int(os.environ.get('ALLOWED_TIME_TO_WAIT', self.ALLOWED_TIME_TO_WAIT_DEFAULT))
        return

    async def initialize_tokens(self) -> bool:
        return await self.check_auth_tokens()

    def create_response_handlers(self) -> Dict:
        result = {
            self.UNPREDICTED_RESPONSE_HANDLER_INDEX: self.handle_unpredicted_response,
            # correct OK response
            200: self.handle_response_200,
            # occurred during a high load of GitHub API and
            # returned the correct result in case of repeating the same request
            202: self.handle_response_202,
            # returned only in cases of invalid GitHub Token
            401: self.handle_response_401,
            # returned in cases of exceeding secondary or primary token rate limits
            403: self.handle_response_403,
            # occurred in case of incorrect URL or deleted GitHub page
            404: self.handle_response_404,
            # occurred rarely when exceeding the primary token rate limit
            429: self.handle_response_429,
            # occurred during a high load of GitHub API and
            # returned the correct result in case of repeating the same request
            500: self.handle_response_500,
            # occurred during a high load of GitHub API and
            # returned the correct result in case of repeating the same request
            502: self.handle_response_502,
            # occurred during a high load of GitHub API and
            # returned the correct result in case of repeating the same request
            503: self.handle_response_503
        }
        return result

    # Can occur during a high load of GitHub API and
    # returned the correct result in case of repeating the same request
    # also can occur in some weird repositories as these:
    # https://github.com/weiss/nsca-ng/graphs/contributors
    # https://github.com/crazy-canux/icinga2.vim/graphs/contributors
    # https://github.com/monitoring-plugins/monitoring-plugin-perl/graphs/contributors
    # We can see how web browser tries to retry `stats` request infinitely.
    # So if we get from GitHub 5 times of 202 response about some repository
    # we will assume, that `stats` response from this repository is empty.
    async def handle_response_202(self, resp: aiohttp.ClientResponse, url: str, **kwargs):
        retry_202_counter: int = 0
        try:
            is_result_present, retry_202_lock = await self._cache.get_and_await(
                f"{url} status code 202 lock", create_new_awaitable=True
            )
        except asyncio.TimeoutError:
            is_result_present = False
        if is_result_present:
            async with retry_202_lock:
                is_result_present, retry_202_counter = await self._cache.get_and_await(
                    f"{url} status code 202 counter", create_new_awaitable=True
                )
                if retry_202_counter >= 5:
                    return False
                else:
                    await self._cache.set(f"{url} status code 202 counter", retry_202_counter + 1)
                    return True
        else:
            await self._cache.set(f"{url} status code 202 lock", asyncio.Lock())
            await self._cache.set(f"{url} status code 202 counter", retry_202_counter + 1)
            return True

    # returned only in cases of invalid GitHub Token
    async def handle_response_401(self, resp, **kwargs):
        raise BadToken(
            "Your GitHub token is not valid. Github returned err validation code!\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.json()}"
        )

    # returned in cases of exceeding secondary or primary token rate limits
    async def handle_response_403(self, resp, **kwargs):
        resp_json = await resp.json()
        if isinstance(resp_json, dict):
            if resp_json.get('message', "") == self.EXCEEDED_SECONDARY_MSG:
                return True
            elif self.EXCEEDED_RATE_LIMIT_MSG in resp_json.get('message', ""):
                raise TokenExceededRateLimit(resp_json.get('message', ""))
        await self.handle_unpredicted_response(resp=resp, **kwargs)
        return False

    # occurred in case of incorrect URL or deleted GitHub page
    async def handle_response_404(self, url, resp, **kwargs):
        raise PageNotFound(
            "Error, 404 status!\n"
            "Maybe your GitHub repository url is wrong!\n"
            f"Cannot find info on such url: {url}\n"
            f"Status code: {resp.status}\n"
            f"Response:\n{await resp.json()}"
        )

    # occurred rarely when exceeding the primary token rate limit
    async def handle_response_429(self, resp, **kwargs):
        resp_json = await resp.json()
        raise TokenExceededRateLimit(f"{resp_json}")

    # occurred during a high load of GitHub API and
    # returned the correct result in case of repeating the same request
    async def handle_response_500(self, **kwargs):
        return True

    # occurred during a high load of GitHub API and
    # returned the correct result in case of repeating the same request
    async def handle_response_502(self, **kwargs):
        return True

    # occurred during a high load of GitHub API and
    # returned the correct result in case of repeating the same request
    async def handle_response_503(self, **kwargs):
        return True

    # Enter Lock
    # if token exist in tokens_dict -> if token is full and its reset time is in future -> return True
    #   -> get event from token dict -> if event is exists -> somebody is already requesting
    #                                   -> if event is not exist -> create event and add it to token dict
    # Exit Lock
    # if somebody is already requesting -> wait to event to be set and return result
    # else -> Usual logic
    async def check_auth_token(self, token) -> bool:
        is_already_requesting: bool
        async with self.check_auth_token_lock:
            is_already_requesting = False
            if token in self.auth_tokens:
                if self.auth_tokens[token]['is_full'] and self.auth_tokens[token]['reset_time'] > int(time.time()):
                    return True
                event: asyncio.Event = self.auth_tokens[token].get('event')
                if isinstance(event, asyncio.Event):
                    is_already_requesting = True
            else:
                self.auth_tokens[token] = {"isGood": False, "reset": -1, "isFull": False, "event": None}
            if not is_already_requesting:
                event = asyncio.Event()
                self.auth_tokens[token]["event"] = event
        if is_already_requesting:
            await event.wait()
            return token in self.auth_tokens
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
            self.auth_tokens[token]['event'] = None
            event.set()
            raise exception

        if resp.status == 200:
            resp_json = await resp.json()
            self.auth_tokens[token]['is_good'] = True
            self.auth_tokens[token]['reset_time'] = resp_json['rate']['reset']
            self.auth_tokens[token]['is_full'] = resp_json['rate']['remaining'] <= 0
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
        for index, token in enumerate(self.auth_tokens.copy()):
            if self.auth_tokens[token]['is_good']:
                continue
            if not await self.check_auth_token(token):
                self.print(f"Token #{index + 1} is not valid!")
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
            tasks.append(self.get_company_info(company['url']))
        companies_info = list(await asyncio.gather(*tasks))
        return companies_info

    # get company (organization) information
    # expected data
    # https://docs.github.com/en/rest/orgs/orgs#get-an-organization
    async def get_company_info(self, company_url) -> Dict:
        try:
            # set timeout to ALLOWED_TIME_TO_WAIT + 120
            # as because if there is token expiration - we need to await some time
            # before getting a new response after token reset
            # by default we are waiting 200 minutes, as it is a little bit
            # of overkill, and can be considered as infinity by that time
            # should be set to much lower value in future updates
            is_result_present, cached_result = await self._cache.get_and_await(
                company_url, create_new_awaitable=True, timeout=self.allowed_time_to_wait
            )
        except asyncio.TimeoutError:
            is_result_present = False
        if is_result_present:
            return cached_result
        company_resp = await self.request(
            method=HTTP_METHOD.GET,
            url=company_url,
        )
        company_info = await company_resp.json()
        await self._cache.set(company_url, company_info)
        return company_info

    async def get_random_token(self) -> str:
        remaining_tokens = []
        is_greater_than_allowed_time = True
        time_of_token_reset = 2**64
        for token, token_info in self.auth_tokens.copy().items():
            if token_info['is_full']:
                token_reset_time = token_info.get('reset_time', 0)
                if token_reset_time >= int(time.time()):
                    is_greater_than_allowed_time = \
                        is_greater_than_allowed_time and (int(time.time()) - token_reset_time) > \
                        self.allowed_time_to_wait
                    time_of_token_reset = min(time_of_token_reset, token_reset_time)
                else:
                    self.auth_tokens[token]['is_full'] = False
                    remaining_tokens.append(token)
            else:
                remaining_tokens.append(token)
        if len(remaining_tokens) == 0:
            if is_greater_than_allowed_time:
                print("Timeout is too big")
                raise NoTokensLeft("Every token is on long cooldown right now!")
            # Let's wait an additional 1.1 seconds as GitHub sometimes would not allow
            # To run at the same time with token reset
            sleep_duration = max(time_of_token_reset - int(time.time()), 1.0) + 1.1
            # We are using 5 seconds to wait between prints, as it seems like optimal value between such prints
            self.print(
                f"Let's wait till {datetime.datetime.fromtimestamp(time_of_token_reset)} and then back to work!",
                f"Requests to GitHub will not be done in the next {datetime.timedelta(seconds=sleep_duration)} seconds",
                signature="Let's wait till",
                time_to_wait=5.0
            )
            await asyncio.sleep(sleep_duration)
            # Randomization in the next method will allow us to make requests at slightly different time.
            await self.request_limit_timeout_and_await(5)
            # We are using 5 seconds to wait between prints, as it seems like optimal value between such prints
            self.print("GitHub's requests are running again!", signature="Running Again", time_to_wait=5.0)
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

    def print(self, *args, signature=None, time_to_wait: float = 1.0, **kwargs):
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
