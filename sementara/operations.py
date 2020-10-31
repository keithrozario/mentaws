import platform
from configparser import ConfigParser
import getpass
import secrets
import base64
import json
import os

from .exceptions import InvalidPasswordError


def get_platform_config() -> dict:
    """
    :return: platform_config : dict of platform configurations (aws_directory, credentials file)
    """
    from .config import config

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


def load_conf_file(platform_config: dict) -> dict:
    "Return platform configuration"

    conf_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["conf_file_name"]
    )

    try:
        with open(conf_file_path, "r") as config_file:
            config = json.loads(config_file.read())
    except FileNotFoundError:
        raise FileNotFoundError
    return config


def load_profiles(platform_config: dict, profiles: list) -> dict:
    "Loads missing profiles into profile file"

    profile_details = {}
    prof_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["profile_file_name"]
    )
    with open(prof_file_path, "w") as prof_file:
        for profile in profiles:
            profile_details[profile] = {}
        prof_file.write(json.dumps(profile_details))

    return


def setup_conf_file(platform_config: dict) -> dict:

    conf_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["conf_file_name"]
    )

    salt = secrets.token_bytes(nbytes=32)
    salt_b64 = base64.b64encode(salt).decode("utf-8")

    config = {
        "salt": salt_b64,
        "default_duration_seconds": platform_config["default_duration_seconds"],
        "default_region": platform_config["default_region"],
    }

    with open(conf_file_path, "w") as config_file:
        config_file.write(json.dumps(config))

    return config


def write_creds_file(config: ConfigParser, platform_config: dict):

    creds_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    with open(creds_file_path, "w") as creds_file:
        config.write(creds_file)

    return


def decrypt_credentials(
    platform_config,
    config,
    password_prompt="🔑 Enter password: ",
    return_type: str = "ConfigParser",
):
    """

    :param platform_config: Platform configuration
    :param config: Sementara configuration
    :param password_prompt: Prompt for password configuration
    :param return_type: String specifying return values
    :return:
    """

    # Decrypt credentials file
    p = getpass.getpass(prompt=password_prompt)
    creds = ConfigParser()
    data = ""

    try:
        data = decrypt_creds_file(
            platform_config=platform_config, password=p, salt=config["salt"]
        )
        creds.read_string(data)
        load_profiles(platform_config, creds.sections())
    except InvalidPasswordError:
        print("🛑 Invalid password, exiting 🛑")
        exit(1)

    if return_type == "ConfigParser":
        return creds
    if return_type == "str":
        return data
    if return_type == "ConfigParserWithPassword":
        return creds, p
    if return_type == "strWithPassword":
        return data, p

    return creds


def check_new_profiles() -> dict:
    platform_config = get_platform_config()

    cred_file_path = os.path.join(platform_config["aws_directory"], "credentials")
    creds = ConfigParser()
    creds.read(filenames=[cred_file_path], encoding='utf-8')

    new_profiles = dict()
    for section in creds.sections():
        key_id = creds.get(section, "aws_access_key_id")
        if key_id[:4] == "AKIA":
            new_section = {}
            for option in creds.options(section):
                new_section[option] = creds.get(section, option)
            new_profiles[section] = new_section

    return new_profiles
