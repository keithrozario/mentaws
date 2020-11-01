import json
import getpass
import configparser
import tempfile
import sys
import os

from typing import List

from .aws_operations import get_token, get_region
from .operations import setup_new_db, list_profiles_in_db, get_plaintext_credentials, write_creds_file, remove_profile_from_db, check_new_profiles

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


def list_profiles():
    list_profiles_in_db()
    return
    

def refresh():
    
    new_profiles = check_new_profiles()
    creds = get_plaintext_credentials()
    gen_temp_tokens(creds)

    return 


def remove(profile_name: str):
    remove_profile_from_db(profile_name)
    return


def add_profile():
    add_profile()


def gen_temp_tokens(creds: List[dict]):
    # Generate temp credentials
    temp_config = configparser.ConfigParser()

    print("Generating temporary tokens...")
    print(f"\n👷🏿 Profile{' ' * 20}🌎 Region:{' '*12}⏰ Tokens expire at")
    for section in creds:
        region = get_region(profile=section['profile'])
        temp_token = get_token(
            key_id=section["aws_access_key_id"],
            secret_access_key=section["aws_secret_access_key"],
            region=region,
        )
        temp_config[section['profile']] = temp_token
        print(f"   {section['profile']:<30}{region:<22}{temp_token['aws_token_expiry_time']}")

    # Replace ~/.aws/credentials
    write_creds_file(config=temp_config)
    print(f"\n\nYou're ready to go 🚀🚀 ")
    return
