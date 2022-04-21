import asyncio
import json

from risky_code_hunter.RiskyCodeHunter import RiskyCodeHunter
from risky_code_hunter.RiskyRepo import RiskyRepo
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

    repoResult: RiskyRepo
    is_success, repoResult = asyncio.run(riskyCodeHunter.scanRepo(repo_url))
    if is_success is True:
        repoResult.printFullReport()
    else:
        raise Exception("Some error occured while scanning repo. Sorry.")

    scanResults = asyncio.run(riskyCodeHunter.scanRepos(repo_url_list))
    risky_json = []
    for is_success, repoResult in scanResults:
        if is_success is True:
            risky_json.append(repoResult.getRiskyJSON())
    print(json.dumps(risky_json, indent=4))

    # All values in repoResult can be read, but not be written!
    print("All values in classes RiskyRepo, Contributor and TriggeredRule can be read, but not be written!")

    print(
        "RiskyRepo fields",
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
    for contributor in repoResult.contributorsList:
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
            f"Risk Rating: {contributor.riskRating}",
            f"Triggered Rules count: {len(contributor.triggeredRules)}"
        )
        triggeredRule: TriggeredRule
        for triggeredRule in contributor.triggeredRules:
            print(
                "Triggered Rule info",
                f"Type: {triggeredRule.type}",
                f"Field Name: {triggeredRule.fieldName}",
                f"Trigger: {triggeredRule.trigger}",
                f"Value (str from contributor that has triggered a rule): {triggeredRule.value}",
                f"Risk Value (risk rating of triggered rule): {triggeredRule.riskValue}",
                f"Description (human-readable): {triggeredRule.description}"
            )

    # Process through all risky contributors
    for contributor in repoResult.riskyContributorsList:
        # Process through all their triggered rules
        for triggeredRule in contributor.triggeredRules:
            # same as usual contributors
            continue

    # If repository author was considered as risky:
    if repoResult.riskyAuthor:
        print(
            "Main details:",
            f"Login: {repoResult.riskyAuthor.login}",
            f"Contributor GitHubAPI URL: {repoResult.riskyAuthor.url}",
            "=" * 12,
            "Details about commits in repo",
            f"Commits into scanned repo: {repoResult.riskyAuthor.commits}",
            f"Added lines into scanned repo: {repoResult.riskyAuthor.additions}",
            f"Deleted lines from scanned repo: {repoResult.riskyAuthor.deletions}",
            f"Accumulation of additions and deletions into scanned repo: {repoResult.riskyAuthor.delta}",
            "=" * 12,
            f"Location: {repoResult.riskyAuthor.location}",
            f"Emails: {repoResult.riskyAuthor.emails}",
            f"Twitter Username: {repoResult.riskyAuthor.twitter_username}",
            f"Names: {repoResult.riskyAuthor.names}",
            f"Company: {repoResult.riskyAuthor.company}",
            f"Blog: {repoResult.riskyAuthor.blog}",
            f"Bio: {repoResult.riskyAuthor.bio}",
            f"Risk Rating: {repoResult.riskyAuthor.riskRating}",
            f"Triggered Rules count: {len(repoResult.riskyAuthor.triggeredRules)}"
        )
        for triggeredRule in repoResult.riskyAuthor.triggeredRules:
            print(
                "Triggered Rule info",
                f"Type: {triggeredRule.type}",
                f"Field Name: {triggeredRule.fieldName}",
                f"Trigger: {triggeredRule.trigger}",
                f"Value (str from contributor that has triggered a rule): {triggeredRule.value}",
                f"Risk Value (risk rating of triggered rule): {triggeredRule.riskValue}",
                f"Description (human-readable): {triggeredRule.description}"
            )

    # You decided to change risk boundary value while running program

    # set new boundary value
    repoResult.risk_boundary_value = 2

    # recalculate repoResult risky values and risky contributors
    repoResult.updateRiskyList()

    # Use it
    # Process through all risky contributors
    for contributor in repoResult.riskyContributorsList:
        # Process through all their triggered rules
        for triggeredRule in contributor.triggeredRules:
            # same as usual contributors
            continue
    return


if __name__ == '__main__':
    main()
