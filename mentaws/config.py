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

refresh_message = """
You're all fresh 😎
"""

unsetup_message = """So long, farewell, auf Wiedersehen, goodbye 😢"""
setup_message = """mentaws successfully setup, run mentaws refresh to get fresh tokens"""
already_setup_message = "It looks like mentaws is already setup, use mentaws refresh or mentaws list"


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
