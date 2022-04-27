import json
from typing import List, Dict

from .MyGithubApi import GithubApi
from .Contributor import Contributor


class Repo:
    # Repo main info
    repo_author: str
    repo_name: str

    # details about commits in repo
    commits: int
    additions: int
    deletions: int
    delta: int
    contributors_count: int

    # risky ones
    risky_commits: int
    risky_additions: int
    risky_deletions: int
    risky_delta: int
    risky_contributors_count: int

    # contributors list
    contributorsList: List[Contributor]
    # Risky contributors list
    riskyContributorsList: List[Contributor]
    riskyAuthor: Contributor

    # Boundary value that helps us
    # to determine if contributor
    # Is risky or not
    risk_boundary_value: float

    # Provide
    def __init__(self, repo_author, repo_name, config: dict = None):
        self.repo_author = repo_author
        self.repo_name = repo_name
        self.commits = int()
        self.additions = int()
        self.deletions = int()
        self.delta = int()
        self.contributors_count = int()
        self.risky_commits = int()
        self.risky_additions = int()
        self.risky_deletions = int()
        self.risky_delta = int()
        self.risky_contributors_count = int()
        self.contributorsList = []
        self.riskyContributorsList = []
        self.riskyAuthor = None
        self.risk_boundary_value = float()
        if not config:
            config = {}
        self.risk_boundary_value = config.get('risk_boundary_value', 0.9)
        return

    def addContributor(self, contributor: Contributor):
        if not isinstance(contributor, Contributor):
            return
        self.commits += contributor.commits
        self.additions += contributor.additions
        self.deletions += contributor.deletions
        self.delta += contributor.delta
        self.contributors_count += 1
        self.contributorsList.append(contributor)
        return

    def addContributors(self, contributors_list: List[Contributor]):
        for contributor in contributors_list:
            self.addContributor(contributor)

    # Print Full Human-Readable report
    def printFullReport(self):
        for contributor in self.riskyContributorsList:
            if self.repo_author is contributor.login:
                continue
            print("That contributor triggered rules:")
            for triggeredRule in contributor.triggeredRules:
                print(triggeredRule.description)
            riskyDict = contributor.getJSON()
            riskyDict.pop('triggeredRules', None)
            print(json.dumps(riskyDict, indent=4))
            print("=" * 40)

        self.printShortReport()
        return

    # Print short human-readable report
    def printShortReport(self):
        print(f"Risky commits count: {self.risky_commits} \t Risky delta count: {self.risky_delta}")
        print(f"Total commits count: {self.commits} \t Total delta count: {self.delta}")
        print(
            f"Risky commits ratio: {self.risky_commits / self.commits} \t"
            f"Risky delta ratio: {self.risky_delta / self.delta}"
        )
        print(f"{self.risky_contributors_count}/{self.contributors_count} contributors are risky")

        if self.riskyAuthor:
            print("=" * 40)
            print("Warning author of repo suspicious!")
            print("That contributor triggered rules:")
            for triggeredRule in self.riskyAuthor.triggeredRules:
                print(triggeredRule.description)
            riskyDict = self.riskyAuthor.getJSON()
            riskyDict.pop('triggeredRules', None)
            print(json.dumps(riskyDict, indent=4))
        return

    # Print Full Human-Readable report
    def getFullReport(self) -> str:
        separator = '=' * 40
        result = []
        for contributor in self.riskyContributorsList:
            if self.repo_author is contributor.login:
                continue
            result.append("That contributor triggered rules:")
            for triggeredRule in contributor.triggeredRules:
                result.append(triggeredRule.description)
            riskyDict = contributor.getJSON()
            riskyDict.pop('triggeredRules', None)
            result.append(json.dumps(riskyDict, indent=4))
            result.append(separator)
        result.append(self.getShortReport())
        return "\n".join(result)

    # Print short human-readable report
    def getShortReport(self) -> str:
        separator = '=' * 40
        result = []
        result.append(f"Risky commits count: {self.risky_commits} \t Risky delta count: {self.risky_delta}")
        result.append(f"Total commits count: {self.commits} \t Total delta count: {self.delta}")
        result.append(f"Risky commits ratio: {self.risky_commits / self.commits} \t"
                      f"Risky delta ratio: {self.risky_delta / self.delta}")
        result.append(f"{self.risky_contributors_count}/{self.contributors_count} contributors are risky")

        if self.riskyAuthor:
            result.append(separator)
            result.append("Warning author of repo suspicious!")
            result.append("That contributor triggered rules:")
            for triggeredRule in self.riskyAuthor.triggeredRules:
                result.append(triggeredRule.description)
            riskyDict = self.riskyAuthor.getJSON()
            riskyDict.pop('triggeredRules', None)
            result.append(json.dumps(riskyDict, indent=4))
        return "\n".join(result)

    async def getContributorsList(self, myGithubApi: GithubApi) -> List[Contributor]:
        contributors_info = []
        contributors_per_login = {}

        # get list of all contributors:
        # anonymous contributors are currently turned off
        contributors_json = await myGithubApi.getRepoContributors(self.repo_author, self.repo_name)
        for contributor in contributors_json:
            contributor_obj = Contributor(contributor)
            contributors_info.append(contributor_obj)
            if contributor['type'] != "Anonymous":
                contributors_per_login[contributor_obj.login] = contributor_obj

        # get contributors with stats (only top100)
        contributors_json = await myGithubApi.getRepoContributorsStats(self.repo_author, self.repo_name)
        for contributor in contributors_json:
            if contributors_per_login.get(contributor['author']['login']):
                contributor_obj = contributors_per_login.get(contributor['author']['login'])
                contributor_obj.addValue(contributor['author'])
                contributor_obj.commits = 0
            else:
                contributor_obj = Contributor(contributor['author'])
                contributors_per_login[contributor_obj.login] = contributor_obj
                contributors_info.append(contributor_obj)
            for week in contributor['weeks']:
                contributor_obj.commits += week['c']
                contributor_obj.additions += week['a']
                contributor_obj.deletions += week['d']
            contributor_obj.delta = contributor_obj.additions + contributor_obj.deletions

        self.addContributors(contributors_info)

        return self.contributorsList

    def updateRiskyList(self):
        self.risky_commits = 0
        self.risky_additions = 0
        self.risky_deletions = 0
        self.risky_delta = 0
        self.risky_contributors_count = 0
        self.riskyContributorsList.clear()
        self.riskyAuthor = None

        for contributor in self.contributorsList:
            if contributor.riskRating < self.risk_boundary_value:
                continue
            self.risky_commits += contributor.commits
            self.risky_additions += contributor.additions
            self.risky_deletions += contributor.deletions
            self.risky_delta += contributor.delta
            self.risky_contributors_count += 1
            self.riskyContributorsList.append(contributor)
            if contributor.login == self.repo_author:
                self.riskyAuthor = contributor
        return

    def getJSON(self) -> Dict:
        result = self.__dict__.copy()

        result.pop('riskyContributorsList')
        result.pop('riskyAuthor')

        contributorsList = []
        for contributor in self.contributorsList:
            contributorsList.append(contributor.getJSON())
        result['contributorsList'] = contributorsList

        return result

    def getRiskyJSON(self) -> Dict:
        result = self.__dict__.copy()

        result.pop('contributorsList')
        result.pop('riskyAuthor')

        riskyContributorsList = []
        for contributor in self.riskyContributorsList:
            riskyContributorsList.append(contributor.getJSON())
        result['riskyContributorsList'] = riskyContributorsList

        return result
