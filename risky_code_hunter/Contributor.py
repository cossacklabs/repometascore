from typing import List, Dict, Set

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

        login = input_dict.get('login', '')
        if login and isinstance(login, str):
            self.login = login

        url = input_dict.get('url', '')
        if url and isinstance(url, str):
            self.url = url

        commits = input_dict.get('commits', 0)
        if commits and isinstance(commits, int):
            self.commits = commits

        commits = input_dict.get('contributions', 0)
        if commits and isinstance(commits, int):
            self.commits = commits

        additions = input_dict.get('additions', 0)
        if additions and isinstance(additions, int):
            self.additions = additions

        deletions = input_dict.get('deletions', 0)
        if deletions and isinstance(deletions, int):
            self.deletions = deletions

        delta = input_dict.get('delta', 0)
        if delta and isinstance(delta, int):
            self.delta = delta

        location = input_dict.get('location', '')
        if location and isinstance(location, str):
            self.location.add(location)

        email = input_dict.get('email', '')
        if email and isinstance(email, str):
            self.emails.add(email)

        twitter_username = input_dict.get('twitter', '')
        if twitter_username and isinstance(twitter_username, str):
            self.twitter_username = twitter_username

        twitter_username = input_dict.get('twitter_username', '')
        if twitter_username and isinstance(twitter_username, str):
            self.twitter_username = twitter_username

        name = input_dict.get('name', '')
        if name and isinstance(name, str):
            self.names.add(name)

        company = input_dict.get('company', '')
        if company and isinstance(company, str):
            self.company = company

        blog = input_dict.get('blog', '')
        if blog and isinstance(blog, str):
            self.blog = blog

        bio = input_dict.get('bio', '')
        if bio and isinstance(bio, str):
            self.bio.add(bio)

        riskRating = input_dict.get('riskRating', 0.0)
        if riskRating and isinstance(riskRating, float):
            self.riskRating = riskRating

        return

    async def fillWithInfo(self, repo_author, repo_name, requestManager: RequestManager):
        if not (isinstance(self.url, str) or self.url):
            return self
        await self.fillWithCommitsInfo(repo_author, repo_name, requestManager.githubAPI)
        await self.fillWithProfileInfo(requestManager.githubAPI)
        await self.fillWithTwitterInfo(requestManager.twitterAPI)
        return self

    async def fillWithCommitsInfo(self, repo_author, repo_name, githubAPI: GithubAPI):
        if not (isinstance(self.url, str) or self.url):
            return

        commit_info = await githubAPI.getRepoCommitByAuthor(
            repo_author,
            repo_name,
            self.login,
            1
        )
        if len(commit_info) > 0:
            self.addValue(commit_info[0]['commit']['author'])

        if self.commits > 1:
            commit_info = await githubAPI.getRepoCommitByAuthor(
                repo_author,
                repo_name,
                self.login,
                self.commits
            )
            if len(commit_info) > 0:
                self.addValue(commit_info[0]['commit']['author'])
        return

    async def fillWithProfileInfo(self, githubAPI):
        if not (isinstance(self.url, str) or self.url):
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
        if not (isinstance(self.twitter_username, str) or self.twitter_username):
            return
        twitter_info = await twitterAPI.getTwitterAccountInfo(self.twitter_username)
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
            return
        self.addValue(add_dict)
        return
