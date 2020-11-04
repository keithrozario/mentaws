import configparser
import sys

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

# default encoding
sys.setdefaultencoding('utf-8')

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
        print(welcome_message)
    exit(0)

    return True


def setup():
    profiles = setup_new_db()
    if len(profiles) > 0:
        print(f"The following {len(profiles)} were added to mentaws:")
        print(f"\n👷🏿 Profile{' ' * 20}")
        for k, profile in enumerate(profiles):
            print(f"{k+1:2}.{profile:<30}")
    return profiles


def list_profiles():
    profiles = list_profiles_in_db()
    print(f"\n👷🏿 Profile{' ' * 20}")
    for k, profile in enumerate(profiles):
        print(f"{k+1:2}.{profile:<30}")
    return profiles


def refresh():

    new_profiles = check_new_profiles()
    if len(new_profiles) > 0:
        print(
            f"Found {len(new_profiles)} new profiles in credentials file, added these to mentaws:"
        )
        for profile in new_profiles:
            print(f"{profile}")

    creds = get_plaintext_credentials()

    # Generate temp credentials
    temp_config = configparser.ConfigParser()

    print("Generating temporary tokens...")
    print(f"\n👷🏿 Profile{' ' * 20}🌎 Region:{' '*12}⏰ Tokens expire at")
    for section in creds:
        region = get_region(profile=section["profile"])
        temp_token = get_token(
            key_id=section["aws_access_key_id"],
            secret_access_key=section["aws_secret_access_key"],
            region=region,
        )
        temp_config[section["profile"]] = temp_token
        print(
            f"   {section['profile']:<30}{region:<22}{temp_token['aws_token_expiry_time']}"
        )

    # Replace ~/.aws/credentials
    write_creds_file(config=temp_config)
    print(f"\n\nYou're ready to go 🚀🚀 ")

    return


def remove(profile_name: str):

    if check_profile_in_db(profile_name):
        if yes_or_no(f"Are you sure you want to delete {profile_name}?"):
            remove_profile_from_db(profile_name)
            print(f"Profile {profile_name} was deleted")
        else:
            pass
    else:
        print(f"Profile {profile_name} not found")

    return list_profiles_in_db()


def yes_or_no(question):
    reply = str(input(question + " (y/n): ")).lower().strip()
    if reply[0] == "y":
        return True
    else:
        return False
