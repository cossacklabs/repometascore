import sys

from Contributor import Contributor
from TCH import TCH
from RiskyRepo import RiskyRepo
import time


def main():
    if len(sys.argv) < 3:
        print("You should provide url to github repository and your github token")
    repo_url = sys.argv[1]
    auth_token = sys.argv[2]

    toxicCodeHunter = TCH(repo_url, auth_token)
    toxicCodeHunter.checkAuthToken()

    repoResult: RiskyRepo = None
    start_time = time.time()
    boolResult, repoResult = toxicCodeHunter.scanRepo()
    if boolResult is True:
        repoResult.printFullReport()
    print("--- %s seconds ---" % (time.time() - start_time))

    return


if __name__ == '__main__':
    main()
