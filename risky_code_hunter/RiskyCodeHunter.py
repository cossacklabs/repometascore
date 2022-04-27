import json
import asyncio
from typing import List, Dict, Tuple, Iterable

from .MyGithubApi import GithubApi
from .RiskyRepo import Repo
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
    repo_list: List[Repo]
    githubApi: GithubApi
    config: Dict

    def __init__(self, config, git_token=None):
        self.__loadConfig(config)
        if git_token:
            self.config['git_token'] = git_token
        auth_token = f"token {self.config['git_token']}"
        self.githubApi = GithubApi(
            auth_token,
            self.config.get('auth_token_max_retries', 5),
            self.config.get('github_min_await', 5.0),
            self.config.get('github_max_await', 15.0)
        )
        self.repo_list = []

    # load config via config file
    # if file not found or was not provided
    # raise an Exception
    def __loadConfig(self, config_file):
        if not config_file:
            raise Exception("No config file has been provided!")
        try:
            with open(config_file) as file:
                self.config = json.load(file)
        except FileNotFoundError:
            raise Exception("Wrong config file has been provided!")

    async def checkAuthToken(self) -> bool:
        return await self.githubApi.checkAuthTokenRetries(self.githubApi.auth_token_max_retries)

    async def scanRepo(self, repo_url) -> Tuple[bool, Repo]:
        if not await self.checkAuthToken():
            return False, None
        if not repo_url:
            raise Exception("No repository URL has been provided!")
        repo_scan = Repo(
            get_repo_author(repo_url),
            get_repo_name(repo_url),
            self.config
        )
        self.repo_list.append(repo_scan)

        print(f"Starting to scan '{repo_scan.repo_author}/{repo_scan.repo_name}' repository")
        await repo_scan.getContributorsList(self.githubApi)
        await self.__checkAndFillRepoContributorWrap(repo_scan)
        repo_scan.updateRiskyList()
        print(f"End of scanning '{repo_scan.repo_author}/{repo_scan.repo_name}' repository")
        return True, repo_scan

    async def scanRepos(self, repo_url_list: Iterable[str]) -> List[Tuple[bool, Repo]]:
        if not await self.checkAuthToken():
            return []
        tasks = []
        for repo_url in repo_url_list:
            tasks.append(asyncio.ensure_future(self.scanRepo(repo_url)))
        results = list(await asyncio.gather(*tasks, return_exceptions=True))
        for result in results:
            if isinstance(result, Exception):
                print(result)
        return list(filter(lambda x: not isinstance(x, Exception), results))

    async def __checkAndFillRepoContributorWrap(self, repo_scan: Repo) -> List[Contributor]:
        tasks = []
        user_contributors = []
        for contributor in repo_scan.contributorsList:
            if contributor.url and isinstance(contributor.url, str):
                user_contributors.append(contributor)
        for contributor in user_contributors:
            tasks.append(asyncio.ensure_future(self.__checkAndFillContributor(repo_scan, contributor)))
        contributors = list(await asyncio.gather(*tasks))
        return contributors

    async def __checkAndFillContributor(self, repo_scan: Repo, contributor: Contributor):
        contributor = await contributor.fillWithInfo(repo_scan.repo_author, repo_scan.repo_name, self.githubApi)
        contributor = await self.__checkContributor(contributor)
        if contributor.riskRating <= repo_scan.risk_boundary_value + 3:
            ## TODO additional info from github repo
            ## clone githubrepo and check commit timezones
            # self.checkTimezones(cloned_repo_path, contributor.emails)
            pass
        return contributor

    async def __checkContributor(self, contributor):
        for field in self.config['fields']:
            await self.__checkContributorField(contributor, field)
        return contributor

    async def __checkContributorField(self, contributor, field):
        contributor_field = contributor.__dict__.get(field['name'])
        trigRuleList = []

        if contributor_field and isinstance(contributor_field, list):
            for contributor_field_value in contributor_field:
                trigRuleList += await self.__checkFieldRules(contributor_field_value.lower(), field)
        elif contributor_field:
            trigRuleList += await self.__checkFieldRules(contributor_field.lower(), field)
        contributor.triggeredRules += trigRuleList
        for trigRule in trigRuleList:
            contributor.riskRating += trigRule.riskValue
        return

    async def __checkFieldRules(self, value, field) -> List[TriggeredRule]:
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

    async def close(self):
        await self.githubApi.closeSession()
