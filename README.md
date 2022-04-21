# Risky Code Hunter
Get rid of toxic code!

---

## Description
Current package can be used to identify risky contributors 
into some repositories. All info about contributors are
gathered through official GitHub API and solely based only
on info that was leaved on GH by users. Currently you can 
provide your very own config with own rulesets. Or use our
config purely to see how our package performs.

To begin work with this packages, firstly, you need to create
and provide GitHub token. 
[Here is description](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
on how to create it. For your security we recommend creating 
a separate token for our program without any security
permissions. 

## Configuration file
Configuration file must be with `*.json` extension. And contain
only JSON dictionary.
Variables, that are used in config file:
### Root
| Variable                 | Type         | Description                                                                                                                                                                                  | 
|--------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `risk_boundary_value`    | `float`      | Used in RiskyRepo. Sets boundary value, which helps us to define whether should we consider contributor as risky one or not. It compares `Contributor.riskRating` value with boundary value. |
| `git_token`              | `str`        | Your GitHub token as string.                                                                                                                                                                 |
| `github_min_await`       | `float`      | Opyional. Default `5.0`. Minimum await time (in seconds) while GitHubAPI responds with timeouts.                                                                                             |
| `github_max_await`       | `float`      | Optional. Default `15.0`. Maximum await time (in seconds) while GitHubAPI responds with timeouts.                                                                                            |
| `auth_token_max_retries` | `int`        | Optional. Default `5`. Shows how many times we should try to reconnect to users GitHub token.                                                                                                |
| `fields`                 | `List[Dict]` | List of fields with rules. More detailed about this variable in the next section.                                                                                                            |


### Fields
| Variable | Type         | Description                                                                                                                                                                           | 
|----------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`   | `str`        | Must be the same as property name in `Contributor` class. Otherwise nothing would happen. In case of success it pulls data from variable in `Contributor` class and operates with it. |
| `rules`  | `List[Dict]` | List of rules that would append onto data gathered from `name` variable from `Contributor` class.                                                                                     |
#### Rules
| Variable     | Type        | Description                                                                                                                                                                               | 
|--------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `triggers`   | `List[str]` | Currently this is a list of strings. Program takes data (strings) from contributor class. Modifies it to lowercase string. And then checks if data from contributor matches every trigger. |
| `type`       | `str`       | String-name what can help user to understand what type of rule has been detected (e.g `Strong`, `Considerable`, `Weak`, etc.).                                                            |
| `risk_value` | `float`     | This value accumulates to `Contributor.riskRating` variable. Also can be negative one for some extra cases.                                                                               |

# Main Classses
###### All classes and methods that was not mentioned in this file - shouldn't be used by users. 
## RiskyCodeHunter class
### Variables
| Variable          | Type              | Description                                                                                          | 
|-------------------|-------------------|------------------------------------------------------------------------------------------------------|
| `risky_repo_list` | `List[RiskyRepo]` | List of all `RiskyRepo` class objects that were or processing right now in `RiskyCodeHunter` object. |
| `myGithubApi`     | `MyGithubApi`     | Object of `MyGithubApi` class, that was created in `RiskyCodeHunter` constructor.                    |
| `config`          | `Dict`            | Configuration that was provided via `*.json` file. Stores as python `Dict` object.                   |
### Methods
| Method                                             | Return Type                    | Description                                                                                                                                                                                                                                    |
|----------------------------------------------------|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `async checkAuthToken()`                           | `bool`                         | Check github auth token, that has been provided into `RiskyCodeHunter` class.                                                                                                                                                                  |
| `async scanRepo( repo_url: str )`                  | `Tuple[bool, RiskyRepo]`       | Scan GitHub repository via provided URL. Can throw Exceptions that needed to be handled.                                                                                                                                                       |
| `async scanRepos( repos_url_list: Iterable[str] )` | `List[Tuple[bool, RiskyRepo]]` | Scan several GitHub repositories simultaneously. Will await untill every repo would get scanned or throw an exception. Also suppresses all exceptions from internal scanning to not interfere with other scans. Should not return an Exception |

## RiskyRepo
### Variables
| Variable                   | Type                | Description                                                                                                     |
|----------------------------|---------------------|-----------------------------------------------------------------------------------------------------------------|
| `repo_author`              | `str`               | Repository author's login.                                                                                      |
| `repo_name`                | `str`               | Repository name.                                                                                                |
| `commits`                  | `int`               | Total commits count into repository made by contributors.                                                       |
| `additions`                | `int`               | Total line additions made to the code by contributors.                                                          |
| `deletions`                | `int`               | Total line deletions made to the code by contributors.                                                          |
| `delta`                    | `int`               | Sum of total additions and deletions made to the code by contributors.                                          |
| `contributors_count`       | `int`               | Total number of contributors that are going to be checked.                                                      |
| `risky_commits`            | `int`               | Total commits count into repository made by risky contributors.                                                 |
| `risky_additions`          | `int`               | Total line additions made to the code by risky contributors.                                                    |
| `risky_deletions`          | `int`               | Total line deletions made to the code by risky contributors.                                                    |
| `risky_delta`              | `int`               | Sum of total additions and deletions made to the code by risky contributors.                                    |
| `risky_contributors_count` | `int`               | Total number of risky contributors that has been checked.                                                       |
| `contributorsList`         | `List[Contributor]` | List of contributors that are objects of `Contributor` class that are going to be/was processed by the program. |
| `riskyContributorsList`    | `List[Contributor]` | List of risky contributors that are objects of `Contributor` class that was processed by the program.           |
| `riskyAuthor`              | `Contributor`       | If repository author is risky, then this value is not None.                                                     |
| `risk_boundary_value`      | `float`             | Boundary value that filters contributors on risky and not risky ones.                                           |
### Methods
| Method               | Return Type | Description                                                                                                                                                                              |
|----------------------|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `updateRiskyList()`  | `None`      | Recalculates all risky values based on `self.risk_boundary_value`.                                                                                                                       |
| `printShortReport()` | `None`      | Prints short report (only counts and ratio). And if author is risky - his description.                                                                                                   |
| `printFullReport()`  | `None`      | Prints info about every contributor and short report in the end.                                                                                                                         |
| `getShortReport()`   | `str`       | Returns same info as `printShortReport()` in `str` type value and without printing it.                                                                                                   |
| `getFullReport()`    | `str`       | Returns same info as `printFullReport()` in `str` type value and without printing it.                                                                                                    |
| `getJSON()`          | `Dict`      | Returns `json` info about `RiskyRepo` object variables. Generated safely, so user can modify it without consequences. Don't stores info about `riskyContributorsList` and `riskyAuthor`. |
| `getRiskyJSON()`     | `Dict`      | Returns `json` info about `RiskyRepo` object variables. Generated safely, so user can modify it without consequences. Don't stores info about `contributorsList` and `riskyAuthor`.      |

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
### Methods
| Method       | Return Type | Description                                                                                                               |
|--------------|-------------|---------------------------------------------------------------------------------------------------------------------------|
| `getPrint()` | `str`       | Generates human readable description based on object's variables.                                                         |
| `getJSON()`  | `Dict`      | Returns `json` info about `TriggeredRule` object variables. Generated safely, so user can modify it without consequences. |


# Installation

In order to work with this package you will need to have python3.6+ on your host system.
Currently, this package can be installed via pip several ways:
- like this:
```
pip3 install https://github.com/cossacklabs/risky-code-hunter/archive/master.zip 
```
- or like this:
```
pip3 install git+https://github.com/cossacklabs/risky-code-hunter.git@master 
```

# Usage
To use our package in CLI mode you will need create file 
with GitHub token in it (in order to not leave your security
token in cmd/terminal history). Or create own configuration
with your very own rules in it (also you can specify your 
GotHub security token in that configuration file).
Example of usage in CLI:
```
 python -m risky_code_hunter --url https://github.com/yandex/yandex-tank --tokenfile token_file
```
or
```
python -m risky_code_hunter --url https://github.com/yandex/yandex-tank --config config_file
```

Also you can work with our program as package. [Example is here](https://github.com/cossacklabs/risky-code-hunter/blob/main/examples/example.py).

# License
"Risky Code Hunter" is distributed under the terms of the Apache License (Version 2.0). See license folder for details.