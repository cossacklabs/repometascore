import json
import statistics
from typing import List, Dict, Tuple

from .Contributor import Contributor
from .RequestManager import RequestManager


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
    contributors_list: List[Contributor]
    # Risky contributors list
    risky_contributors_list: List[Contributor]
    risky_author: Contributor

    # Boundary value that helps us
    # to determine if contributor
    # Is risky or not
    risk_boundary_value: float

    # Provide
    def __init__(self, repo_author, repo_name, config: Dict = None):
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
        self.contributors_list = []
        self.risky_contributors_list = []
        self.risky_author = None
        self.risk_boundary_value = float()
        if not config:
            config = {}
        self.risk_boundary_value = config.get('risk_boundary_value', 0.9)
        return

    def add_contributor(self, contributor: Contributor):
        if not isinstance(contributor, Contributor):
            return
        self.commits += contributor.commits
        self.additions += contributor.additions
        self.deletions += contributor.deletions
        self.delta += contributor.delta
        self.contributors_count += 1
        self.contributors_list.append(contributor)
        return

    def add_contributors(self, contributors_list: List[Contributor]):
        for contributor in contributors_list:
            self.add_contributor(contributor)

    async def get_contributors_list(self, request_manager: RequestManager) -> List[Contributor]:
        contributors_info = []
        contributors_per_login = {}

        # get list of all contributors:
        # anonymous contributors are currently turned off
        contributors_json = await request_manager.github_api.get_repo_contributors(self.repo_author, self.repo_name)
        for contributor in contributors_json:
            contributor_obj = Contributor(contributor)
            contributors_info.append(contributor_obj)
            if contributor['type'] != "Anonymous":
                contributors_per_login[contributor_obj.login] = contributor_obj

        # get contributors with stats (only top100)
        contributors_json = await request_manager.github_api.get_repo_contributors_stats(
            self.repo_author, self.repo_name
        )
        for contributor in contributors_json:
            if contributors_per_login.get(contributor['author']['login']):
                contributor_obj = contributors_per_login.get(contributor['author']['login'])
                contributor_obj.add_value(contributor['author'])
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

        self.add_contributors(contributors_info)

        return self.contributors_list

    def update_risky_list(self):
        self.risky_commits = 0
        self.risky_additions = 0
        self.risky_deletions = 0
        self.risky_delta = 0
        self.risky_contributors_count = 0
        self.risky_contributors_list.clear()
        self.risky_author = None

        for contributor in self.contributors_list:
            if contributor.risk_rating < self.risk_boundary_value:
                continue
            self.risky_commits += contributor.commits
            self.risky_additions += contributor.additions
            self.risky_deletions += contributor.deletions
            self.risky_delta += contributor.delta
            self.risky_contributors_count += 1
            self.risky_contributors_list.append(contributor)
            if contributor.login == self.repo_author:
                self.risky_author = contributor
        return

    def get_verbose_output(self, verbose_level: int = 0, output_type: str = "human"):
        if not(isinstance(verbose_level, int) and isinstance(output_type, str)):
            raise Exception("Wrong parameter types!")
        if output_type.lower() == "json":
            if verbose_level == 0:
                return self.__get_very_short_json()
            elif verbose_level == 1:
                return self.__get_short_json()
            elif verbose_level == 2:
                return self.__get_risky_json()
            elif verbose_level >= 3:
                return self.get_json()
        elif output_type.lower() == "human":
            if verbose_level == 0:
                return self.__get_very_short_report()
            elif verbose_level == 1:
                return self.__get_short_report()
            elif verbose_level >= 2:
                return self.__get_full_report()

    def __get_commits_ratio(self) -> float:
        if self.commits <= 0:
            return 0
        return self.risky_commits / self.commits

    def __get_delta_ratio(self) -> float:
        if self.delta <= 0:
            return 0
        return self.risky_delta / self.delta

    def __get_contributors_ratio(self) -> float:
        if self.contributors_count <= 0:
            return 0
        return self.risky_contributors_count / self.contributors_count

    def __get_score(self) -> Tuple[float, str]:
        risky_score: float
        verbal_score: str
        arithmetic_mean_from = []
        if self.commits > 0:
            arithmetic_mean_from.append(self.__get_commits_ratio())
        if self.delta > 0:
            arithmetic_mean_from.append(self.__get_delta_ratio())
        if self.contributors_count > 0:
            arithmetic_mean_from.append(self.__get_contributors_ratio())

        if arithmetic_mean_from:
            risky_score = statistics.mean(arithmetic_mean_from)
        else:
            risky_score = 0

        # This operation can bring us to 100+ percentage
        # Thus we need to get minimum of our score and 100 percents
        if self.risky_author:
            risky_score *= 1.5

        risky_score *= 100
        risky_score = round(risky_score, 2)
        risky_score = min(risky_score, 100.0)

        if risky_score >= 90:
            verbal_score = "Ultra high"
        elif risky_score >= 80:
            verbal_score = "High"
        elif risky_score >= 40:
            verbal_score = "Medium"
        else:
            verbal_score = "Low"
        return risky_score, verbal_score

    # Print short human-readable report
    def __get_very_short_report(self) -> str:
        risky_score, verbal_score = self.__get_score()
        result = [
            f"Results of scanning https://github.com/{self.repo_author}/{self.repo_name}:",
            f"Risky score: {risky_score}%",
            f"{verbal_score} risk factor."
        ]
        return "\n".join(result)

    # Print short human-readable report
    def __get_short_report(self) -> str:
        risky_score, verbal_score = self.__get_score()

        commits_ratio = self.__get_commits_ratio()
        delta_ratio = self.__get_delta_ratio()

        result = [
            f"Results of scanning https://github.com/{self.repo_author}/{self.repo_name}:",
            f"Risky commits count: {self.risky_commits} \t Risky delta count: {self.risky_delta}",
            f"Total commits count: {self.commits} \t Total delta count: {self.delta}",
            f"Risky commits ratio: {commits_ratio} \t"
            f"Risky delta ratio: {delta_ratio}"
        ]
        if self.risky_author:
            result.append("Warning author of repo suspicious!")
        result.append(f"{self.risky_contributors_count}/{self.contributors_count} contributors are risky")
        result.append(f"Risky score: {risky_score}%")
        result.append(f"{verbal_score} risk factor.")
        return "\n".join(result)

    # Print Full Human-Readable report
    def __get_full_report(self) -> str:
        separator = '=' * 40
        result = [f"Results of scanning https://github.com/{self.repo_author}/{self.repo_name}:"]
        for contributor in self.risky_contributors_list:
            if self.repo_author is contributor.login:
                continue
            result.append("That contributor triggered rules:")
            for triggeredRule in contributor.triggered_rules:
                result.append(triggeredRule.description)
            risky_dict = contributor.get_json()
            risky_dict.pop('triggered_rules', None)
            result.append(json.dumps(risky_dict, indent=4))
            result.append(separator)
        result.append(self.__get_short_report())
        return "\n".join(result)

    def __get_very_short_json(self) -> Dict:
        risky_score, verbal_score = self.__get_score()
        result = {
            'repository': f"https://github.com/{self.repo_author}/{self.repo_name}",
            'risky_score': risky_score,
            'verbal_score': verbal_score
        }
        return result

    def __get_short_json(self) -> Dict:
        risky_score, verbal_score = self.__get_score()
        result = self.__dict__.copy()
        result['repository'] = f"https://github.com/{self.repo_author}/{self.repo_name}"
        result['risky_score'] = risky_score
        result['verbal_score'] = verbal_score
        result.pop('risky_contributors_list', None)
        result.pop('contributors_list', None)
        result.pop('risky_author', None)

        return result

    def __get_risky_json(self) -> Dict:
        risky_score, verbal_score = self.__get_score()
        result = self.__dict__.copy()
        result['repository'] = f"https://github.com/{self.repo_author}/{self.repo_name}"
        result['risky_score'] = risky_score
        result['verbal_score'] = verbal_score
        result.pop('contributors_list', None)
        result.pop('risky_author', None)

        risky_contributors_list = []
        for contributor in self.risky_contributors_list:
            risky_contributors_list.append(contributor.get_json())
        result['risky_contributors_list'] = risky_contributors_list

        return result

    def get_json(self) -> Dict:
        risky_score, verbal_score = self.__get_score()
        result = self.__dict__.copy()
        result['repository'] = f"https://github.com/{self.repo_author}/{self.repo_name}"
        result['risky_score'] = risky_score
        result['verbal_score'] = verbal_score
        result.pop('risky_contributors_list', None)
        result.pop('risky_author', None)

        contributors_list = []
        for contributor in self.contributors_list:
            contributors_list.append(contributor.get_json())
        result['contributors_list'] = contributors_list

        return result
