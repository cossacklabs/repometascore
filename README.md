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
| Variable                 | Type         | Description                                                                                                                                                        | 
|--------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `risk_border_value`      | `float`      | Used in RiskyRepo. Sets border value, which define whether consider contributor as risky one or not. It compares `Contributor.riskRating` value with border value. |
| `git_token`              | `str`        | Your GitHub token as string.                                                                                                                                       |
| `auth_token_max_retries` | `int`        | Shows how many times we should try to reconnect to users GitHub token.                                                                                             |
| `fields`                 | `List[Dict]` | List of fields with rules. More detailed about this variable in the next topic.                                                                                    |


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