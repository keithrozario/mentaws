import platform
import getpass

config = {
    "default_duration_seconds": 14400,
    "default_region": "ap-southeast-1",
    "default_app_name": "sementara",
    "default_table_name": "creds",
    "Darwin": {
        "aws_directory": "/Users/{user_name}/.aws",
        "database_file": "sementara.db",
        "creds_file_name": "credentials",
        "config_file_name": "config",
        "encryption_key_name": "encryption_key"
    },
}

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
        if key.startswith("default"):
            platform_config[key] = config[key]

    return platform_config