import asyncio
from typing import List, Dict, Set

from .DomainInfo import DomainInfo
from .MyGithubApi import GithubAPI
from .RequestManager import RequestManager
from .TriggeredRule import TriggeredRule
from .TwitterAPI import TwitterAPI


class Contributor:
    # main contributor arguments
    login: str
    url: str

    # details about commits in repo
    commits: int
    additions: int
    deletions: int
    delta: int

    # detailed info from profile
    location: Set[str]
    emails: Set[str]
    twitter_username: str
    names: Set[str]
    company: str
    blog: str
    bio: Set[str]

    # risk rating
    # 0 - clear
    # n - risky
    riskRating: float

    # List of instances TriggeredRule
    # Why rule has been triggered
    triggeredRules: List[TriggeredRule]

    def __init__(self, input_dict=None):
        self.login = str()
        self.url = str()
        self.commits = int()
        self.additions = int()
        self.deletions = int()
        self.delta = int()
        self.location = set()
        self.emails = set()
        self.twitter_username = str()
        self.names = set()
        self.company = str()
        self.blog = str()
        self.bio = set()
        self.riskRating = float()
        self.triggeredRules = []
        if input_dict:
            self.add_value(input_dict)
        return

    # Get some dict with values
    # If found interesting values
    # We would add them and rewrite
    # Old object values
    def add_value(self, input_dict: Dict):
        # Check whether we have dict as input
        if not isinstance(input_dict, Dict):
            return

        login = input_dict.get('login')
        if isinstance(login, str):
            self.login = login

        url = input_dict.get('url')
        if isinstance(url, str):
            self.url = url

        commits = input_dict.get('commits')
        if isinstance(commits, int):
            self.commits = commits

        commits = input_dict.get('contributions')
        if isinstance(commits, int):
            self.commits = commits

        additions = input_dict.get('additions')
        if isinstance(additions, int):
            self.additions = additions

        deletions = input_dict.get('deletions')
        if isinstance(deletions, int):
            self.deletions = deletions

        delta = input_dict.get('delta')
        if isinstance(delta, int):
            self.delta = delta

        location = input_dict.get('location')
        if isinstance(location, str):
            self.location.add(location)

        email = input_dict.get('email')
        if isinstance(email, str):
            self.emails.add(email)

        twitter_username = input_dict.get('twitter')
        if isinstance(twitter_username, str):
            self.twitter_username = twitter_username

        twitter_username = input_dict.get('twitter_username')
        if isinstance(twitter_username, str):
            self.twitter_username = twitter_username

        name = input_dict.get('name')
        if isinstance(name, str):
            self.names.add(name)

        company = input_dict.get('company')
        if isinstance(company, str):
            self.company = company

        blog = input_dict.get('blog')
        if isinstance(blog, str):
            self.blog = blog

        bio = input_dict.get('bio')
        if isinstance(bio, str):
            self.bio.add(bio)

        risk_rating = input_dict.get('riskRating')
        if isinstance(risk_rating, float):
            self.riskRating = risk_rating

        return

    async def fill_with_info(self, repo_author, repo_name, request_manager: RequestManager):
        if not (isinstance(self.url, str) and self.url):
            return self

        await self.fillWithProfileInfo(requestManager.githubAPI)
        tasks = [
            asyncio.ensure_future(self.fill_with_commits_info(repo_author, repo_name, request_manager.githubAPI)),
            asyncio.ensure_future(self.fill_with_twitter_info(request_manager.twitterAPI)),
            asyncio.ensure_future(self.fill_with_blog_url_info(request_manager.domainInfo)),
        ]
        await asyncio.gather(*tasks)
        return self

    async def fill_with_commits_info(self, repo_author, repo_name, github_api: GithubAPI):
        if not (isinstance(self.url, str) and self.url):
            return

        page: int = 1
        per_page: int = 100
        commits_info = await github_api.get_repo_commit_by_author(
            repo_author,
            repo_name,
            self.login,
            page,
            per_page
        )
        for commit_info in commits_info:
            self.add_value(commit_info['commit']['author'])

        # we are doing double-check here, because GitHub can store correct counter for commits
        # but can't store info about all commits
        if len(commits_info) == per_page and self.commits > per_page:
            commits_info = await github_api.get_repo_commit_by_author(
                repo_author,
                repo_name,
                self.login,
                (self.commits // per_page) + 1,
                per_page
            )
            for commit_info in commits_info:
                self.add_value(commit_info['commit']['author'])
        return

    async def fill_with_profile_info(self, github_api):
        if not (isinstance(self.url, str) and self.url):
            return
        contributor_info = await github_api.get_user_profile_info(self.url)
        self.add_value(contributor_info)
        return

    async def fillWithProfileInfo(self, githubAPI):
        if not (isinstance(self.url, str) and self.url):
            return
        contributor_info = await githubAPI.getUserProfileInfo(self.url)
        self.addValue(contributor_info)
        return

    def get_json(self) -> Dict:
        result = self.__dict__.copy()

        result['names'] = list(self.names)
        result['emails'] = list(self.emails)
        result['location'] = list(self.location)
        result['bio'] = list(self.bio)

        triggered_rules = []
        for triggeredRule in self.triggeredRules:
            triggered_rules.append(triggeredRule.get_json())
        result['triggeredRules'] = triggered_rules

        return result

    async def fill_with_twitter_info(self, twitter_api: TwitterAPI):
        if not isinstance(self.twitter_username, Set):
            return
        for twitter_username in self.twitter_username:
            twitter_info = await twitter_api.get_twitter_account_info(twitter_username)
            try:
                add_dict = {
                    'name': twitter_info['data']['user']['result']['legacy']['name'],
                    'location': twitter_info['data']['user']['result']['legacy']['location'],
                    'bio': twitter_info['data']['user']['result']['legacy']['description']
                }
            except KeyError:
                # Current twitter account does not exists
                # Example: https://twitter.com/1anisim
                # Response example:
                # { "data" : {} }
                continue
            self.add_value(add_dict)
        return

    async def fill_with_blog_url_info(self, domain_info: DomainInfo):
        if not (isinstance(self.blog, str) and self.blog):
            return
        blog_domain = domain_info.get_domain(self.blog)
        if blog_domain[-8:] == "about.me":
            return
            # TODO about.me retrieve info part
        if blog_domain[-12:] == "linkedin.com":
            return
            # TODO www.linkedin.com retrieve info part
        if blog_domain[-10:] == "github.com":
            return
        if blog_domain[-9:] == "github.io":
            return
        if blog_domain[-12:] == "facebook.com":
            return
        blog_url_location_info = await domain_info.get_domain_info(self.blog)
        self.location.update(blog_url_location_info['location'])
