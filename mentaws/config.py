import platform
import getpass

config = {
    "default_duration_seconds": 14400,
    "default_region": "ap-southeast-1",
    "default_app_name": "sementara",
    "default_table_name": "creds",
    "database_file": "sementara.db",
    "creds_file_name": "credentials",
    "encryption_key_name": "encryption_key",
    "config_file_name": "config", # AWS config name
    "Darwin": {
        "aws_directory": "/Users/{user_name}/.aws",
    },
    "Windows": {
        "aws_directory": "C:\\Users\\{user_name}\\.aws\\"
    }
}

welcome_message = """
Welcome to mentaws ⌛. 
A cli-tool that encrypts your aws credentials file, and replaces it with temporary tokens from sts. 

Usage   : mentaws <command> <args>

Commands: setup           first time setup
          refresh         refresh new STS tokens
          list            list all profiles currently encrypted by sementera
          remove          remove profile from active profiles

        """


def get_platform_config() -> dict:
    """
    Platform configuration refers to OS specific fields (e.g. location fo aws credentials file)
    :return: platform_config : dict of platform configurations (aws_directory, credentials file)
    """

    platform_config = config[
        platform.system()
    ]  # platform.system() is a built-in python functionality

    user_name = getpass.getuser()
    platform_config["aws_directory"] = platform_config["aws_directory"].format(
        user_name=user_name
    )

    for key in config.keys():
        if key not in ['Linux', 'Darwin', 'Java', 'Windows']:
            platform_config[key] = config[key]

    return platform_config
