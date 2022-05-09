# Risky Code Hunter

Detect risky code in your dependency chain.

---

## The main idea

This package helps to prevent supply chain risks by analyzing contributors in specific repositories. Nothing prevents open source project maintainers, especially from oppressed countries, from injecting malicious code and introducing backdoors.

Risky Code Hunter analyses the given repository collects information about its maintainers and contributors, and outputs the "risk rating". All info about contributors is collected through the official GitHub API, and other public sources, and is solely based on the information users provide in their accounts.

## How it works

You install the package, provide a link to a repository-in-question and check the output. The output contains risk ratings and info about each contributor. You decide whether to use the repository in your product.

The default configuration aims to detect repositories originating from Russia or being under the significant control of Russian citizens. Without making any statement about potential Russian malicious activity in open-source, this tool was built to mitigate the risks.

## Installation

Requirements: Debian, Ubuntu, Mac. Python 3.8+ installed.

Install Risky Code Hunter via pip:

```
pip3 install git+https://github.com/cossacklabs/risky-code-hunter.git@main 
```

or alternatively like zip:
```
pip3 install https://github.com/cossacklabs/risky-code-hunter/archive/main.zip 
```

## Usage

1. [Follow GitHub guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) to create new personal access token. We recommend creating a new, clean, token without any permissions.

2. Copy created token into a separate file, call it `token_file.txt`.

3. Run Risky Code Hunter with default config, point it to the repository-in-question and provide a path to your `token_file.txt`:

```
python3 -m risky_code_hunter --url https://github.com/yandex/yandex-tank --tokenfile token_file.txt
```

4. Also, there is a verbose parameter. It can be set with different levels. When nothing is set, the user will only get short output. To set the level of verbose output, you need to repeat the parameter several times. For example:
   - nothing 	- verbose with level 0. Output only risk level and percentage.
   - `-v`   	- verbose with level 1. Additionally to the ‘zero’ level, output info about the program and commits, code delta, and contributors risk ratio.
   - `-vv`  	- verbose with level 2. Additionally to the previous level, output info about every risky contributor.
   - `-vvv` 	- verbose with level 3. Additionally outputs info about every contributor. Currently, it only works with `JSON`-type output.

Enjoy the output and make decision whether to use this repository for your project.

## Customisation

You can create your own configuration with specific rules in it, and specific your GitHub security token in that configuration file.

1. Copy the default configuration file [config.json](https://github.com/cossacklabs/risky-code-hunter/blob/main/examples/config.json).

2. Update `git_token` value to have your GitHub token: `"git_token": "ghp_KvDv..."`

3. Run Risky Code Hunter with your config:

```
python3 -m risky_code_hunter --url https://github.com/yandex/yandex-tank --config config.json
```

---

## Configuration file

Configuration file should be a valid JSON file that contains a JSON dictionary.

Variables that are used in the config file:

### Root
| Variable              | Type         | Description                                                                                                                                                                             | 
|-----------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `risk_boundary_value` | `float`      | Used in Repo. Sets boundary value that helps us define whether we should consider contributors as risky or not. It compares the `Contributor.riskRating` value with the boundary value. |
| `git_token`           | `str`        | Your GitHub token as string.                                                                                                                                                            |
| `request_max_retries` | `int`        | Optional. Default `5`. It shows how often we should try to reconnect to some kinds of requests.                                                                                         |
| `request_min_await`   | `float`      | Optional. Default `5.0`. Minimum wait time (in seconds) when a remote server responds with timeouts.                                                                                    |
| `request_max_await`   | `float`      | Optional. Default `15.0`. Maximum wait time (in seconds) when a remote server responds with timeouts.                                                                                   |
| `fields`              | `List[Dict]` | List of fields with rules. More details about this variable are in the next section.                                                                                                    |

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
---

# License

"Risky Code Hunter" is distributed under the terms of the Apache License (Version 2.0).

This software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.


