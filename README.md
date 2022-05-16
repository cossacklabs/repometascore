# RepoMetaScore

Use RepoMetaScore (repository metadata scoring) to find risky projects in your dependency chain.

![rch-github-logo](https://user-images.githubusercontent.com/2877920/167950182-7a436304-7480-4b8b-9492-35af4a7d7be6.png)

---

## The main idea

This package helps to prevent supply chain risks by analyzing _metadata_ about the repository and its contributors. 

Open-source maintainers weaponize their projects by introducing backdoors and vulnerabilities in the source code. Aside from being led by criminal and activist motivations, maintainers who live in regions with oppressive governments might be forced to introduce backdoors involuntarily. 

RepoMetaScore analyses the given repository, collects information about its maintainers and contributors, and outputs the "risk rating". All info about contributors is collected through the official GitHub API, and other public sources, and is solely based on the information users provide in their accounts.

## How it works

You install the package, provide a link to the repository-in-question and check the output. The output contains risk ratings and info about each contributor. You decide whether to use the repository in your product.

The default configuration uses a growing list of criteria to identify potentially problematic repositories: maintainers’ GitHub and Twitter profiles, location, commit history, email domain, etc. Use RepoMetaScore as a manual tool for one-time check, or change it to be a part of your CICD pipeline.

⚠️ _The configurations are rather raw and still work in progress. Feel free to contribute!_


## Installation

Requirements: Debian, Ubuntu, or Mac. Python 3.8+ installed.

Install RepoMetaScore via pip:

```
pip3 install git+https://github.com/cossacklabs/repometascore.git@release 
```

or alternatively as zip:
```
pip3 install https://github.com/cossacklabs/repometascore/archive/release.zip 
```

ℹ️ _In order to get latest stable, download product from `release` branch, to get latest working version, use `main` branch._


## Usage

1. [Follow GitHub guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) to create new personal access token. We recommend creating a new, clean, token without any permissions.

2. Copy created token into a separate file, call it `token_file.txt`. If you want to extend the limitation of requests to GitHub API - you can create additional tokens from the **OTHER** GitHub account. And add it in the next line to `token_file.txt` 

3. Run RepoMetaScore with default config, point it to the repository-in-question and provide a path to your `token_file.txt`:

```
python3 -m repometascore --url https://github.com/yandex/yandex-tank --tokenfile token_file.txt
```

4. The output is controlled by verbose parameter. By default, the verbose level is 0, which means the shortest output. To control verbosity, use `-v` param:
   - nothing 	- verbose with level 0. Output only risk level and percentage.
   - `-v`   	- verbose with level 1. Additionally to the ‘zero’ level, output info about the program and commits, code delta, and contributors risk ratio.
   - `-vv`  	- verbose with level 2. Additionally to the previous level, output info about every risky contributor.
   - `-vvv` 	- verbose with level 3. Additionally outputs info about every contributor. Currently, it only works with `JSON`-type output.
   - `-vvvv` 	- verbose with level 4. Additionally shows different log outputs of this program.

Enjoy the output and make decision whether to use this repository for your project.

## Customisation

You can create your own configuration with specific rules in it, and specific your GitHub security token in that configuration file.

1. Copy the default configuration file [config.json](https://github.com/cossacklabs/repometascore/blob/main/examples/config.json).

2. Update `git_token` value to have your GitHub token: `"git_token": "ghp_KvDv..."`

3. Run RepoMetaScore with your config:

```
python3 -m repometascore --url https://github.com/yandex/yandex-tank --config config.json
```

---

## Configuration file

Configuration file should be a valid JSON file that contains a JSON dictionary.

Variables that are used in the config file:

### Root
| Variable              | Type         | Description                                                                                                                                                                                                                             | 
|-----------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `risk_boundary_value` | `float`      | Optional. Default `0.95`. Used in Repo. Sets boundary value that helps us define whether we should consider contributors as risky or not. It compares the `Contributor.riskRating` value with the boundary value.                       |
| `git_tokens`          | `List[str]`  | Your GitHub tokens as a list of strings. If you want to extend the limitation of requests to GitHub API - you can create additional tokens from the **OTHER** GitHub account. And add it as next `str` variable into `git_tokens` list. |
| `request_max_retries` | `int`        | Optional. Default `5`. It shows how often we should try to reconnect to some kinds of requests.                                                                                                                                         |
| `request_min_await`   | `float`      | Optional. Default `5.0`. Minimum wait time (in seconds) when a remote server responds with timeouts.                                                                                                                                    |
| `request_max_await`   | `float`      | Optional. Default `15.0`. Maximum wait time (in seconds) when a remote server responds with timeouts.                                                                                                                                   |
| `fields`              | `List[Dict]` | List of fields with rules. More details about this variable are in the next section.                                                                                                                                                    |

### Fields
| Variable | Type         | Description                                                                                                                                                                                          | 
|----------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`   | `str`        | Must be the same as the property name in the `Contributor` class. Otherwise, nothing would happen. In case of success, it pulls data from variables in the `Contributor` class and operates with it. |
| `rules`  | `List[Dict]` | List of rules that would append onto data gathered from the `name` variable from the `Contributor` class.                                                                                            |
### Rules
| Variable     | Type        | Description                                                                                                                                                                                           | 
|--------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `triggers`   | `List[str]` | Currently this is a list of strings. The program takes data (strings) from the contributor class. Modifies it to a lowercase string. And then checks if data from contributors matches every trigger. |
| `type`       | `str`       | Verbose string name that can help the user understand what type of rule has been detected (e.g. `Strong`, `Considerable`, `Weak`, etc.).                                                              |
| `risk_value` | `float`     | This value accumulates to `Contributor.riskRating` variable. Also can be a negative one for some extra cases.                                                                                         |

## Environmental Variables
| Variable               | Type  | Description                                                                                                                                                                                                |
|------------------------|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `HTTP_REQUEST_TIMEOUT` | `int` | Optional. Default `20`. Time (in seconds) of an HTTP connection timeouts.                                                                                                                                  |
| `ALLOWED_TIME_TO_WAIT` | `int` | Optional. Default `12000`. Time (in seconds) shows how long should we wait for GitHub API token reset. If token reset time is longer than `ALLOWED_TIME_TO_WAIT` exception `NoTokensLeft` would be thrown. |

---

# Next steps

1. Improving location parsing & scores.
2. Adding more checks, improving dictionaries.
3. Adding risk factor based on comments language.
4. Adding checks inspired by [What are Weak Links in the npm Supply Chain?](https://arxiv.org/abs/2112.10165) paper.

---

# License

"RepoMetaScore" is distributed under the terms of the Apache License (Version 2.0).

This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

---

# Contributing

Feel free to extend the configuration, rules, scoring and come back with PRs. Also, we are welcome contributions that aimed at automation: add to CICD, add to GitHub plugins, etc. 

