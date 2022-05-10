import asyncio
import json

from risky_code_hunter.RiskyCodeHunter import RiskyCodeHunter
from risky_code_hunter.RiskyRepo import Repo
from risky_code_hunter.Contributor import Contributor
from risky_code_hunter.TriggeredRule import TriggeredRule


def main():
    repo_url = "https://github.com/yandex/yandex-tank"
    repo_url_list = [
        "https://github.com/JetBrains/kotlin",
        "https://github.com/yandex/yandex-tank"
    ]
    config_path = None
    git_token = "ghp_token"
    riskyCodeHunter = RiskyCodeHunter(config=config_path, git_token=git_token)
    riskyCodeHunter.checkAuthToken()

    repoResult: Repo
    is_success, repoResult = asyncio.run(riskyCodeHunter.scan_repo(repo_url))
    if is_success is True:
        repoResult.printFullReport()
    else:
        raise Exception("Some error occured while scanning repo. Sorry.")

    scanResults = asyncio.run(riskyCodeHunter.scan_repos(repo_url_list))
    risky_json = []
    for is_success, repoResult in scanResults:
        if is_success is True:
            risky_json.append(repoResult.__getRiskyJSON())
    print(json.dumps(risky_json, indent=4))

    # All values in repoResult can be read, but not be written!
    print("All values in classes Repo, Contributor and TriggeredRule can be read, but not be written!")

    print(
        "Repo fields",
        f"Repo author: {repoResult.repo_author}",
        f"Repo name: {repoResult.repo_name}",
        f"Details about commits in repo",
        f"Total commits: {repoResult.commits}",
        f"Total added lines into scanned repo: {repoResult.additions}",
        f"Total deleted lines from scanned repo: {repoResult.deletions}",
        f"Total accumulation of additions and deletions into scanned repo: {repoResult.delta}",
        f"Total contributors count: {repoResult.contributors_count}",
        f"Risky commits: {repoResult.risky_commits}",
        f"Risky added lines into scanned repo: {repoResult.risky_additions}",
        f"Risky deleted lines from scanned repo: {repoResult.risky_deletions}",
        f"Risky accumulation of additions and deletions into scanned repo: {repoResult.risky_delta}",
        f"Risky contributors count: {repoResult.risky_contributors_count}",
        f"Risk boundary value: {repoResult.risk_boundary_value}"
    )

    # Process through all contributors
    contributor: Contributor
    for contributor in repoResult.contributors_list:
        print(
            "Main details:",
            f"Login: {contributor.login}",
            f"Contributor GitHubAPI URL: {contributor.url}",
            "="*12,
            "Details about commits in repo",
            f"Commits into scanned repo: {contributor.commits}",
            f"Added lines into scanned repo: {contributor.additions}",
            f"Deleted lines from scanned repo: {contributor.deletions}",
            f"Accumulation of additions and deletions into scanned repo: {contributor.delta}",
            "="*12,
            f"Location: {contributor.location}",
            f"Emails: {contributor.emails}",
            f"Twitter Username: {contributor.twitter_username}",
            f"Names: {contributor.names}",
            f"Company: {contributor.company}",
            f"Blog: {contributor.blog}",
            f"Bio: {contributor.bio}",
            f"Risk Rating: {contributor.risk_rating}",
            f"Triggered Rules count: {len(contributor.triggered_rules)}"
        )
        triggeredRule: TriggeredRule
        for triggeredRule in contributor.triggered_rules:
            print(
                "Triggered Rule info",
                f"Type: {triggeredRule.type_verbal}",
                f"Field Name: {triggeredRule.field_name}",
                f"Trigger: {triggeredRule.trigger}",
                f"Value (str from contributor that has triggered a rule): {triggeredRule.value}",
                f"Risk Value (risk rating of triggered rule): {triggeredRule.risk_value}",
                f"Description (human-readable): {triggeredRule.description}"
            )

    # Process through all risky contributors
    for contributor in repoResult.risky_contributors_list:
        # Process through all their triggered rules
        for triggeredRule in contributor.triggered_rules:
            # same as usual contributors
            continue

    # If repository author was considered as risky:
    if repoResult.risky_author:
        print(
            "Main details:",
            f"Login: {repoResult.risky_author.login}",
            f"Contributor GitHubAPI URL: {repoResult.risky_author.url}",
            "=" * 12,
            "Details about commits in repo",
            f"Commits into scanned repo: {repoResult.risky_author.commits}",
            f"Added lines into scanned repo: {repoResult.risky_author.additions}",
            f"Deleted lines from scanned repo: {repoResult.risky_author.deletions}",
            f"Accumulation of additions and deletions into scanned repo: {repoResult.risky_author.delta}",
            "=" * 12,
            f"Location: {repoResult.risky_author.location}",
            f"Emails: {repoResult.risky_author.emails}",
            f"Twitter Username: {repoResult.risky_author.twitter_username}",
            f"Names: {repoResult.risky_author.names}",
            f"Company: {repoResult.risky_author.company}",
            f"Blog: {repoResult.risky_author.blog}",
            f"Bio: {repoResult.risky_author.bio}",
            f"Risk Rating: {repoResult.risky_author.risk_rating}",
            f"Triggered Rules count: {len(repoResult.risky_author.triggered_rules)}"
        )
        for triggeredRule in repoResult.risky_author.triggered_rules:
            print(
                "Triggered Rule info",
                f"Type: {triggeredRule.type_verbal}",
                f"Field Name: {triggeredRule.field_name}",
                f"Trigger: {triggeredRule.trigger}",
                f"Value (str from contributor that has triggered a rule): {triggeredRule.value}",
                f"Risk Value (risk rating of triggered rule): {triggeredRule.risk_value}",
                f"Description (human-readable): {triggeredRule.description}"
            )

    # You decided to change risk boundary value while running program

    # set new boundary value
    repoResult.risk_boundary_value = 2

    # recalculate repoResult risky values and risky contributors
    repoResult.update_risky_list()

    # Use it
    # Process through all risky contributors
    for contributor in repoResult.risky_contributors_list:
        # Process through all their triggered rules
        for triggeredRule in contributor.triggered_rules:
            # same as usual contributors
            continue
    return


if __name__ == '__main__':
    main()
