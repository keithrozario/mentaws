import platform
import getpass
import os

config = {
    "default_duration_seconds": 14400,
    "default_region": "ap-southeast-1",
    "default_app_name": "mentaws",
    "default_table_name": "creds",
    "database_file": "mentaws.db",
    "creds_file_name": "credentials",
    "encryption_key_name": "encryption_key",
    "config_file_name": "config",  # AWS config name
    "Darwin": {
        "aws_directory": "/Users/{user_name}/.aws",
    },
    "Linux": {
        "aws_directory": "/home/{user_name}/.aws",
    },
    "Windows": {
        "aws_directory": "{user_profile}\\.aws",
    },
}

welcome_message = """Welcome to mentaws!"""

help_message = """
usage: mentaws {setup,refresh,list,remove} [-p PROFILES]

Welcome to mentaws! ⏳

Commands:
  setup                 First time setup of mentaws.
  list                  List all available AWS profiles in mentaws
  refresh               Refreshes all AWS credentials in security file.
  remove                Permanently removes an AWS profile from mentaws.

optional arguments:
  -p, --profile         Comma-separate list of profiles to be actioned on

Example commands:
  mentaws setup
  mentaws list
  mentaws refresh
  mentaws refresh -p default
  mentaws refresh -p default,profile1,profile2
  mentaws remove -p default

"""

refresh_message = """
You're all fresh 😎
"""

unsetup_message = """So long, farewell, auf Wiedersehen, goodbye 😢"""


def get_platform_config() -> dict:
    """
    Platform configuration refers to OS specific fields (e.g. location fo aws credentials file)
    :return: platform_config : dict of platform configurations (aws_directory, credentials file)
    """

    platform_config = config[
        platform.system()
    ]  # platform.system() is a built-in python functionality

    if platform.system() == "Windows":
        platform_config["aws_directory"] = platform_config["aws_directory"].format(
            user_profile=os.environ["USERPROFILE"]
        )
    else:
        platform_config["aws_directory"] = platform_config["aws_directory"].format(
            user_name=getpass.getuser()
        )

    for key in config.keys():
        if key not in ["Linux", "Darwin", "Java", "Windows"]:
            platform_config[key] = config[key]

    return platform_config
