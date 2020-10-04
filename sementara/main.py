import getpass
import configparser
import sys
import os

from .exceptions import InvalidPasswordError
from .aws_operations import get_aws_config, get_token, get_region
from .operations import (
    load_conf_file,
    setup_conf_file,
    encrypt_creds_file,
    decrypt_creds_file,
    write_creds_file,
    get_platform_config,
)


def main():

    if "setup" in sys.argv[1:]:
        setup()
    elif "refresh" in sys.argv[1:]:
        refresh()
    else:
        print(
            """
Welcome to Sementara ⌛. 
A cli-tool that encrypts your aws credentials file, and replaces it with temporary tokens from sts. 

Usage   : sementara <command> <args>

Commands: setup      first time setup to encrypt credentials file, and generate temporary tokens
          refresh    refresh credentials
        """
        )

    exit(0)


def setup():

    platform_config = get_platform_config()
    sementara_encrypted_file = os.path.join(
        platform_config["aws_directory"], platform_config["encrypted_file_name"]
    )

    if not os.path.isfile(sementara_encrypted_file):
        config = setup_conf_file(platform_config)
        p = getpass.getpass(prompt="Enter encryption password: ")
        p2 = getpass.getpass(prompt="Confirm Password: ")
        if p == p2:
            encrypt_creds_file(password=p, salt=config["salt"])
            print(
                "AWS credentials encrypted, run sementara again to generate new creds"
            )
        else:
            print("Passwords do no match, aborting...")
            exit(1)
    else:
        print("Setup already performed, to change password use sementara re-encrypt")

    return


def refresh():

    platform_config = get_platform_config()
    config = load_conf_file(platform_config)

    # Decrypt credentials file
    try:
        p = getpass.getpass(prompt="🔑 Enter password: ")
        data = decrypt_creds_file(
            platform_config=platform_config, password=p, salt=config["salt"]
        )
        creds = configparser.ConfigParser()
        creds.read_string(data)
    except InvalidPasswordError:
        print(" 🛑 Invalid password, exiting 🛑")
        exit(1)

    # get AWS configuration
    aws_config = get_aws_config(platform_config)
    temp_config = configparser.ConfigParser()

    # Generate temp credentials
    print("Generating temporary tokens...")
    print(f"\n👷🏿 Profile{' ' * 20}⏰ Tokens expire at")
    for section in creds.sections():
        region = get_region(aws_config=aws_config, config=config, section=section)
        temp_token = get_token(
            key_id=creds[section]["aws_access_key_id"],
            secret_access_key=creds[section]["aws_secret_access_key"],
            duration_seconds=config["default_duration_seconds"],
            region=region,
        )
        temp_config[section] = temp_token
        print(f"   {section:<30}{temp_token['aws_token_expiry_time']}")

    # Replace ~/.aws/credentials
    write_creds_file(platform_config=platform_config, config=temp_config)
    print(f"\n\nYou're ready to go 🚀🚀 ")

    return
