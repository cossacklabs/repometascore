import asyncio
import argparse
import json
import os
import time
from typing import List, Tuple

from risky_code_hunter.RiskyCodeHunter import RiskyCodeHunter
from risky_code_hunter.RiskyRepo import Repo


async def main():
    parser = argparse.ArgumentParser(
        description=
        'Processing GitHub repositories and showing risky contributors.\n'
        'Our GitHub repo: https://github.com/cossacklabs/risky-code-hunter'
    )
    group_repos = parser.add_mutually_exclusive_group(required=True)
    group_configuration = parser.add_mutually_exclusive_group(required=True)
    group_output = parser.add_argument_group()
    group_repos.add_argument('--url', metavar='URL', type=str, nargs='*',
                             help='an url or list of urls to repos that needs to be checked')
    group_repos.add_argument('--urlfile', metavar='URL_FILE', type=str, action='store',
                             help='file with list of urls to repos that needs to be checked')
    group_configuration.add_argument('--config', metavar='CONFIG_PATH', type=str, action='store',
                       default=os.path.join(os.path.dirname(__file__), 'data/config.json'),
                       help='path to configuration file')
    group_configuration.add_argument('--tokenfile', metavar='GIT_TOKEN_FILE', type=str, action='store',
                       help='file with your github token in it')
    group_output.add_argument('--outputType', metavar='OUTPUT_TYPE', type=str, action='store',
                              choices=['human', 'json'], default='human',
                              help="output type. Can be either 'human' or 'json'. 'human' by default")
    group_output.add_argument('--outputfile', metavar='OUTPUT_FILE', type=str, action='store',
                              help='path to output file')
    group_output.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()

    git_token = None
    if args.tokenfile:
        try:
            with open(args.tokenfile) as token_file:
                git_token = token_file.readline().strip()
        except FileNotFoundError:
            raise Exception("Wrong token file has been provided!")

    if args.urlfile:
        try:
            args.url = []
            with open(args.urlfile) as url_file:
                for line in url_file:
                    line = line.strip()
                    if line:
                        args.url.append(line.strip())
        except FileNotFoundError:
            raise Exception("Wrong file with urls has been provided!")

    riskyCodeHunter = RiskyCodeHunter(config=args.config, git_token=git_token)

    reposResultList: List[Tuple[bool, Repo]]

    start_time = time.time()
    reposResultList = []
    if args.url:
        reposResultList = await riskyCodeHunter.scanRepos(args.url)
    else:
        raise Exception("No URLs were provided!")
    end_time = time.time()

    json_output = []
    str_result = []
    separator = '=' * 40
    print("Got result from the program. Processing output!")
    print(separator)
    for is_success, repoResult in reposResultList:
        if is_success is True:
            repo_output = repoResult.getVerboseOutput(verbose_level=args.verbose, output_type=args.outputType)
            if args.outputType == 'human':
                if args.outputfile:
                    str_result.append(repo_output)
                    str_result.extend(separator for _ in range(1 + args.verbose))
                else:
                    print(repo_output)
                    print("\n".join([separator for _ in range(1 + args.verbose)]))
            elif args.outputType == 'json':
                json_output.append(repo_output)
        else:
            raise Exception("Some error occurred while scanning repo. Sorry.")

    if args.outputType == 'json':
        if args.outputfile:
            str_result.append(json.dumps(json_output, indent=4))
        else:
            print(json.dumps(json_output, indent=4))

    if args.outputfile:
        try:
            with open(args.outputfile, "w") as out_file:
                out_file.write("\n".join(str_result))
        except Exception as err:
            print("\n".join(str_result))
            print(err)

    print(f"--- {end_time - start_time} seconds ---")

    await riskyCodeHunter.close()
    return


if __name__ == '__main__':
    asyncio.run(main())
