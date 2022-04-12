import asyncio
from risky_code_hunter.RiskyCodeHunter import RiskyCodeHunter
from risky_code_hunter.RiskyRepo import RiskyRepo
from risky_code_hunter.Contributor import Contributor
from risky_code_hunter.TriggeredRule import TriggeredRule


def main():
    repo_url = "https://github.com/yandex/yandex-tank"
    config_path = None
    git_token = "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"
    riskyCodeHunter = RiskyCodeHunter(repo_url, config=config_path, git_token=git_token)
    riskyCodeHunter.checkAuthToken()

    repoResult: RiskyRepo = None
    boolResult, repoResult = asyncio.run(riskyCodeHunter.scanRepo())
    if boolResult is True:
        repoResult.printFullReport()

    # Process through all contributors
    for contributor in repoResult.contributorsList:
        continue

    # Process through all risky contributors
    for contributor in repoResult.riskyContributorsList:
        # Process through all their triggered rules
        for triggeredRule in contributor.triggeredRules:
            continue

    return


if __name__ == '__main__':
    main()
