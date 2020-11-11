import configparser
import sys
import copy
import os
from typing import List

import click

from mentaws.__init__ import __version__
from mentaws.aws_operations import get_token, get_region
from mentaws.operations import (
    setup_new_db,
    list_profiles_in_db,
    get_plaintext_credentials,
    write_creds_file,
    remove_profile_from_db,
    check_new_profiles,
    check_profile_in_db,
    creds_file_contents,
    remove_mentaws_db
)
import mentaws.config as mentaws_config


@click.group()
def main():
    pass


@main.command()
def setup():
    """
    First time setup of mentaws.
    """
    profiles = setup_new_db()

    if profiles is None:
        safe_print(mentaws_config.already_setup_message)
    elif len(profiles) > 0:
        safe_print(f"The following {len(profiles)} profiles were added to mentaws:")
        safe_print(f"\n👷🏿 Profile{' ' * 20}")
        for k, profile in enumerate(profiles):
            safe_print(f"  {k+1:2}.{profile:<30}")
        safe_print(mentaws_config.setup_message)
    elif len(profiles) == 0:
        safe_print("🤔 No profiles were found in the aws credentials file")

    return profiles


@main.command()
@click.option('--profiles', '-p', 
    help='Comma separated list of profiles to refresh (e.g. profile1,profile2)',
    default=""
)
def refresh(profiles: str = ""):
    """
    Refreshes AWS credentials in security file.
    """

    new_profiles = check_new_profiles()
    if len(new_profiles) > 0:
        safe_print(
            f"\nFound {len(new_profiles)} new profiles in credentials file, added these to mentaws:"
        )
        for profile in new_profiles:
            safe_print(f"{profile}")

    # Return credentials only for specified profiles
    creds = get_plaintext_credentials(profiles)

    # Generate temp credentials
    temp_config = configparser.ConfigParser()

    safe_print(f"\nGenerating temporary tokens for {len(creds)} profiles")
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
    safe_print(mentaws_config.refresh_message)

    return


@main.command()
@click.option('--profiles', '-p', 
    help='Comma separated list of profiles to remove (e.g. profile1,profile2)',
    required=True
)
@click.confirmation_option(prompt=f'Deleting a profile is irreversible, are you sure?')
def remove(profiles: str="") -> bool:
    """
    Removes an AWS profile from mentaws [REQUIRES -p option].
    """
    profiles_list = profiles.split(",")

    for profile_name in profiles_list:
        if check_profile_in_db(profile_name):
                remove_profile_from_db(profile_name)
                safe_print(f"Profile {profile_name} was deleted")
        else:
            safe_print(f"Profile {profile_name} not found")

    return True


@main.command()
def status() -> List[dict]:
    """
    List out all Profiles, key IDs and expiry times of tokens
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
    
    safe_print("")

    return profiles


@main.command()
def unsetup() -> bool:
    """
    Restores back the long-lived credentials.
    Deletes the mentaws db -- does not actually delete mentaws (hence we call it unsetup)
    """

    creds = get_plaintext_credentials(all=True)
    temp_config = configparser.ConfigParser()

    for section in creds:
        profile = section["profile"]
        del section["profile"]
        temp_config[profile] = copy.deepcopy(section)

        # remove empty fields
        for key in temp_config[profile]:
            if temp_config[profile][key] == "":
                del temp_config[profile][key]
    
    write_creds_file(config=temp_config, replace=True)
    mentaws_db_path = remove_mentaws_db()

    safe_print(f"{mentaws_db_path} has been been deleted, it's like we were never here")
    safe_print(mentaws_config.unsetup_message)
    
    return True


def safe_print(print_string: str) -> None:
    """
    Windows Command prompt (and older terminals), don't support emojis
    The 'smart' thing to do was to remove emojis...but I implemented this instead.
    Emoji's are the future, and we can't delay the future because some folks run cmd.exe (fight me!)
    """

    try:
        print(print_string)
    except UnicodeEncodeError:
        print(print_string.encode("ascii", "ignore").decode("ascii"))

    return None