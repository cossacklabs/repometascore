import asyncio
import sys
import argparse

from TCH import TCH
from RiskyRepo import RiskyRepo
import time


def main():
    parser = argparse.ArgumentParser(description='Process github repositories and showing risky contributors.')

    parser.add_argument('--url', metavar='URL', type=str, nargs=1, required=True,
                        help='an url to repo that needs to be checked')

    parser.add_argument('--config', metavar='CONFIG_PATH', type=str, nargs=1, required=True,
                        help='path to configuration file')

    parser.add_argument('--sync', action='store_true', default=False,
                        help='synchronous mode (default: async mode)')

    args = parser.parse_args()

    repo_url = args.url[0]
    config_path = args.config[0]
    sync_mode = args.sync

    toxicCodeHunter = TCH(repo_url, 'config.json')
    toxicCodeHunter.checkAuthToken()

    repoResult: RiskyRepo = None
    start_time = time.time()
    if sync_mode:
        boolResult, repoResult = toxicCodeHunter.scanRepo()
    else:
        boolResult, repoResult = asyncio.run(toxicCodeHunter.scanRepoAsync())
    if boolResult is True:
        repoResult.printFullReport()
    a = time.time() - start_time
    print(f"--- { time.time() - start_time } seconds ---")

    return


if __name__ == '__main__':
    main()
