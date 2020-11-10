import configparser
import sys
import os
import argparse
from typing import List

from .__init__ import __version__
from .config import welcome_message, help_message
from .aws_operations import get_token, get_region
from .operations import (
    setup_new_db,
    list_profiles_in_db,
    get_plaintext_credentials,
    write_creds_file,
    remove_profile_from_db,
    check_new_profiles,
    check_profile_in_db,
    creds_file_contents,
)


def main():

    parser = argparse.ArgumentParser(description=welcome_message, add_help=False)
    parser.add_argument(
        "command",
        choices=["setup", "refresh", "status", "list", "remove", "help"],
        type=str,
        help="Name of command, must be setup, refresh, list or remove",
    )
    parser.add_argument(
        "-p",
        "--profiles",
        type=str,
        default="",
        help="Comma-separate list of profiles to be actioned on",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Display the version of this tool",
    )

    if len(sys.argv) == 1:
        safe_print(help_message)
        return 0

    args = parser.parse_args()
    command = args.command
    profiles = args.profiles

    if args.command == "help":
        safe_print(help_message)
        command = 0

    elif args.command == "setup":
        setup()
        command = 1

    elif args.command == "refresh":
        refresh()
        command = 2

    elif args.command == "list":
        list_profiles()
        command = 3

    elif args.command == "status":
        status()
        command = 4

    elif args.command == "remove":
        if not profiles == "":
            remove(profiles)
            comamand = 5
        else:
            safe_print("You must provide a profile(s) using the -p argument")
            command = -1

    return command


def setup():

    profiles = setup_new_db()

    if profiles is None:
        safe_print(
            "It looks like mentaws is already setup, use mentaws refresh or mentaws list"
        )
    elif len(profiles) > 0:
        safe_print(f"The following {len(profiles)} profiles were added to mentaws:")
        safe_print(f"\n👷🏿 Profile{' ' * 20}")
        for k, profile in enumerate(profiles):
            safe_print(f"  {k+1:2}.{profile:<30}")
    elif len(profiles) == 0:
        safe_print("🤔 No profiles were found in the aws credentials file")

    return profiles


def list_profiles():
    profiles = list_profiles_in_db()
    safe_print(f"\n👷🏿 Profile{' ' * 20}")
    for k, profile in enumerate(profiles):
        safe_print(f"{k+1:2}. {profile:<30}")
    return profiles


def refresh(profiles: str = ""):
    """
    Args:
      profiles: comma delimited string of profiles to refresh for
    """

    new_profiles = check_new_profiles()
    if len(new_profiles) > 0:
        safe_print(
            f"Found {len(new_profiles)} new profiles in credentials file, added these to mentaws:"
        )
        for profile in new_profiles:
            safe_print(f"{profile}")

    # Return credentials only for specified profiles
    creds = get_plaintext_credentials(profiles)

    # Generate temp credentials
    temp_config = configparser.ConfigParser()

    safe_print(f"Generating temporary tokens for {len(creds)} profiles")
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
            f"   {section['profile']:<30}{region:<22}{temp_token['aws_token_expiry_time_human']}"
        )

    # Replace ~/.aws/credentials
    write_creds_file(config=temp_config, replace=False)
    safe_print(f"\n\nYou're ready to go 🚀🚀 ")

    return


def remove(profiles: str) -> bool:

    profiles_list = profiles.split(",")

    for profile_name in profiles_list:
        if check_profile_in_db(profile_name):
            if yes_or_no(f"Are you sure you want to delete {profile_name}?"):
                remove_profile_from_db(profile_name)
                safe_print(f"Profile {profile_name} was deleted")
                deleted = True
            else:
                deleted = False
        else:
            safe_print(f"Profile {profile_name} not found")
            deleted = False

    return deleted


def status() -> List[dict]:
    """
    List out all Profiles, eys and expiry times
    """

    creds = creds_file_contents()
    profiles = list()

    safe_print(f"\n👷🏿 Profile{' ' * 20}🔑 Key:{' '*18}⏰ Tokens expire at")

    for section in creds.sections():
        if not section == "DEFAULT":
            try:
                safe_print(
                    f"   {section:<30}{creds[section]['aws_access_key_id']:<25}{creds[section]['aws_token_expiry_time_human']}"
                )
                temp = {
                    "profile": section,
                    "aws_access_key_id": creds[section]["aws_access_key_id"],
                    "token_expiry": creds[section]["aws_token_expiry_time_human"],
                }
            except KeyError:
                # Sections without expiry time
                safe_print(f"   {section:<30}-{' '*24}No Token Expiry")
                temp = {"profile": section}
            profiles.append(temp)

    return profiles


def yes_or_no(question):
    reply = str(input(question + " (y/n): ")).lower().strip()
    if reply[0] == "y":
        return True
    else:
        return False


def safe_print(print_string: str) -> None:
    """
    Windows Command prompt (and older terminals), don't support emojis
    The 'smart' thing to do was to remove emojis...but I implemented this instead.
    Emoji's are the future, and we shouldn't delay the future because some folks run cmd.exe (fight me!)
    """

    try:
        print(print_string)
    except UnicodeEncodeError:
        print(print_string.encode("ascii", "ignore").decode("ascii"))

    return None
