import asyncio
import argparse
import time

from TCH import TCH
from RiskyRepo import RiskyRepo



def main():
    parser = argparse.ArgumentParser(description='Processing github repositories and showing risky contributors.')
    parser.add_argument('--url', metavar='URL', type=str, nargs=1, required=True,
                        help='an url to repo that needs to be checked')
    parser.add_argument('--config', metavar='CONFIG_PATH', type=str, nargs=1, required=True,
                        help='path to configuration file')
    args = parser.parse_args()

    repo_url = args.url[0]
    config_path = args.config[0]

    toxicCodeHunter = TCH(repo_url, config_path)
    toxicCodeHunter.checkAuthToken()

    repoResult: RiskyRepo = None
    start_time = time.time()
    boolResult, repoResult = asyncio.run(toxicCodeHunter.scanRepo())
    if boolResult is True:
        repoResult.printFullReport()
    print(f"--- { time.time() - start_time } seconds ---")

    return


if __name__ == '__main__':
    main()
