import configparser
import sys
import os

from .config import welcome_message
from .aws_operations import get_token, get_region
from .operations import (
    setup_new_db,
    list_profiles_in_db,
    get_plaintext_credentials,
    write_creds_file,
    remove_profile_from_db,
    check_new_profiles,
    check_profile_in_db,
)


def main():

    # set encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

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
            safe_print(f"Please provide the profile to remove")
            exit(1)
    else:
        safe_print(welcome_message)
    exit(0)

    return True


def setup():

    profiles = setup_new_db()
    if len(profiles) > 0:
        safe_print(f"The following {len(profiles)} profiles were added to mentaws:")
        safe_print(f"\n👷🏿 Profile{' ' * 20}".encode('ascii', 'ignore').decode('ascii'))
        for k, profile in enumerate(profiles):
            safe_print(f"{k+1:2}.{profile:<30}")
    return profiles


def list_profiles():
    profiles = list_profiles_in_db()
    safe_print(f"\n👷🏿 Profile{' ' * 20}")
    for k, profile in enumerate(profiles):
        safe_print(f"{k+1:2}.{profile:<30}")
    return profiles


def refresh():

    new_profiles = check_new_profiles()
    if len(new_profiles) > 0:
        safe_print(
            f"Found {len(new_profiles)} new profiles in credentials file, added these to mentaws:"
        )
        for profile in new_profiles:
            safe_print(f"{profile}")

    creds = get_plaintext_credentials()

    # Generate temp credentials
    temp_config = configparser.ConfigParser()

    safe_print("Generating temporary tokens...")
    safe_print(f"\n👷🏿 Profile{' ' * 20}🌎 Region:{' '*12}⏰ Tokens expire at")
    for section in creds:
        region = get_region(profile=section["profile"])
        temp_token = get_token(
            key_id=section["aws_access_key_id"],
            secret_access_key=section["aws_secret_access_key"],
            region=region,
        )
        temp_config[section["profile"]] = temp_token
        safe_print(
            f"   {section['profile']:<30}{region:<22}{temp_token['aws_token_expiry_time']}"
        )

    # Replace ~/.aws/credentials
    write_creds_file(config=temp_config)
    safe_print(f"\n\nYou're ready to go 🚀🚀 ")

    return


def remove(profile_name: str):

    if check_profile_in_db(profile_name):
        if yes_or_no(f"Are you sure you want to delete {profile_name}?"):
            remove_profile_from_db(profile_name)
            safe_print(f"Profile {profile_name} was deleted")
        else:
            pass
    else:
        safe_print(f"Profile {profile_name} not found")

    return list_profiles_in_db()


def yes_or_no(question):
    reply = str(input(question + " (y/n): ")).lower().strip()
    if reply[0] == "y":
        return True
    else:
        return False


def safe_print(print_string: str)-> None:

    try:
        print(print_string)
    except UnicodeEncodeError:
        print(print_string.encode('ascii', 'ignore').decode('ascii'))

    return None
