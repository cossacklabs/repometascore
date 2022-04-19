import json
import aiohttp
import asyncio
from typing import List, Dict, Tuple

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


class RiskyCodeHunter:
    risky_repo_list: List[RiskyRepo]
    auth_token_max_retries: int
    myGithubApi: MyGithubApi
    config: Dict

    def __init__(self, config=None, git_token=None):
        self.initialiseVariables()
        if not config:
            raise Exception("No config file has been provided!")
        try:
            with open(config) as conf_file:
                self.config = json.load(conf_file)
        except FileNotFoundError:
            raise Exception("Wrong config file has been provided!")
        if git_token:
            self.config['git_token'] = git_token
        auth_token = f"token {self.config['git_token']}"
        self.myGithubApi = MyGithubApi(
            auth_token,
            self.config.get('auth_token_max_retries', 5),
            self.config.get('github_min_await', 5.0),
            self.config.get('github_max_await', 15.0)
        )

    def initialiseVariables(self):
        self.config = {}
        self.risky_repo_list = []
        self.auth_token_max_retries = int()

    def checkAuthToken(self):
        return self.myGithubApi.checkAuthTokenRetries(self.myGithubApi.auth_token_max_retries)

    async def checkAuthTokenAsync(self, session):
        return await self.myGithubApi.checkAuthTokenRetriesAsync(session, self.myGithubApi.auth_token_max_retries)

    async def scanRepo(self, repo_url) -> Tuple[bool, RiskyRepo]:
        session = aiohttp.ClientSession()
        try:
            if not await self.checkAuthTokenAsync(session):
                return False, None
            if not repo_url:
                raise Exception("No repository URL has been provided!")
            risky_repo_scan = RiskyRepo(
                get_repo_author(repo_url),
                get_repo_name(repo_url),
                self.config
            )
            self.risky_repo_list.append(risky_repo_scan)

            contributors: List[Contributor]
            contributors = await risky_repo_scan.getContributorsList(session, self.myGithubApi)
            await self.checkAndFillRepoContributorWrap(session, risky_repo_scan)
            await risky_repo_scan.updateRiskyList()
        finally:
            await session.close()
        return True, risky_repo_scan

    async def __scanRepoSuppress(self, repo_url) -> Tuple[bool, RiskyRepo]:
        result = False, None
        try:
            result = await self.scanRepo(repo_url)
        except Exception as e:
            print(e)
        return result

    async def scanRepos(self, repo_url_list) -> List[Tuple[bool, RiskyRepo]]:
        tasks = []
        for repo_url in repo_url_list:
            tasks.append(asyncio.ensure_future(self.__scanRepoSuppress(repo_url)))
        results = list(await asyncio.gather(*tasks))
        return results

    async def checkAndFillRepoContributorWrap(self, session, risky_repo_scan: RiskyRepo) -> List[Contributor]:
        tasks = []
        user_contributors = []
        for contributor in risky_repo_scan.contributorsList:
            if contributor.url and isinstance(contributor.url, str):
                user_contributors.append(contributor)

        for contributor in user_contributors:
            tasks.append(asyncio.ensure_future(self.checkAndFillContributor(session, risky_repo_scan, contributor)))
        contributors = list(await asyncio.gather(*tasks))
        return contributors

    async def checkAndFillContributor(self, session, risky_repo_scan: RiskyRepo, contributor: Contributor):
        contributor = await contributor.fillWithInfo(session, risky_repo_scan.repo_author, risky_repo_scan.repo_name, self.myGithubApi)
        contributor = await self.checkContributor(contributor)
        if contributor.riskRating <= risky_repo_scan.risk_boundary_value + 3:
            ## TODO additional info from github repo
            ## clone githubrepo and check commit timezones
            # self.checkTimezones(cloned_repo_path, contributor.emails)
            pass
        return contributor

    async def checkContributor(self, contributor):
        for field in self.config['fields']:
            await self.checkContributorField(contributor, field)
        return contributor

    async def checkContributorField(self, contributor, field):
        contributor_field = contributor.__dict__.get(field['name'])
        trigRuleList = []

        if contributor_field and isinstance(contributor_field, list):
            for contributor_field_value in contributor_field:
                trigRuleList += await self.checkFieldRules(contributor_field_value.lower(), field)
        elif contributor_field:
            trigRuleList += await self.checkFieldRules(contributor_field.lower(), field)
        contributor.triggeredRules += trigRuleList
        for trigRule in trigRuleList:
            contributor.riskRating += trigRule.riskValue
        return

    async def checkFieldRules(self, value, field) -> List[TriggeredRule]:
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
