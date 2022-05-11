import json
import asyncio
import re
from typing import List, Dict, Tuple, Iterable, Set

from .RequestManager import RequestManager
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
    requestManager: RequestManager
    verbose: int
    config: Dict

    def __init__(self, config, git_token=None, verbose: int = 0):
        self.__loadConfig(config)
        if git_token:
            self.config['git_token'] = git_token
        self.requestManager = RequestManager(self.config, verbose=verbose)
        self.repo_list = []
        self.verbose = verbose
        return

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
        return await self.requestManager.githubAPI.checkAuthTokenRetries()

    async def scanRepo(self, repo_url) -> Tuple[bool, Repo]:
        if not await self.requestManager.initializeTokens():
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
        await repo_scan.getContributorsList(self.requestManager)
        await self.__checkAndFillRepoContributorWrap(repo_scan)
        repo_scan.updateRiskyList()
        self.print(f"End of scanning '{repo_scan.repo_author}/{repo_scan.repo_name}' repository")
        return True, repo_scan

    async def scanRepos(self, repo_url_list: Iterable[str]) -> List[Tuple[bool, Repo]]:
        if not await self.requestManager.initializeTokens():
            return []

        tasks = []
        for repo_url in repo_url_list:
            tasks.append(asyncio.ensure_future(self.scanRepo(repo_url)))
        results = list(await asyncio.gather(*tasks, return_exceptions=True))
        for result in results:
            if isinstance(result, Exception):
                print("Error while scanning repo\n", result)
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
        contributor = await contributor.fillWithInfo(repo_scan.repo_author, repo_scan.repo_name, self.requestManager)
        contributor = await self.__check_contributor(contributor)
        if contributor.riskRating <= repo_scan.risk_boundary_value + 3:
            # TODO additional info from github repo
            # clone githubrepo and check commit timezones
            # self.checkTimezones(cloned_repo_path, contributor.emails)
            pass
        return contributor

    async def __check_contributor(self, contributor):
        for field in self.config['fields']:
            if field['name'].lower() == 'login':
                await self.__check_contributor_login(contributor, field)
            elif field['name'].lower() == 'location':
                await self.__check_contributor_location(contributor, field)
            elif field['name'].lower() == 'emails':
                await self.__check_contributor_emails(contributor, field)
            elif field['name'].lower() == 'twitter_username':
                await self.__check_contributor_twitter_username(contributor, field)
            elif field['name'].lower() == 'names':
                await self.__check_contributor_names(contributor, field)
            elif field['name'].lower() == 'company':
                await self.__check_contributor_company(contributor, field)
            elif field['name'].lower() == 'blog':
                await self.__check_contributor_blog(contributor, field)
            elif field['name'].lower() == 'bio':
                await self.__check_contributor_bio(contributor, field)
        return contributor

    async def __check_contributor_login(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        login = contributor.login
        trig_rule_list.extend(await self.__check_login_rules(login, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_location(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        locations = contributor.location
        trig_rule_list.extend(await self.__check_location_rules(locations, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_emails(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        emails = contributor.emails
        trig_rule_list.extend(await self.__check_emails_rules(emails, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_twitter_username(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        twitter_username = contributor.twitter_username
        trig_rule_list.extend(await self.__check_twitter_username_rules(twitter_username, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_names(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        names = contributor.names
        trig_rule_list.extend(await self.__check_names_rules(names, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_company(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        company = contributor.company
        trig_rule_list.extend(await self.__check_company_rules(company, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_blog(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        blog = contributor.blog
        trig_rule_list.extend(await self.__check_blog_rules(blog, field))
        contributor.add_triggered_rules(trig_rule_list)

    async def __check_contributor_bio(self, contributor: Contributor, field: Dict):
        trig_rule_list: List[TriggeredRule] = []
        bio = contributor.bio
        trig_rule_list.extend(await self.__check_bio_rules(bio, field))
        contributor.add_triggered_rules(trig_rule_list)

    # Use default substring search
    async def __check_login_rules(self, login, login_rules) -> List[TriggeredRule]:
        return await self.__check_field_rules_substr(login.lower(), login_rules)

    # Only will trigger on same location name
    # Location names are being checked with extra spaces
    async def __check_location_rules(self, locations, location_rules) -> List[TriggeredRule]:
        trig_rule_list: List[TriggeredRule] = []
        for location in locations:
            trig_rule_list.extend(await self.__check_field_rules_location(location.lower(), location_rules))
        return trig_rule_list

    # Use default substring search
    async def __check_emails_rules(self, emails, email_rules) -> List[TriggeredRule]:
        triggered_rules: List[TriggeredRule] = []
        for email in emails:
            triggered_rules.extend(await self.__check_field_rules_substr(email.lower(), email_rules))
        return triggered_rules

    # Use default substring search
    async def __check_twitter_username_rules(self, twitter_username, twitter_username_rules) -> List[TriggeredRule]:
        return await self.__check_field_rules_substr(twitter_username.lower(), twitter_username_rules)

    # Use default substring search
    async def __check_names_rules(self, names, names_rules) -> List[TriggeredRule]:
        triggered_rules: List[TriggeredRule] = []
        for name in names:
            triggered_rules.extend(await self.__check_field_rules_substr(name.lower(), names_rules))
        return triggered_rules

    # Use default substring search
    async def __check_company_rules(self, company, company_rules) -> List[TriggeredRule]:
        return await self.__check_field_rules_substr(company.lower(), company_rules)

    # Use default substring search
    async def __check_blog_rules(self, blog, blog_rules) -> List[TriggeredRule]:
        return await self.__check_field_rules_substr(blog.lower(), blog_rules)

    # Use default substring search
    async def __check_bio_rules(self, bio, bio_rules) -> List[TriggeredRule]:
        triggered_rules: List[TriggeredRule] = []
        for biography in bio:
            triggered_rules.extend(await self.__check_field_rules_substr(biography.lower(), bio_rules))
        return triggered_rules

    async def __check_field_rules_location(self, value, field) -> List[TriggeredRule]:
        value = re.sub(r"[!@#$%^&*()\[\]{};:,./<>?|`~\-=_+]", " ", value)
        value = ''.join((' ', value, ' '))
        trig_rule_list: List[TriggeredRule] = []
        for rule in field['rules']:
            for trigger in rule['triggers']:
                if f" {trigger} " in value:
                    trig_rule = TriggeredRule(
                        fieldName=field['name'],
                        type=rule['type'],
                        trigger=trigger,
                        value=value,
                        riskValue=rule['risk_value']
                    )
                    trig_rule_list.append(trig_rule)
        return trig_rule_list

    async def __check_field_rules_substr(self, value, field) -> List[TriggeredRule]:
        trig_rule_list: List[TriggeredRule] = []
        for rule in field['rules']:
            for trigger in rule['triggers']:
                if trigger in value:
                    trig_rule = TriggeredRule(
                        fieldName=field['name'],
                        type=rule['type'],
                        trigger=trigger,
                        value=value,
                        riskValue=rule['risk_value']
                    )
                    trig_rule_list.append(trig_rule)
        return trig_rule_list

    def print(self, *args, verbose_level: int = 1, **kwargs):
        if self.verbose >= verbose_level:
            print(*args, **kwargs)

    async def close(self):
        await self.requestManager.closeSession()
