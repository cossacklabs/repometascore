import json
from typing import List
from Contributor import Contributor


class RiskyRepo:
    # Repo main info
    repo_author: str = str()
    repo_name: str = str()

    # details about commits in repo
    commits: int = int()
    additions: int = int()
    deletions: int = int()
    delta: int = int()
    contributors: int = int()

    # risky ones
    risky_commits: int = int()
    risky_additions: int = int()
    risky_deletions: int = int()
    risky_delta: int = int()
    risky_contributors: int = int()

    # Risky contributors list
    riskyContributorsList: List[Contributor]
    riskyAuthor: Contributor = None

    # Border of which
    # We will determine if contributor
    # Is risky or not
    riskRatingBorder: float = float()

    # Provide
    def __init__(self, repo_author, repo_name, config: dict = None):
        if not config:
            return
        self.repo_author = repo_author
        self.repo_name = repo_name
        self.riskRatingBorder = config.get('risk_border_value', 0.9)
        self.riskyContributorsList = []
        return

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
        self.contributors += 1

        if contributor.riskRating >= self.riskRatingBorder:
            self.risky_commits += contributor.commits
            self.risky_additions += contributor.additions
            self.risky_deletions += contributor.deletions
            self.risky_delta += contributor.delta
            self.risky_contributors += 1

            self.riskyContributorsList.append(contributor)
        return

    # Print Full Human-Readable report
    def printFullReport(self):
        for contributor in self.riskyContributorsList:
            if self.repo_author is contributor.login:
                continue
            print("That contributor triggered rules:")
            print("\n".join(contributor.triggeredRulesDesc))
            riskyDict = contributor.__dict__.copy()
            riskyDict.pop('triggeredRules', None)
            riskyDict.pop('triggeredRulesDesc', None)
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
        print(f"{self.risky_contributors}/{self.contributors} contributors are risky")

        if self.riskyAuthor:
            print("=" * 40)
            print("Warning author of repo suspicious!")
            print("That contributor triggered rules:")
            print("\n".join(self.riskyAuthor.triggeredRulesDesc))
            riskyDict = self.riskyAuthor.__dict__.copy()
            riskyDict.pop('triggeredRules', None)
            riskyDict.pop('triggeredRulesDesc', None)
            print(json.dumps(riskyDict, indent=4))
        return
