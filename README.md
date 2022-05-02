# Risky Code Hunter

Detect risky code in your dependency chain.

---

## Description
The current package can be used to identify specific contributors in a repository, thus scoring it as risky. All information about contributors is collected through the official GitHub API and is solely based only on information users provided to the platform.

In the future, we might add more external data sources.

The current RCH configuration aims to detect repositories originating from Russia (or under significant control of Russian citizens) due to concerns about Russian-originating open-source products. Without making any statement about potential Russian malicious activity in open-source, this is what we use it for.

To begin working with these packages, firstly, you need to create and provide a GitHub token. [Here is description](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
on how to create it. We recommend creating 
a separate token for our program without any security
permissions for the sake of your security. 

## Configuration file
Configuration file must be with `*.json` extension. And contain
only JSON dictionary.
Variables that are used in the config file:
### Root
| Variable                 | Type         | Description                                                                                                                                                                             | 
|--------------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `risk_boundary_value`    | `float`      | Used in Repo. Sets boundary value that helps us define whether we should consider contributors as risky or not. It compares the `Contributor.riskRating` value with the boundary value. |
| `git_token`              | `str`        | Your GitHub token as string.                                                                                                                                                            |
| `auth_token_max_retries` | `int`        | Optional. Default `5`. It shows how often we should try to reconnect to the user’s GitHub token.                                                                                        |
| `github_min_await`       | `float`      | Optional. Default `5.0`. Minimum wait time (in seconds) while GitHubAPI responds with timeouts.                                                                                         |
| `github_max_await`       | `float`      | Optional. Default `15.0`. Maximum wait time (in seconds) while GitHubAPI responds with timeouts.                                                                                        |
| `fields`                 | `List[Dict]` | List of fields with rules. More details about this variable are in the next section.                                                                                                    |

### Fields
| Variable | Type         | Description                                                                                                                                                                                          | 
|----------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`   | `str`        | Must be the same as the property name in the `Contributor` class. Otherwise, nothing would happen. In case of success, it pulls data from variables in the `Contributor` class and operates with it. |
| `rules`  | `List[Dict]` | List of rules that would append onto data gathered from the `name` variable from the `Contributor` class.                                                                                            |
#### Rules
| Variable     | Type        | Description                                                                                                                                                                                           | 
|--------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `triggers`   | `List[str]` | Currently this is a list of strings. The program takes data (strings) from the contributor class. Modifies it to a lowercase string. And then checks if data from contributors matches every trigger. |
| `type`       | `str`       | Verbose string name that can help the user understand what type of rule has been detected (e.g. `Strong`, `Considerable`, `Weak`, etc.).                                                              |
| `risk_value` | `float`     | This value accumulates to `Contributor.riskRating` variable. Also can be a negative one for some extra cases.                                                                                         |
---
# Main Classes
###### All classes and methods that was not mentioned in this file - shouldn't be used by users. 
## RiskyCodeHunter class
### Variables
| Variable    | Type         | Description                                                                                     | 
|-------------|--------------|-------------------------------------------------------------------------------------------------|
| `repo_list` | `List[Repo]` | List of all `Repo` class objects that were or processing right now in `RiskyCodeHunter` object. |
| `githubApi` | `GithubApi`  | Object of `GithubApi` class, that was created in `RiskyCodeHunter` constructor.                 |
| `config`    | `Dict`       | Configuration that was provided via `*.json` file. Stores as python `Dict` object.              |
### Methods
| Method                                             | Return Type               | Description                                                                                                                                                                                                                                                         |
|----------------------------------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `async checkAuthToken()`                           | `bool`                    | Check GitHub auth token, that has been provided into `RiskyCodeHunter` class.                                                                                                                                                                                       |
| `async scanRepo( repo_url: str )`                  | `Tuple[bool, Repo]`       | Scan GitHub repository via provided URL. Can throw Exceptions that need to be handled.                                                                                                                                                                              |
| `async scanRepos( repos_url_list: Iterable[str] )` | `List[Tuple[bool, Repo]]` | Scan several GitHub repositories simultaneously. It will wait until every repo gets scanned or throw an exception. It also suppresses all exceptions from internal scanning to not interfere with other scans. Should not return an Exception except `Wrong token`. |

## Repo
### Variables
| Variable                   | Type                | Description                                                                                                 |
|----------------------------|---------------------|-------------------------------------------------------------------------------------------------------------|
| `repo_author`              | `str`               | Repository author's login.                                                                                  |
| `repo_name`                | `str`               | Repository name.                                                                                            |
| `commits`                  | `int`               | Total commits count into repository made by contributors.                                                   |
| `additions`                | `int`               | Total line additions made to the code by contributors.                                                      |
| `deletions`                | `int`               | Total line deletions made to the code by contributors.                                                      |
| `delta`                    | `int`               | Sum of contributors’ total additions and deletions made to the code.                                        |
| `contributors_count`       | `int`               | Total number of contributors that will be checked.                                                          |
| `risky_commits`            | `int`               | Total commits count into repository made by risky contributors.                                             |
| `risky_additions`          | `int`               | Total line additions made to the code by risky contributors.                                                |
| `risky_deletions`          | `int`               | Total line deletions made to the code by risky contributors.                                                |
| `risky_delta`              | `int`               | Sum of total additions and deletions made to the code by risky contributors.                                |
| `risky_contributors_count` | `int`               | Total number of risky contributors checked.                                                                 |
| `contributorsList`         | `List[Contributor]` | List of contributors that are objects of the `Contributor` class that will be/was processed by the program. |
| `riskyContributorsList`    | `List[Contributor]` | List of risky contributors that are objects of the `Contributor` class that was processed by the program.   |
| `riskyAuthor`              | `Contributor`       | If the repository author is risky, this value is not `None`.                                                |
| `risk_boundary_value`      | `float`             | Boundary value that filters contributors on risky and not risky ones.                                       |
### Methods
| Method               | Return Type | Description                                                                                                                                                                         |
|----------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `updateRiskyList()`  | `None`      | Recalculates all risky values based on `self.risk_boundary_value`.                                                                                                                  |
| `printShortReport()` | `None`      | Prints short report (only counts and ratio). And if author is risky - his description.                                                                                              |
| `printFullReport()`  | `None`      | Prints info about every contributor and short report in the end.                                                                                                                    |
| `getShortReport()`   | `str`       | Returns same info as `printShortReport()` in `str` type value and without printing it.                                                                                              |
| `getFullReport()`    | `str`       | Returns same info as `printFullReport()` in `str` type value and without printing it.                                                                                               |
| `getJSON()`          | `Dict`      | Returns `json` info about `Repo` object variables. Generated safely, so user can modify it without consequences. Don't stores info about `riskyContributorsList` and `riskyAuthor`. |
| `getRiskyJSON()`     | `Dict`      | Returns `json` info about `Repo` object variables. Generated safely, so user can modify it without consequences. Don't stores info about `contributorsList` and `riskyAuthor`.      |

## Contributor
### Variables
| Variable           | Type                  | Description                                                                                                                  |
|--------------------|-----------------------|------------------------------------------------------------------------------------------------------------------------------|
| `login`            | `str`                 | Contributor's login.                                                                                                         |
| `url`              | `str`                 | Contributor's url to GitHub API page.                                                                                        |
| `commits`          | `int`                 | Number of contributor's commits into specific repo.                                                                          |
| `additions`        | `int`                 | Number of contributor's additions into the code of specific repo.                                                            |
| `deletions`        | `int`                 | Number of contributor's deletions into the code of specific repo.                                                            |
| `delta`            | `int`                 | Sum of contributor's additions and deletions into the code of specific repo.                                                 |
| `location`         | `str`                 | Contributor's location from GitHub account.                                                                                  |
| `emails`           | `List[str]`           | Contributor's emails from GitHub page and commits info from specific repo.                                                   |
| `twitter_username` | `str`                 | Contributor's twitter username from GitHub account.                                                                          |
| `names`            | `List[str]`           | Contributor's names from GitHub account and commits info from specific repo.                                                 |
| `company`          | `str`                 | Contributor's location from GitHub account.                                                                                  |
| `blog`             | `str`                 | Contributor's blog url from GitHub account.                                                                                  |
| `bio`              | `str`                 | Contributor's bio from GitHub account.                                                                                       |
| `riskRating`       | `float`               | Contributor's risk rating based on sum triggered rules `riskValue`.                                                          |
| `triggeredRules`   | `List[TriggeredRule]` | Contributor's list of triggered rules based on config in `RiskyCodeHunter` and data from current `Contributor` class object. |
### Methods
| Method               | Return Type | Description                                                                                                             |
|----------------------|-------------|-------------------------------------------------------------------------------------------------------------------------|
| `getJSON()`          | `Dict`      | Returns `json` info about `Contributor` object variables. Generated safely, so user can modify it without consequences. |
# Secondary Classes
## TriggeredRule
### Variables
| Variable      | Type    | Description                                                                                                               |
|---------------|---------|---------------------------------------------------------------------------------------------------------------------------|
| `type`        | `str`   | Triggered Rule's human readable type (as of `Strong`, `Weak`, etc).                                                       |
| `fieldName`   | `str`   | `Contributor's` name of variable that triggered specific rule.                                                            |
| `trigger`     | `str`   | Specific trigger that was triggered by `Contributor's` data.                                                              |
| `value`       | `str`   | Data that triggered rule.                                                                                                 |
| `riskValue`   | `float` | Float score that would be summed to `Contributor.riskRating`.                                                             |
| `description` | `str`   | Human readable description of triggered rule. Generates automatically by `TriggeredRule.getPrint()` in class constructor. |
### Methods
| Method       | Return Type | Description                                                                                                               |
|--------------|-------------|---------------------------------------------------------------------------------------------------------------------------|
| `getPrint()` | `str`       | Generates human readable description based on object's variables.                                                         |
| `getJSON()`  | `Dict`      | Returns `json` info about `TriggeredRule` object variables. Generated safely, so user can modify it without consequences. |

---
# Installation

To work with this package, you will need to have python3.6+ on your host system.
Currently, this package can be installed via pip in several ways:
- like this (currently not working due to a hidden nature of the repository):
```
pip3 install https://github.com/cossacklabs/risky-code-hunter/archive/main.zip 
```
- or like this:
```
pip3 install git+https://github.com/cossacklabs/risky-code-hunter.git@main 
```

# Usage
To use our package in CLI mode, you will need to create a file 
with GitHub token in it (to not leave your security
token in cmd/terminal history).
```
 python -m risky_code_hunter --url https://github.com/yandex/yandex-tank --tokenfile token_file
```
Or create your configuration
with your very own rules in it (also, you can specify your 
GitHub security token in that configuration file).
```
python -m risky_code_hunter --url https://github.com/yandex/yandex-tank --config config_file
```

Also, you can work with our program as a package. [Example is here](https://github.com/cossacklabs/risky-code-hunter/blob/main/examples/example.py).

# License
"Risky Code Hunter" is distributed under the terms of the Apache License (Version 2.0). See the license folder for details.

