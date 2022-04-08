import asyncio
import argparse
import time

from .RCH import RCH
from .RiskyRepo import RiskyRepo


def main():
    parser = argparse.ArgumentParser(description='Processing github repositories and showing risky contributors.')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--url', metavar='URL', type=str, nargs=1, required=True,
                        help='an url to repo that needs to be checked')
    group.add_argument('--config', metavar='CONFIG_PATH', type=str, nargs=1,
                       help='path to configuration file')
    group.add_argument('--token', metavar='GIT_TOKEN', type=str, nargs=1,
                       help='your github token')
    args = parser.parse_args()

    repo_url = args.url[0]
    config_path = None
    git_token = None
    if args.config:
        config_path = args.config[0]
    if args.token:
        git_token = args.token[0]

    riskyCodeHunter = RCH(repo_url, config=config_path, git_token=git_token)
    riskyCodeHunter.checkAuthToken()

    repoResult: RiskyRepo = None
    start_time = time.time()
    boolResult, repoResult = asyncio.run(riskyCodeHunter.scanRepo())
    if boolResult is True:
        repoResult.printFullReport()
    print(f"--- { time.time() - start_time } seconds ---")

    return


if __name__ == '__main__':
    main()
