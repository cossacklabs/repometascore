import json
import aiohttp
import asyncio
import os, sys
from typing import List, Dict

from .MyGithubApi import MyGithubApi
from .RiskyRepo import RiskyRepo
from .Contributor import Contributor
from .TriggeredRule import TriggeredRule

# This function returns repository name from
# GitHub url of repository. It can be whether
# https or http url. And it must follow next rules:
# aaa/xxx/repo_name or aaa/xxx/repo_name/other_info/.../etc
# example:
# input: 'https://github.com/yandex/yandex-tank'
# output: 'yandex-tank'
def get_repo_name(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_name = repo_name[repo_name.find('/') + 1:]
    repo_name = repo_name[repo_name.find('/') + 1:]
    if repo_name.find('/') > 0:
        repo_name = repo_name[:repo_name.find('/')]

    return repo_name

# This function returns repository name from
# GitHub url of repository. It can be whether
# https or http url. And it must follow next rules:
# aaa/repo_author/xxx or aaa/repo_author/other_info/.../etc
# or aaa/repo_author
# example:
# input: 'https://github.com/yandex/yandex-tank'
# output: 'yandex'
def get_repo_author(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_author = repo_name[repo_name.find('/') + 1:]
    if repo_author.find('/') > 0:
        repo_author = repo_author[:repo_author.find('/')]
    return repo_author


class RCH:
    repo_author: str
    repo_name: str
    auth_token_max_retries: int
    myGithubApi: MyGithubApi
    config: Dict

    def __init__(self, repo_url, config=None, git_token=None):
        self.initialiseVariables()
        self.repo_author = get_repo_author(repo_url)
        self.repo_name = get_repo_name(repo_url)
        if not config:
            config = os.path.join(os.path.dirname(__file__), 'data/config.json')
        with open(config) as conf_file:
            self.config = json.load(conf_file)
        if git_token:
            self.config['git_token'] = git_token
        auth_token = f"token {self.config['git_token']}"
        auth_token_max_retries = self.config['auth_token_max_retries']
        self.myGithubApi = MyGithubApi(auth_token, auth_token_max_retries)

    def initialiseVariables(self):
        self.repo_author = str()
        self.repo_name = str()
        self.auth_token_max_retries = int()
        self.config = {}

    def checkAuthToken(self):
        return self.myGithubApi.checkAuthTokenRetries(self.myGithubApi.auth_token_max_retries)

    async def scanRepo(self):
        if not self.checkAuthToken():
            return False, None

        repo_result = RiskyRepo(
            self.repo_author,
            self.repo_name,
            self.config
        )

        contributors: List[Contributor] = []
        contributors = self.getContributorsList()
        contributors = await self.fillContributorsWithInfo(contributors)

        for contributor in contributors:
            if not isinstance(contributor.url, str) or not contributor.url:
                continue
            contributor = self.checkAndFillContributor(contributor)
            repo_result.addContributor(contributor)

        return True, repo_result

    def getContributorsList(self) -> List[Contributor]:
        contributors_info = []
        login_contributor = {}

        # get list of all contributors:
        # anonymous contributors are currently turned off
        contributors_json = self.myGithubApi.getRepoContributors(self.repo_author, self.repo_name)
        for contributor in contributors_json:
            contributor_obj = Contributor(contributor)
            contributors_info.append(contributor_obj)
            if contributor['type'] != "Anonymous":
                login_contributor[contributor_obj.login] = contributor_obj

        # get contributors with stats (only top100)
        contributors_json = self.myGithubApi.getRepoContributorsStats(self.repo_author, self.repo_name)
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

        return contributors_info

    async def fillContributorsWithInfo(self, contributors: List[Contributor]) -> List[Contributor]:
        tasks = []

        user_contributors = []
        for contributor in contributors:
            if contributor.url and isinstance(contributor.url, str):
                user_contributors.append(contributor)

        async with aiohttp.ClientSession() as session:
            for contributor in user_contributors:
                tasks.append(asyncio.ensure_future(contributor.fillWithInfo(
                    session,
                    self.repo_author,
                    self.repo_name,
                    self.myGithubApi
                )))
            contributors = await asyncio.gather(*tasks)

        return contributors

    def checkAndFillContributor(self, contributor):
        for field in self.config['fields']:
            self.checkAndFillContributorField(contributor, field)
        return contributor

    def checkAndFillContributorField(self, contributor, field):
        contributor_field = contributor.__dict__.get(field['name'])
        trigRuleList = []

        if contributor_field and isinstance(contributor_field, list):
            for contributor_field_value in contributor_field:
                trigRuleList += self.checkFieldRules(contributor_field_value.lower(), field)
        elif contributor_field:
            trigRuleList += self.checkFieldRules(contributor_field.lower(), field)
        contributor.triggeredRules += trigRuleList
        for trigRule in trigRuleList:
            contributor.riskRating += trigRule.riskValue
        return

    def checkFieldRules(self, value, field) -> List[TriggeredRule]:
        trigRuleList: List[TriggeredRule] = []
        for rule in field['rules']:
            for trigger in rule['triggers']:
                if trigger in value:
                    trigRule = TriggeredRule(
                        fieldName=field['name'],
                        type=rule['type'],
                        trigger=trigger,
                        value=value,
                        riskValue=rule['risk_value']
                    )
                    trigRuleList.append(trigRule)
        return trigRuleList
