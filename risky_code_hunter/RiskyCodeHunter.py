import asyncio
import json
import re
from typing import List, Dict, Tuple, Iterable
from urllib.parse import urlparse

from .Contributor import Contributor
from .RequestManager import RequestManager
from .RiskyRepo import Repo
from .TriggeredRule import TriggeredRule


# https://github.com/repo_author/repo_name/ -> /repo_author/repo_name/ -> repo_author/repo_name -> repo_name
def get_repo_name(repo_url) -> str:
    return str(urlparse(repo_url).path).strip('/').split('/')[1]


# https://github.com/repo_author/repo_name/ -> /repo_author/repo_name/ -> repo_author/repo_name -> repo_author
def get_repo_author(repo_url) -> str:
    return str(urlparse(repo_url).path).strip('/').split('/')[0]


class RiskyCodeHunter:
    repo_list: List[Repo]
    request_manager: RequestManager
    verbose: int
    config: Dict
    compiled_regex_pattern: re.Pattern

    def __init__(self, config, git_tokens=None, verbose: int = 0):
        self.__load_config(config)
        if isinstance(git_tokens, List):
            self.config['git_tokens'] = git_tokens
        self.request_manager = RequestManager(self.config, verbose=verbose)
        self.repo_list = []
        self.verbose = verbose
        self.compiled_regex_pattern = re.compile(r"[!@#$%^&*()\[\]{};:,./<>?|`~=_+]")
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
        if not await self.request_manager.initialize_tokens():
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
        await repo_scan.get_contributors_list(self.request_manager)
        await self.__check_and_fill_repo_contributor_wrap(repo_scan)
        repo_scan.update_risky_list()
        self.print(f"End of scanning '{repo_scan.repo_author}/{repo_scan.repo_name}' repository")
        return True, repo_scan

    async def scan_repos(self, repo_url_list: Iterable[str]) -> List[Tuple[bool, Repo]]:
        if not await self.request_manager.initialize_tokens():
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
        contributor = await contributor.fill_with_info(repo_scan.repo_author, repo_scan.repo_name, self.request_manager)
        contributor = await self.__check_contributor(contributor)
        if contributor.risk_rating <= repo_scan.risk_boundary_value + 3:
            # TODO additional info from github repo
            # clone GitHub repo and check commit timezones
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
    async def __check_twitter_username_rules(self, twitter_usernames, twitter_username_rules) -> List[TriggeredRule]:
        triggered_rules: List[TriggeredRule] = []
        for twitter_username in twitter_usernames:
            triggered_rules.extend(
                await self.__check_field_rules_substr(twitter_username.lower(), twitter_username_rules)
            )
        return triggered_rules

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
        value_modified = self.compiled_regex_pattern.sub(" ", value)
        value_modified = ''.join((' ', value_modified, ' '))
        trig_rule_list: List[TriggeredRule] = []
        for rule in field['rules']:
            for trigger in rule['triggers']:
                if f" {trigger} " in value_modified:
                    trig_rule = TriggeredRule(
                        field_name=field['name'],
                        type_verbal=rule['type'],
                        trigger=trigger,
                        value=value,
                        risk_value=rule['risk_value']
                    )
                    trig_rule_list.append(trig_rule)
        return trig_rule_list

    async def __check_field_rules_substr(self, value, field) -> List[TriggeredRule]:
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
        await self.request_manager.close_session()
