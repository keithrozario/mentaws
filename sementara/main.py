import json
import getpass
import configparser
import tempfile
import sys
import os

from .aws_operations import get_aws_config, get_token, get_region
from .operations import (
    load_conf_file,
    setup_conf_file,
    encrypt_creds_file,
    write_creds_file,
    get_platform_config,
    load_profiles,
    decrypt_credentials,
    check_new_profiles,
)

# Initialization code
platform_config = get_platform_config()
aws_config = get_aws_config(platform_config)

def main():

    if sys.argv[1] == "setup":
        setup()
    elif sys.argv[1] == "refresh":
        refresh()
    elif sys.argv[1] == "reencrypt":
        reencrypt()
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

    sementara_encrypted_file = os.path.join(
        platform_config["aws_directory"], platform_config["encrypted_file_name"]
    )

    if not os.path.isfile(sementara_encrypted_file):
        p = getpass.getpass(prompt="🔑 Enter encryption password: ")
        p2 = getpass.getpass(prompt="🔑 Confirm Password: ")
        if p == p2:
            config = setup_conf_file(platform_config)
            encrypt_creds_file(
                platform_config=platform_config, password=p, salt=config["salt"]
            )
            print(
                "AWS credentials encrypted, run sementara again to generate new creds"
            )
        else:
            print("Passwords do no match, aborting...")
            exit(1)
        cred_file_path = os.path.join(platform_config["aws_directory"], "credentials")
        creds = configparser.ConfigParser()
        creds.read(filenames=[cred_file_path], encoding='utf-8')
        gen_temp_tokens(platform_config=platform_config,
                        creds=creds,
                        config=config)
        load_profiles(platform_config, creds.sections())

    else:
        print("Setup already performed, to change password use sementara re-encrypt")

    return


def refresh():

    config = load_conf_file(platform_config)
    creds, password = decrypt_credentials(
        platform_config=platform_config,
        config=config,
        return_type="ConfigParserWithPassword",
    )

    # Check if there are new profiles
    new_profiles = check_new_profiles()
    if len(new_profiles.keys()) > 0:
        print(f"Found: {len(new_profiles.keys())} new profiles 👷🏿")
        # replace/add new profile
        creds.read_dict(new_profiles)
        load_profiles(platform_config, creds.sections())

        # encrypt new credentials file
        encrypt_creds_file(
            platform_config=platform_config,
            password=password,
            salt=config["salt"],
            creds=creds.encode("utf-8"),
        )
    
    # Generate temporary tokens
    gen_temp_tokens(platform_config=platform_config,
                    creds=creds,
                    config=config)

    return True


def reencrypt():

    config = load_conf_file(platform_config)

    creds = decrypt_credentials(
        platform_config=platform_config,
        config=config,
        password_prompt="🔑 Enter **current** password: ",
        return_type="str",
    )

    p = getpass.getpass(prompt="🔑 Enter **NEW** password: ")
    p2 = getpass.getpass(prompt="🔑 Confirm **NEW** password: ")

    if p == p2:
        encrypt_creds_file(
            platform_config=platform_config,
            password=p,
            salt=config["salt"],
            creds=creds.encode("utf-8"),
        )
        print("Password changed, this change is irreversible.")
    else:
        print("Passwords do no match, aborting...")
        exit(1)

    return


def list_profiles():

    prof_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["profile_file_name"]
    )
    with open(prof_file_path, "r") as prof_file:
        profiles = json.loads(prof_file.read())

    for k, profile in enumerate(profiles.keys()):
        print(f"{k+1:2}. {profile}")

    print(f"\nFound total of {k+1} profiles 👷🏿\n")

    return {
        "num_profiles": k+1,
        "profiles": profiles.keys()
        }


def remove(profile_name: str):

    config = load_conf_file(platform_config)

    creds, password = decrypt_credentials(
        platform_config=platform_config,
        config=config,
        return_type="ConfigParserWithPassword",
    )

    if creds.remove_section(profile_name):
        with tempfile.TemporaryFile(mode="w+") as data:
            creds.write(data)
            data.seek(0)
            creds_text = data.read()
        encrypt_creds_file(
            platform_config=platform_config,
            password=password,
            salt=config["salt"],
            creds=creds_text.encode("utf-8"),
        )
        print(
            f"Profile {profile_name} "
            f"removed from encrypted credentials file, you will no longer request tokens for this profile"
        )
    else:
        print(f"Profile {profile_name} not found in encrypted credentials file")

    load_profiles(platform_config, creds.sections())

    return list_profiles()


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
