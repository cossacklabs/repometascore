from TCH import TCH
from RiskyRepo import RiskyRepo

def main():
    repo_url = 'https://github.com/yandex/yandex-tank'
    auth_token = 'ghp_token'

    toxicCodeHunter = TCH(repo_url, auth_token)
    toxicCodeHunter.checkAuthToken()

    repoResult: RiskyRepo = None
    boolResult, repoResult = toxicCodeHunter.scanRepo()
    if boolResult is True:
        repoResult.printFullReport()

    return


if __name__ == '__main__':
    main()
