from typing import List


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
    email: List[str]
    twitter_username: str = str()
    name: List[str]
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

    def __init__(self, input_dict=None):
        # Lol, need to explicitly create new list
        # otherwise it just copies pointers to list
        # and all objects of that class
        # would have accumulated triggeredRulesDesc list
        self.triggeredRulesDesc = list()
        self.email = list()
        self.name = list()
        if input_dict:
            self.addValue(input_dict)
        return

    # Get some dict with values
    # If found interesting values
    # We would add them and rewrite
    # Old object values
    def addValue(self, input_dict: dict):
        # Check whether we have dict as input
        if type(input_dict) is not dict:
            return

        self.login = input_dict['login'] \
            if input_dict.get('login') and type(input_dict.get('login')) is str and \
               input_dict.get('login') is not str() else self.login

        self.url = input_dict['url'] \
            if input_dict.get('url') and type(input_dict.get('url')) is str and \
               input_dict.get('url') is not str() else self.url

        self.commits = input_dict['commits'] \
            if input_dict.get('commits') and type(input_dict.get('commits')) is int and \
               input_dict.get('commits') is not int() else self.commits

        self.additions = input_dict['additions'] \
            if input_dict.get('additions') and type(input_dict.get('additions')) is int and \
               input_dict.get('additions') is not int() else self.additions

        self.deletions = input_dict['deletions'] \
            if input_dict.get('deletions') and type(input_dict.get('deletions')) is int and \
               input_dict.get('deletions') is not int() else self.deletions

        self.delta = input_dict['delta'] \
            if input_dict.get('delta') and type(input_dict.get('delta')) is int and \
               input_dict.get('delta') is not int() else self.delta

        self.location = input_dict['location'] \
            if input_dict.get('location') and type(input_dict.get('location')) is str and \
               input_dict.get('location') is not str() else self.location

        email = input_dict['email'] \
            if input_dict.get('email') and type(input_dict.get('email')) is str and \
               input_dict.get('email') is not str() else None
        if email and email not in self.email:
            self.email.append(email)

        self.twitter_username = input_dict['twitter'] \
            if input_dict.get('twitter') and type(input_dict.get('twitter')) is str and \
               input_dict.get('twitter') is not str() else self.twitter_username

        self.twitter_username = input_dict['twitter_username'] \
            if input_dict.get('twitter_username') and type(input_dict.get('twitter_username')) is str and \
               input_dict.get('twitter_username') is not str() else self.twitter_username

        name = input_dict['name'] \
            if input_dict.get('name') and type(input_dict.get('name')) is str and \
               input_dict.get('name') is not str() else None
        if name and name not in self.name:
            self.name.append(name)

        self.company = input_dict['company'] \
            if input_dict.get('company') and type(input_dict.get('company')) is str and \
               input_dict.get('company') is not str() else self.company

        self.blog = input_dict['blog'] \
            if input_dict.get('blog') and type(input_dict.get('blog')) is str and \
               input_dict.get('blog') is not str() else self.blog

        self.bio = input_dict['bio'] \
            if input_dict.get('bio') and type(input_dict.get('bio')) is str and \
               input_dict.get('bio') is not str() else self.bio

        self.riskRating = input_dict['riskRating'] \
            if input_dict.get('riskRating') and type(input_dict.get('riskRating')) is float and \
               input_dict.get('riskRating') is not float() else self.riskRating

        # Maybe will insert these (triggered rules) values directly through object call
        '''
        self.triggeredRulesDesc = input_dict['triggeredRulesDesc'] \
            if input_dict.get('triggeredRulesDesc') and type(input_dict.get('triggeredRulesDesc')) is str and \
               input_dict.get('triggeredRulesDesc') is not str() else self.triggeredRulesDesc
        '''

        return
