import requests
import json


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

    return repo_author + '/' + repo_name


def get_repo_author(repo_url):
    repo_name = repo_url.lstrip("https://")
    repo_name = repo_name.lstrip("http://")

    repo_name = repo_name[repo_name.find('/') + 1:]
    repo_author = repo_name[:repo_name.find('/')]
    return repo_author


def main():
    repo_url = 'https://api.github.com/MHProDev/MHDDoS'
    repo_name = get_repo_name(repo_url)
    repo_author = get_repo_author(repo_url)
    auth_token = ('github_username', 'ghp_token')

    total_commits = 0
    total_delta = 0

    malicious_commits = 0
    malicious_delta = 0

    response = requests.get(
        url=f"https://api.github.com/repos/{repo_name}/stats/contributors",
        auth=auth_token
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
        contributor_temp['deletetions'] = delete_count
        contributor_temp['delta'] = add_count + delete_count

        contributors_info.append(contributor_temp)

    contributors_info = sorted(contributors_info, key=lambda key: (key['commits'], key['delta']), reverse=True)
    contributors_json.clear()

    for contributor in contributors_info:
        total_commits += contributor['commits']
        total_delta += contributor['delta']

        response = requests.get(
            url=contributor['url'],
            auth=auth_token
        )
        user_json = json.loads(response.text)

        location = user_json['location']
        if location:
            contributor['location'] = location

        email = user_json['email']
        if email:
            contributor['email'] = email

        login = user_json['login']

        twitter_username = user_json['twitter_username']
        if twitter_username:
            contributor['twitter'] = twitter_username

        name = user_json['name']
        if name:
            contributor['name'] = name

        company = user_json['company']
        if company:
            contributor['company'] = company

        if location:
            location_lower = location.lower()
            if "russia" in location_lower or "россия" in location_lower or "rossiya" in location_lower:
                print('Strong russian signature! Location is set on russia!')
                print(location)
                contributor['triggered'] = 1
            elif "rus" in location_lower or "ros" in location_lower or "ru" in location_lower \
                    or "ру" in location_lower or 'rf' in location_lower or 'рф' in location_lower:
                print('Weak signature in location (rus/ros/ru/rf/ру/рф)')
                print(location)
                contributor['triggered'] = 1

        if email:
            email_lower = email.lower()
            mail_domain = email_lower[email_lower.find('@') + 1:]
            if 'mail.ru' in email_lower or 'yandex' in email_lower \
                or 'russia' in email_lower or 'rossiya' in email_lower \
                or 'rambler' in email_lower:
                print("Strong russian signature was found in email!")
                print(email)
                contributor['triggered'] = 1
            elif mail_domain in russian_mail_domains:
                print("Strong russian signature was found in email! Russian mail service!")
                print(email)
                contributor['triggered'] = 1
            elif mail_domain[:-3] == '.ru' or '.ru.' in mail_domain \
                or mail_domain[:-3] == '.rf' or '.rf.' in mail_domain \
                or mail_domain[:-3] == '.рф' or '.рф.' in mail_domain:
                print("Considerable russian signature was found in email. Russian domain is here!")
                print(email)
                contributor['triggered'] = 1

        if login:
            login_lower = login.lower()
            if 'russia' in login_lower or 'rossiya' in login_lower \
                    or 'rambler' in login_lower or 'yandex' in login_lower:
                print("Strong russian signature was found in login!")
                print(login)
                contributor['triggered'] = 1
            elif 'rus' in login_lower or 'ros' in login_lower or 'ru' in login_lower or 'rf' in login_lower:
                print('Weak signature in login (rus/ros/ru/rf)')
                print(login)
                contributor['triggered'] = 1

        if twitter_username:
            twitter_username_lower = twitter_username.lower()
            if 'russia' in twitter_username_lower or 'rossiya' in twitter_username_lower \
                    or 'rambler' in twitter_username_lower or 'yandex' in twitter_username_lower:
                print("Strong russian signature was found in twitter username!")
                print(twitter_username)
                contributor['triggered'] = 1
            elif 'rus' in twitter_username_lower or 'ros' in twitter_username_lower or 'ru' in twitter_username_lower \
                    or 'rf' in twitter_username_lower:
                print('Weak signature in twitter username (rus/ros/ru/rf)')
                print(twitter_username)
                contributor['triggered'] = 1

        if name:
            name_lower = name.lower()
            if 'russia' in name_lower or 'rossiya' in name_lower \
                    or 'rambler' in name_lower or 'yandex' in name_lower \
                    or 'россия' in name_lower:
                print("Strong russian signature was found in name!")
                print(name)
                contributor['triggered'] = 1
            elif "rus" in name_lower or "ros" in name_lower or "ru" in name_lower \
                    or "ру" in name_lower or 'rf' in name_lower or 'рф' in name_lower:
                print('Weak signature in name (rus/ros/ru/rf/ру/рф)')
                print(name)
                contributor['triggered'] = 1

        if company:
            company_lower = company.lower()
            if 'russia' in company_lower or 'rossiya' in company_lower \
                    or 'rambler' in company_lower or 'yandex' in company_lower \
                    or 'россия' in company_lower:
                print("Strong russian signature was found in company!")
                print(company)
                contributor['triggered'] = 1
            elif "rus" in company_lower or "ros" in company_lower or "ru" in company_lower \
                    or "ру" in company_lower or 'rf' in company_lower or 'рф' in company_lower:
                print('Weak signature in company (rus/ros/ru/rf/ру/рф)')
                print(company)
                contributor['triggered'] = 1

        if contributor.get('triggered'):
            malicious_commits += contributor['commits']
            malicious_delta += contributor['delta']

            print("That contributor triggered rules:")
            print(json.dumps(contributor, indent=4))
            print("=" * 40)

    print(f"Malicious commits count: {malicious_commits} \t Malicious delta count: {malicious_delta}")
    print(f"Total commits count: {total_commits} \t Total delta count: {total_delta}")
    print(
        f"Malicious commits ratio: {malicious_commits / total_commits} \t"
        f"Malicious delta ratio: {malicious_delta / total_delta}"
    )

    for contributor in contributors_info:
        if repo_author is not contributor['login']:
            continue
        if contributor.get('triggered'):
            print("="*40)
            print("Warning author of repo suspicious!")
            print(json.dumps(contributor, indent=4))

    return


if __name__ == '__main__':
    main()
