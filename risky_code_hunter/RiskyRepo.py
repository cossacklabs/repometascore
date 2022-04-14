import json
from typing import List

from .Contributor import Contributor


class RiskyRepo:
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

    # Border of which
    # We will determine if contributor
    # Is risky or not
    riskRatingBorder: float

    # Provide
    def __init__(self, repo_author, repo_name, config: dict = None):
        self.initialiseVariables()
        if not config:
            return
        self.repo_author = repo_author
        self.repo_name = repo_name
        self.riskRatingBorder = config.get('risk_border_value', 0.9)
        self.riskyContributorsList = []
        return

    def initialiseVariables(self):
        self.repo_author = str()
        self.repo_name = str()
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
        self.riskRatingBorder = float()

    # Will Only Add Risky Ones
    # Provide as input only after
    # Rules based check was applied
    def addContributor(self, contributor: Contributor):
        if type(contributor) is not Contributor:
            return

        self.commits += contributor.commits
        self.additions += contributor.additions
        self.deletions += contributor.deletions
        self.delta += contributor.delta
        self.contributors_count += 1
        self.contributorsList.append(contributor)

        if contributor.riskRating >= self.riskRatingBorder:
            self.risky_commits += contributor.commits
            self.risky_additions += contributor.additions
            self.risky_deletions += contributor.deletions
            self.risky_delta += contributor.delta
            self.risky_contributors_count += 1

            self.riskyContributorsList.append(contributor)
        return

    # Print Full Human-Readable report
    def printFullReport(self):
        for contributor in self.riskyContributorsList:
            if self.repo_author is contributor.login:
                continue
            print("That contributor triggered rules:")
            for triggeredRule in contributor.triggeredRules:
                print(triggeredRule.description)
            riskyDict = contributor.__dict__.copy()
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
            riskyDict = self.riskyAuthor.__dict__.copy()
            riskyDict.pop('triggeredRules', None)
            print(json.dumps(riskyDict, indent=4))
        return
