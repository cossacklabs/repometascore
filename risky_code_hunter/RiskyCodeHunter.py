import asyncio
import json
from typing import List, Dict, Tuple, Iterable, Set

from .Contributor import Contributor
from .RequestManager import RequestManager
from .RiskyRepo import Repo
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
    requestManager: RequestManager
    verbose: int
    config: Dict

    def __init__(self, config, git_tokens=None, verbose: int = 0):
        self.__load_config(config)
        if isinstance(git_tokens, List):
            self.config['git_tokens'] = git_tokens
        self.requestManager = RequestManager(self.config, verbose=verbose)
        self.repo_list = []
        self.verbose = verbose
        return

    # load config via config file
    # if file not found or was not provided
    # raise an Exception
    def __load_config(self, config_file):
        if not config_file:
            raise Exception("No config file has been provided!")
        try:
            with open(config_file) as file:
                self.config = json.load(file)
        except FileNotFoundError:
            raise Exception("Wrong config file has been provided!")

    async def scan_repo(self, repo_url) -> Tuple[bool, Repo]:
        if not await self.requestManager.initialize_tokens():
            return False, None
        if not repo_url:
            raise Exception("No repository URL has been provided!")
        repo_scan = Repo(
            get_repo_author(repo_url),
            get_repo_name(repo_url),
            self.config
        )
        self.repo_list.append(repo_scan)

        self.print(f"Starting to scan '{repo_scan.repo_author}/{repo_scan.repo_name}' repository")
        await repo_scan.get_contributors_list(self.requestManager)
        await self.__check_and_fill_repo_contributor_wrap(repo_scan)
        repo_scan.update_risky_list()
        self.print(f"End of scanning '{repo_scan.repo_author}/{repo_scan.repo_name}' repository")
        return True, repo_scan

    async def scan_repos(self, repo_url_list: Iterable[str]) -> List[Tuple[bool, Repo]]:
        if not await self.requestManager.initialize_tokens():
            return []

        tasks = []
        for repo_url in repo_url_list:
            tasks.append(asyncio.ensure_future(self.scan_repo(repo_url)))
        results = list(await asyncio.gather(*tasks, return_exceptions=True))
        for result in results:
            if isinstance(result, Exception):
                print("Error while scanning repo\n", result)
        return list(filter(lambda x: not isinstance(x, Exception), results))

    async def __check_and_fill_repo_contributor_wrap(self, repo_scan: Repo) -> List[Contributor]:
        tasks = []
        user_contributors = []
        for contributor in repo_scan.contributors_list:
            if contributor.url and isinstance(contributor.url, str):
                user_contributors.append(contributor)
        for contributor in user_contributors:
            tasks.append(asyncio.ensure_future(self.__check_and_fill_contributor(repo_scan, contributor)))
        contributors = list(await asyncio.gather(*tasks))
        return contributors

    async def __check_and_fill_contributor(self, repo_scan: Repo, contributor: Contributor):
        contributor = await contributor.fill_with_info(repo_scan.repo_author, repo_scan.repo_name, self.requestManager)
        contributor = await self.__check_contributor(contributor)
        if contributor.riskRating <= repo_scan.risk_boundary_value + 3:
            # TODO additional info from github repo
            # clone GitHub repo and check commit timezones
            # self.checkTimezones(cloned_repo_path, contributor.emails)
            pass
        return contributor

    async def __check_contributor(self, contributor):
        for field in self.config['fields']:
            await self.__check_contributor_field(contributor, field)
        return contributor

    async def __check_contributor_field(self, contributor, field):
        contributor_field = contributor.__dict__.get(field['name'])
        trig_rule_list = []
        if isinstance(contributor_field, Set):
            for contributor_field_value in contributor_field:
                trig_rule_list += await self.__check_field_rules(contributor_field_value.lower(), field)
        elif contributor_field:
            trig_rule_list += await self.__check_field_rules(contributor_field.lower(), field)
        contributor.triggeredRules += trig_rule_list
        for trigRule in trig_rule_list:
            contributor.riskRating += trigRule.riskValue
        return

    async def __check_field_rules(self, value, field) -> List[TriggeredRule]:
        trig_rule_list: List[TriggeredRule] = []
        for rule in field['rules']:
            for trigger in rule['triggers']:
                if trigger in value:
                    trig_rule = TriggeredRule(
                        field_name=field['name'],
                        type_verbal=rule['type'],
                        trigger=trigger,
                        value=value,
                        risk_value=rule['risk_value']
                    )
                    trig_rule_list.append(trig_rule)
        return trig_rule_list

    def print(self, *args, verbose_level: int = 1, **kwargs):
        if self.verbose >= verbose_level:
            print(*args, **kwargs)

    async def close(self):
        await self.requestManager.close_session()
