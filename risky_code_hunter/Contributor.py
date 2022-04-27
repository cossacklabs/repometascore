from typing import List, Dict

from .MyGithubApi import GithubApi
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
    location: str
    emails: List[str]
    twitter_username: str
    names: List[str]
    company: str
    blog: str
    bio: str

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
        self.location = str()
        self.emails = []
        self.twitter_username = str()
        self.names = []
        self.company = str()
        self.blog = str()
        self.bio = str()
        self.riskRating = float()
        self.triggeredRules = []
        if input_dict:
            self.addValue(input_dict)
        return

    # Get some dict with values
    # If found interesting values
    # We would add them and rewrite
    # Old object values
    def addValue(self, input_dict: dict):
        # Check whether we have dict as input
        if not isinstance(input_dict, dict):
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
            self.location = location

        email = input_dict.get('email', '')
        if email and isinstance(email, str) and email not in self.emails:
            self.emails.append(email)

        twitter_username = input_dict.get('twitter', '')
        if twitter_username and isinstance(twitter_username, str):
            self.twitter_username = twitter_username

        twitter_username = input_dict.get('twitter_username', '')
        if twitter_username and isinstance(twitter_username, str):
            self.twitter_username = twitter_username

        name = input_dict.get('name', '')
        if name and isinstance(name, str) and name not in self.names:
            self.names.append(name)

        company = input_dict.get('company', '')
        if company and isinstance(company, str):
            self.company = company

        blog = input_dict.get('blog', '')
        if blog and isinstance(blog, str):
            self.blog = blog

        bio = input_dict.get('bio', '')
        if bio and isinstance(bio, str):
            self.bio = bio

        riskRating = input_dict.get('riskRating', 0.0)
        if riskRating and isinstance(riskRating, float):
            self.riskRating = riskRating

        return

    async def fillWithInfo(self, repo_author, repo_name, githubApi: GithubApi):
        if not isinstance(self.url, str) or not self.url:
            return self
        await self.fillWithCommitsInfo(repo_author, repo_name, githubApi)
        await self.fillWithProfileInfo(githubApi)
        await self.fillWithTwitterLocation(githubApi)
        await self.fillWithBlogDomain(githubApi)
        return self

    async def fillWithCommitsInfo(self, repo_author, repo_name, githubApi: GithubApi):
        if not isinstance(self.url, str) or not self.url:
            return

        commit_info = await githubApi.getRepoCommitByAuthor(
            repo_author,
            repo_name,
            self.login,
            1
        )
        if len(commit_info) > 0:
            self.addValue(commit_info[0]['commit']['author'])

        if self.commits > 1:
            commit_info = await githubApi.getRepoCommitByAuthor(
                repo_author,
                repo_name,
                self.login,
                self.commits
            )
            if len(commit_info) > 0:
                self.addValue(commit_info[0]['commit']['author'])
        return

    async def fillWithProfileInfo(self, githubApi):
        if not isinstance(self.url, str) or not self.url:
            return
        contributor_info = await githubApi.getUserProfileInfo(self.url)
        self.addValue(contributor_info)
        return

    async def fillWithTwitterLocation(self, githubApi):
        if not isinstance(self.twitter_username, str) or not self.twitter_username:
            return
        ## TODO: add getting twitter location
        return

    async def fillWithBlogDomain(self, githubApi):
        if not isinstance(self.blog, str) or not self.blog:
            return
        ## TODO: add filling info with blog domain info
        return

    def getJSON(self) -> Dict:
        result = self.__dict__.copy()

        result['names'] = self.names.copy()
        result['emails'] = self.emails.copy()

        triggeredRules = []
        for triggeredRule in self.triggeredRules:
            triggeredRules.append(triggeredRule.getJSON())
        result['triggeredRules'] = triggeredRules

        return result
