import json

import requests
from typing import List

from RiskyRepo import RiskyRepo
from Contributor import Contributor


russian_mail_domains = [
    "rambler.ru"
    "lenta.ru",
    "autorambler.ru",
    "myrambler.ru",
    "ro.ru",
    "rambler.ua",
    "mail.ua",
    "mail.ru",
    "internet.ru",
    "bk.ru",
    "inbox.ru",
    "list.ru",
    "yandex.ru",
    "ya.ru"
]


def get_repo_name(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_name = repo_name[repo_name.find('/') + 1:]
    repo_author = repo_name[:repo_name.find('/')]
    repo_name = repo_name[repo_name.find('/') + 1:]
    if repo_name.find('/') > 0:
        repo_name = repo_name[:repo_name.find('/')]

    return repo_name


def get_repo_author(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_name = repo_name[repo_name.find('/') + 1:]
    repo_author = repo_name[:repo_name.find('/')]
    return repo_author


class TCH:
    repo_author: str = str()
    repo_name: str = str()
    auth_token: str = str()
    auth_token_check: bool = False

    def __init__(self, repo_url, gth_token):
        self.repo_author = get_repo_author(repo_url)
        self.repo_name = get_repo_name(repo_url)
        self.auth_token = f"token {gth_token}"

    def checkAuthToken(self):
        print("Checking Auth Token")

        resp = requests.get(
            url='https://api.github.com',
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )

        if resp.status_code == 401:
            print("Token is not valid!")
            raise Exception("Your github token is not valid. Github returned err validation code!")
        elif resp.status_code == 200:
            print("Auth Token is valid!")
            self.auth_token_check = True
            return True

        print("Some error occured while requesting github api")
        self.auth_token_check = False
        return False

    def scanRepo(self):
        retries_count = 0
        while not self.auth_token_check and retries_count < 5:
            self.checkAuthToken()
            retries_count += 1
            if not self.auth_token_check:
                print(f"Retry one more time! Try count: {retries_count}")
        retries_count = 0

        if not self.auth_token_check:
            return False, None

        repo_result = RiskyRepo(
            self.repo_author,
            self.repo_name,
            {'riskRatingBorder': 1}
        )

        contributors: List[Contributor] = list()
        contributors = self.getContributorsList()
        for contributor in contributors:
            contributor = self.getContributorInfo(contributor)
            contributor = self.checkContributor(contributor)
            repo_result.addContributor(contributor)

        return True, repo_result

    def getContributorsList(self):
        response = requests.get(
            url=f"https://api.github.com/repos/{self.repo_author}/{self.repo_name}/stats/contributors",
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )

        contributors_json = json.loads(response.text)
        contributors_info = list()

        for contributor in contributors_json:
            contributor_temp = dict()
            contributor_temp['login'] = contributor['author']['login']
            contributor_temp['url'] = contributor['author']['url']
            commits_count = 0
            add_count = 0
            delete_count = 0
            for week in contributor['weeks']:
                commits_count += week['c']
                add_count += week['a']
                delete_count += week['d']
            contributor_temp['commits'] = commits_count
            contributor_temp['additions'] = add_count
            contributor_temp['deletions'] = delete_count
            contributor_temp['delta'] = add_count + delete_count

            contributor = Contributor(contributor_temp)

            contributors_info.append(contributor)

        contributors_info = sorted(contributors_info, key=lambda key: (key.commits, key.delta), reverse=True)
        contributors_json.clear()
        return contributors_info

    def getContributorInfo(self, contributor: Contributor):
        response = requests.get(
            url=contributor.url,
            headers={
                'Authorization': self.auth_token,
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        contributor.addValue(json.loads(response.text))

        return contributor

    def checkContributor(self, contributor):
        location_lower = contributor.location.lower()
        if "russia" in location_lower or "россия" in location_lower or "rossiya" in location_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Location: {contributor.location}")
            contributor.riskRating += 1.0
        elif "rus" in location_lower or "ros" in location_lower or "ru" in location_lower \
                or "ру" in location_lower or 'rf' in location_lower or 'рф' in location_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Location. Rule (rus/ros/ru/rf/ру/рф): {contributor.location}")
            contributor.riskRating += 1.0

        email_lower = contributor.email.lower()
        mail_domain = email_lower[email_lower.find('@') + 1:]
        if 'mail.ru' in email_lower or 'yandex' in email_lower \
                or 'russia' in email_lower or 'rossiya' in email_lower \
                or 'rambler' in email_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Email: {contributor.email}")
            contributor.riskRating += 1.0
        elif mail_domain in russian_mail_domains:
            contributor.triggeredRulesDesc.append(f"Strong. Email. Rule russian mail service: {contributor.email}")
            contributor.riskRating += 1.0
        elif mail_domain[:-3] == '.ru' or '.ru.' in mail_domain \
                or mail_domain[:-3] == '.rf' or '.rf.' in mail_domain \
                or mail_domain[:-3] == '.рф' or '.рф.' in mail_domain:
            contributor.triggeredRulesDesc.append(f"Considerable. Email. Rule russian mail service: {contributor.email}")
            contributor.riskRating += 1.0

        login_lower = contributor.login.lower()
        if 'russia' in login_lower or 'rossiya' in login_lower \
                or 'rambler' in login_lower or 'yandex' in login_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Login: {contributor.login}")
            contributor.riskRating += 1.0
        elif 'rus' in login_lower or 'ros' in login_lower or 'ru' in login_lower or 'rf' in login_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Login. Rule (rus/ros/ru/rf): {contributor.login}")
            contributor.riskRating += 1.0

        twitter_username_lower = contributor.twitter_username.lower()
        if 'russia' in twitter_username_lower or 'rossiya' in twitter_username_lower \
                or 'rambler' in twitter_username_lower or 'yandex' in twitter_username_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Twitter username: {contributor.twitter_username}")
            contributor.riskRating += 1.0
        elif 'rus' in twitter_username_lower or 'ros' in twitter_username_lower or 'ru' in twitter_username_lower \
                or 'rf' in twitter_username_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Twitter username. Rule (rus/ros/ru/rf): {contributor.twitter_username}")
            contributor.riskRating += 1.0

        name_lower = contributor.name.lower()
        if 'russia' in name_lower or 'rossiya' in name_lower \
                or 'rambler' in name_lower or 'yandex' in name_lower \
                or 'россия' in name_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Name: {contributor.name}")
            contributor.riskRating += 1.0
        elif "rus" in name_lower or "ros" in name_lower or "ru" in name_lower \
                or "ру" in name_lower or 'rf' in name_lower or 'рф' in name_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Name. Rule (rus/ros/ru/rf/ру/рф): {contributor.name}")
            contributor.riskRating += 1.0

        company_lower = contributor.company.lower()
        if 'russia' in company_lower or 'rossiya' in company_lower \
                or 'rambler' in company_lower or 'yandex' in company_lower \
                or 'россия' in company_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Company: {contributor.company}")
            contributor.riskRating += 1.0
        elif "rus" in company_lower or "ros" in company_lower or "ru" in company_lower \
                or "ру" in company_lower or 'rf' in company_lower or 'рф' in company_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Company. Rule (rus/ros/ru/rf/ру/рф): {contributor.company}")
            contributor.riskRating += 1.0

        blog_lower = contributor.blog.lower()
        if 'russia' in blog_lower or 'rossiya' in blog_lower \
                or 'rambler' in blog_lower or 'yandex' in blog_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Blog: {contributor.blog}")
            contributor.riskRating += 1.0
        elif "rus" in blog_lower or "ros" in blog_lower or "ru" in blog_lower \
                or 'rf' in blog_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Blog. Rule (rus/ros/ru/rf): {contributor.blog}")
            contributor.riskRating += 1.0

        bio_lower = contributor.bio.lower()
        if 'russia' in bio_lower or 'rossiya' in bio_lower \
                or 'rambler' in bio_lower or 'yandex' in bio_lower \
                or 'россия' in bio_lower:
            contributor.triggeredRulesDesc.append(f"Strong. Bio: {contributor.bio}")
            contributor.riskRating += 1.0
        elif "rus" in bio_lower or "ros" in bio_lower or "ru" in bio_lower \
                or "ру" in bio_lower or 'rf' in bio_lower or 'рф' in bio_lower:
            contributor.triggeredRulesDesc.append(f"Weak. Bio. Rule (rus/ros/ru/rf/ру/рф): {contributor.bio}")
            contributor.riskRating += 1.0

        return contributor