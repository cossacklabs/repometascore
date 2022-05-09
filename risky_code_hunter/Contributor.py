import asyncio
from typing import List, Dict, Set

from .DomainInfo import DomainInfo
from .TwitterAPI import TwitterAPI
from .RequestManager import RequestManager
from .MyGithubApi import GithubAPI
from .TriggeredRule import TriggeredRule


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
            self.addValue(input_dict)
        return

    # Get some dict with values
    # If found interesting values
    # We would add them and rewrite
    # Old object values
    def addValue(self, input_dict: Dict):
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

        riskRating = input_dict.get('riskRating')
        if isinstance(riskRating, float):
            self.riskRating = riskRating

        return

    async def fillWithInfo(self, repo_author, repo_name, requestManager: RequestManager):
        if not (isinstance(self.url, str) and self.url):
            return self

        await self.fillWithProfileInfo(requestManager.githubAPI)
        tasks = [
            asyncio.ensure_future(self.fillWithCommitsInfo(repo_author, repo_name, requestManager.githubAPI)),
            asyncio.ensure_future(self.fillWithTwitterInfo(requestManager.twitterAPI)),
            asyncio.ensure_future(self.fillWithBlogURLInfo(requestManager.domainInfo))
        ]
        await asyncio.gather(*tasks)
        return self

    async def fillWithCommitsInfo(self, repo_author, repo_name, githubAPI: GithubAPI):
        if not (isinstance(self.url, str) and self.url):
            return

        page: int = 1
        per_page: int = 100
        commits_info = await githubAPI.getRepoCommitByAuthor(
            repo_author,
            repo_name,
            self.login,
            page,
            per_page
        )
        for commit_info in commits_info:
            self.addValue(commit_info['commit']['author'])

        # we are doing double-check here, because GitHub can store correct counter for commits
        # but can't store info about all commits
        if len(commits_info) == per_page and self.commits > per_page:
            commits_info = await githubAPI.getRepoCommitByAuthor(
                repo_author,
                repo_name,
                self.login,
                (self.commits // per_page) + 1,
                per_page
            )
            for commit_info in commits_info:
                self.addValue(commit_info['commit']['author'])
        return

    async def fillWithProfileInfo(self, githubAPI):
        if not (isinstance(self.url, str) and self.url):
            return
        contributor_info = await githubAPI.getUserProfileInfo(self.url)
        self.addValue(contributor_info)
        return

    def getJSON(self) -> Dict:
        result = self.__dict__.copy()

        result['names'] = list(self.names)
        result['emails'] = list(self.emails)
        result['location'] = list(self.location)
        result['bio'] = list(self.bio)

        triggeredRules = []
        for triggeredRule in self.triggeredRules:
            triggeredRules.append(triggeredRule.getJSON())
        result['triggeredRules'] = triggeredRules

        return result

    async def fillWithTwitterInfo(self, twitterAPI: TwitterAPI):
        if not isinstance(self.twitter_username, Set):
            return
        for twitter_username in self.twitter_username:
            twitter_info = await twitterAPI.getTwitterAccountInfo(twitter_username)
            try:
                add_dict = {
                    'name': twitter_info['data']['user']['result']['legacy']['name'],
                    'location': twitter_info['data']['user']['result']['legacy']['location'],
                    'bio': twitter_info['data']['user']['result']['legacy']['description']
                }
            except KeyError as e:
                # Current twitter account does not exists
                # Example: https://twitter.com/1anisim
                # Response example:
                # { "data" : {} }
                continue
            self.addValue(add_dict)
        return

    async def fillWithBlogURLInfo(self, domainInfo: DomainInfo):
        if not (isinstance(self.blog, str) and self.blog):
            return
        blog_domain = domainInfo.get_domain(self.blog)
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
        blogURLLocationInfo = await domainInfo.get_domain_info(self.blog)
        self.location.update(blogURLLocationInfo['location'])
