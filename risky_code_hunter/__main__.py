import asyncio
import argparse
import os
import time

from risky_code_hunter.RiskyCodeHunter import RiskyCodeHunter
from risky_code_hunter.RiskyRepo import RiskyRepo


def main():
    parser = argparse.ArgumentParser(
        description=
        'Processing GitHub repositories and showing risky contributors.\n'
        'Our GitHub repo: https://github.com/cossacklabs/risky-code-hunter'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--url', metavar='URL', type=str, action='store', required=True,
                        help='an url to repo that needs to be checked')
    group.add_argument('--config', metavar='CONFIG_PATH', type=str, action='store',
                       default=os.path.join(os.path.dirname(__file__), 'data/config.json'),
                       help='path to configuration file')
    group.add_argument('--tokenfile', metavar='GIT_TOKEN_FILE', type=str, action='store',
                       help='file with your github token in it')
    args = parser.parse_args()

    repo_url = None
    config_path = None
    git_token = None
    if args.url:
        repo_url = args.url
    else:
        raise Exception("No url has been provided!")
    if args.config:
        config_path = args.config
    else:
        raise Exception("No config file has been provided!")
    if args.tokenfile:
        try:
            with open(args.tokenfile) as token_file:
                git_token = token_file.readline()
        except FileNotFoundError:
            raise Exception("Wrong token file has been provided!")

    riskyCodeHunter = RiskyCodeHunter(repo_url, config=config_path, git_token=git_token)
    riskyCodeHunter.checkAuthToken()

    repoResult: RiskyRepo
    is_success: bool
    start_time = time.time()
    is_success, repoResult = asyncio.run(riskyCodeHunter.scanRepo())
    if is_success is True:
        repoResult.printFullReport()
    print(f"--- { time.time() - start_time } seconds ---")

    return


if __name__ == '__main__':
    main()
