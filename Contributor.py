from typing import List

from TriggeredRule import TriggeredRule


class Contributor:
    # main contributor arguments
    login: str = str()
    url: str = str()

    # details about commits in repo
    commits: int = int()
    additions: int = int()
    deletions: int = int()
    delta: int = int()

    # detailed info from profile
    location: str = str()
    emails: List[str]
    twitter_username: str = str()
    names: List[str]
    company: str = str()
    blog: str = str()
    bio: str = str()

    # risk rating
    # 0 - clear
    # n - risky
    riskRating: float = float()

    # List of human-readable descriptions
    # Why rule was triggered
    triggeredRulesDesc: List[str]
    triggeredRules: List[TriggeredRule]

    def __init__(self, input_dict=None):
        # Lol, need to explicitly create new list
        # otherwise it just copies pointers to list
        # and all objects of that class
        # would have accumulated triggeredRulesDesc list
        self.triggeredRulesDesc = []
        self.triggeredRules = []
        self.emails = []
        self.names = []
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

        # Maybe will insert these (triggered rules) values directly through object call
        '''
        self.triggeredRulesDesc = input_dict['triggeredRulesDesc'] \
            if input_dict.get('triggeredRulesDesc') and type(input_dict.get('triggeredRulesDesc')) is str and \
               input_dict.get('triggeredRulesDesc') is not str() else self.triggeredRulesDesc
        '''

        return
