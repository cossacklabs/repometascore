import json
import random

import requests
from typing import List, Dict

from RiskyRepo import RiskyRepo
from Contributor import Contributor

import aiohttp
import asyncio

from TriggeredRule import TriggeredRule

russian_mail_domains = [
    "rambler.ru"
    "lenta.ru",
    "autorambler.ru",
    "myrambler.ru",
    "ro.ru",
    "rambler.ua",
    "mail.ua",
    "mail.ru",
    "internet.ru",
    "bk.ru",
    "inbox.ru",
    "list.ru",
    "yandex.ru",
    "ya.ru"
]


def get_repo_name(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_name = repo_name[repo_name.find('/') + 1:]
    repo_author = repo_name[:repo_name.find('/')]
    repo_name = repo_name[repo_name.find('/') + 1:]
    if repo_name.find('/') > 0:
        repo_name = repo_name[:repo_name.find('/')]

    return repo_name


def get_repo_author(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_name = repo_name[repo_name.find('/') + 1:]
    repo_author = repo_name[:repo_name.find('/')]
    return repo_author


class TCH:
    repo_author: str = str()
    repo_name: str = str()
    auth_token: str = str()
    auth_token_check: bool = False
    config: Dict

    event = None

    def __init__(self, repo_url, config):
        self.repo_author = get_repo_author(repo_url)
        self.repo_name = get_repo_name(repo_url)
        with open(config) as conf_file:
            self.config = json.load(conf_file)
        self.auth_token = f"token {self.config['git_token']}"

    def checkAuthToken(self):
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

        print("Some error occured while requesting github api")
        self.auth_token_check = False
        return False

    def checkAuthTokenRetries(self, retries_count):
        retries_count = 0
        while not self.auth_token_check and retries_count < 5:
            self.checkAuthToken()
            retries_count += 1
            if not self.auth_token_check:
                print(f"Retry one more time! Try count: {retries_count}")
        return self.auth_token_check

    def scanRepo(self):
        if not self.checkAuthTokenRetries(5) and not self.auth_token_check:
            return False, None

        repo_result = RiskyRepo(
            self.repo_author,
            self.repo_name,
            self.config
        )

        contributors: List[Contributor] = []
        contributors = self.getContributorsList()
        for contributor in contributors:
            if not isinstance(contributor.url, str) or not contributor.url:
                continue
            contributor = self.getContributorInfo(contributor)
            contributor = self.checkContributor(contributor)
            repo_result.addContributor(contributor)

        return True, repo_result

    async def scanRepoAsync(self):
        if not self.checkAuthTokenRetries(5) and not self.auth_token_check:
            return False, None

        if not self.auth_token_check:
            return False, None

        repo_result = RiskyRepo(
            self.repo_author,
            self.repo_name,
            self.config
        )

        contributors: List[Contributor] = []
        contributors = self.getContributorsList()
        contributors = await self.getContributorsInfoAsync(contributors)

        for contributor in contributors:
            if not isinstance(contributor.url, str) or not contributor.url:
                continue
            contributor = self.checkContributor(contributor)
            repo_result.addContributor(contributor)

        return True, repo_result

    def getContributorsList(self):
        contributors_info = []
        login_contributor = {}

        # get all list of contributors:
        per_page = 100
        page_num = 1
        while True:
            response = requests.get(
                url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/contributors"
                    f"?anon=0&per_page={per_page}&page={page_num}",
                headers={
                    'Authorization': self.auth_token,
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            contributors_json = json.loads(response.text)
            if len(contributors_json) == 0:
                break

            for contributor in contributors_json:
                contributor_obj = Contributor(contributor)
                contributors_info.append(contributor_obj)
                if contributor['type'] != "Anonymous":
                    login_contributor[contributor_obj.login] = contributor_obj

            page_num += 1

        # get contributors with stats (only top100)
        response = requests.get(
            url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/stats/contributors",
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        contributors_json = json.loads(response.text)

        for contributor in contributors_json:
            if login_contributor.get(contributor['author']['login']):
                contributor_obj = login_contributor.get(contributor['author']['login'])
                contributor_obj.addValue(contributor['author'])
                contributor_obj.commits = 0
            else:
                contributor_obj = Contributor(contributor['author'])
                login_contributor[contributor_obj.login] = contributor_obj
                contributors_info.append(contributor_obj)
            for week in contributor['weeks']:
                contributor_obj.commits += week['c']
                contributor_obj.additions += week['a']
                contributor_obj.deletions += week['d']
            contributor_obj.delta = contributor_obj.additions + contributor_obj.deletions

        contributors_json.clear()
        login_contributor.clear()
        contributors_info = sorted(contributors_info, key=lambda key: (key.commits, key.delta), reverse=True)
        return contributors_info

    def getContributorInfo(self, contributor: Contributor):
        if not isinstance(contributor.url, str) or not contributor.url:
            return contributor

        response = requests.get(
            url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/commits"
                f"?author={contributor.login}&per_page=1&page=1",
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        some_commit = json.loads(response.text)

        if len(some_commit) > 0:
            contributor.addValue(some_commit[0]['commit']['author'])

        if contributor.commits > 1:
            response = requests.get(
                url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/commits"
                    f"?author={contributor.login}&per_page=1&page={contributor.commits}",
                headers={
                    'Authorization': self.auth_token,
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            some_commit = json.loads(response.text)

            if len(some_commit) > 0:
                contributor.addValue(some_commit[0]['commit']['author'])

        response = requests.get(
            url=contributor.url,
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        contributor_info = json.loads(response.text)
        contributor.addValue(contributor_info)

        return contributor

    async def getContributorsInfoAsync(self, contributors: List[Contributor]) -> List[Contributor]:
        tasks = []

        user_contributors = []
        for contributor in contributors:
            if contributor.url and isinstance(contributor.url, str):
                user_contributors.append(contributor)

        async with aiohttp.ClientSession() as session:
            for contributor in contributors:
                tasks.append(asyncio.ensure_future(self.getContributorInfoAsync(session, contributor)))
            contributors = await asyncio.gather(*tasks)

        return contributors

    async def getContributorInfoAsync(self, session, contributor: Contributor):
        if not isinstance(contributor.url, str) or not contributor.url:
            return contributor

        some_commit = await self.getAsyncRequest(
            session,
            url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/commits"
                f"?author={contributor.login}&per_page=1&page=1",
        )
        if len(some_commit) > 0:
            contributor.addValue(some_commit[0]['commit']['author'])
        if contributor.commits > 1:
            some_commit = await self.getAsyncRequest(
                session,
                url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/commits"
                    f"?author={contributor.login}&per_page=1&page={contributor.commits}",
            )
            if len(some_commit) > 0:
                contributor.addValue(some_commit[0]['commit']['author'])

        contributor_info = await self.getAsyncRequest(
            session,
            url=contributor.url
        )
        contributor.addValue(contributor_info)

        return contributor

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

    def checkContributor(self, contributor):
        for field in self.config['fields']:
            self.checkContributorField(contributor, field)
        return contributor

    def checkContributorField(self, contributor, field):
        contributor_field = contributor.__dict__.get(field['name'], field['type'])
        trigRuleList = []

        if isinstance(contributor_field, list):
            for contributor_field_value in contributor_field:
                trigRuleList += self.checkFieldRules(contributor_field_value.lower(), field)
        else:
            trigRuleList += self.checkFieldRules(contributor_field.lower(), field)
        contributor.triggeredRules += trigRuleList
        for trigRule in trigRuleList:
            contributor.triggeredRulesDesc.append(trigRule.getPrint())
            contributor.riskRating += trigRule.riskValue
        return

    def checkFieldRules(self, value, field) -> List[TriggeredRule]:
        trigRuleList: List[TriggeredRule] = []
        for rule in field['rules']:
            for trigger in rule['triggers']:
                if trigger in value:
                    trigRule = TriggeredRule()
                    trigRule.type = rule['type']
                    trigRule.value = value
                    trigRule.trigger = trigger
                    trigRule.fieldName = field['name']
                    trigRule.riskValue = rule['risk_value']
                    trigRuleList.append(trigRule)
        return trigRuleList




