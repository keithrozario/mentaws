import json
import getpass
import configparser
import tempfile
import sys
import os

from .aws_operations import get_aws_config, get_token, get_region
from .operations import setup_new_db

def main():

    if sys.argv[1] == "setup":
        setup()
    elif sys.argv[1] == "refresh":
        refresh()
    elif sys.argv[1] == "list":
        list_profiles()
    elif sys.argv[1] == "remove":
        try:
            profile_name = sys.argv[2]
            remove(profile_name)
        except IndexError:
            print(f"Please provide the profile to remove")
            exit(1)
    else:
        print(
            """
Welcome to Sementara ⌛. 
A cli-tool that encrypts your aws credentials file, and replaces it with temporary tokens from sts. 

Usage   : sementara <command> <args>

Commands: setup           first time setup
          refresh         refresh new STS tokens
          reencrypt       change the password used for encryption
          list            list all profiles currently encrypted by sementera
          remove          remove profile from active profiles

WARNING: Sementara does not store your encryption password anywhere. If you forget it, you'll lose access to your credentials.
        """
        )

    exit(0)

    return True


def setup():
    setup_new_db()
    return


def refresh():
    
    creds = get_plaintext_credentials()
    # Generate temporary tokens
    gen_temp_tokens(platform_config=platform_config,
                    creds=creds,
                    config=config)

    return True


def gen_temp_tokens(platform_config: dict, creds: configparser.ConfigParser, config: dict):

    # Generate temp credentials
    temp_config = configparser.ConfigParser()

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
